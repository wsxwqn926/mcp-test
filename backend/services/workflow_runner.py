from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime
from typing import Any

from backend.models.test_result import AssertionResult
from backend.models.workflow import NodeType, Workflow, WorkflowNode
from backend.models.workflow_result import NodeResult, WorkflowRunResult
from backend.utils.logger import get_logger

from .test_runner import AssertionEngine

logger = get_logger("workflow_runner")


class WorkflowRunner:
    def __init__(self, app_state):
        self.app_state = app_state
        self.variables: dict[str, Any] = {}
        self.node_results: dict[str, NodeResult] = {}
        self._stop_requested = False
        self._last_node_id: str | None = None

    def request_stop(self):
        self._stop_requested = True

    async def run(self, workflow: Workflow, initial_vars: dict | None = None) -> WorkflowRunResult:
        self.variables = dict(workflow.variables)
        if initial_vars:
            self.variables.update(initial_vars)
        self._stop_requested = False
        self.node_results.clear()

        start_nodes = [n for n in workflow.nodes if n.type == NodeType.START]
        if not start_nodes:
            raise ValueError("流程缺少 Start 节点")

        start_node = start_nodes[0]
        for m in start_node.data.get("_input_mappings", []):
            var_name = m.get("variable_name", "")
            if var_name and var_name not in self.variables:
                self.variables[var_name] = m.get("value", "")

        start_dt = datetime.now()
        start_mono = time.monotonic()

        self._broadcast_node(start_nodes[0].id, "running")
        current = start_nodes[0]
        overall_status = "passed"

        while current and not self._stop_requested:
            result = await self._execute_node(current, workflow)
            self.node_results[current.id] = result
            self._broadcast_node(current.id, result.status)

            if result.status in ("error", "failed"):
                overall_status = "error" if result.status == "error" else "failed"
                break

            current = await self._find_next(current, workflow)

        if self._stop_requested:
            overall_status = "stopped"

        for node in workflow.nodes:
            if node.id not in self.node_results:
                self.node_results[node.id] = NodeResult(
                    node_id=node.id, node_type=node.type.value, status="skipped"
                )

        run_result = WorkflowRunResult(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status=overall_status,
            started_at=start_dt,
            finished_at=datetime.now(),
            duration_ms=(time.monotonic() - start_mono) * 1000,
            node_results=self.node_results,
            variables_snapshot=dict(self.variables),
        )

        self.app_state.emit("workflow_run_complete", {
            "workflow_id": workflow.id,
            "run_id": run_result.id,
            "status": overall_status,
            "duration_ms": run_result.duration_ms,
        })
        return run_result

    async def _find_next(self, current: WorkflowNode, workflow: Workflow) -> WorkflowNode | None:
        if current.type == NodeType.CONDITION:
            met = self._evaluate_condition(current.data.get("expression", {}))
            handle = "true" if met else "false"
            edge = self._find_edge(workflow, current.id, handle)
        elif current.type == NodeType.LOOP:
            edge = await self._handle_loop(current, workflow)
        elif current.type == NodeType.END:
            return None
        else:
            edge = self._find_edge(workflow, current.id)

        if not edge:
            return None

        target_node = self._get_node(workflow, edge.target)
        if target_node:
            self._broadcast_node(target_node.id, "running")
        return target_node

    async def _handle_loop(self, loop_node: WorkflowNode, workflow: Workflow):
        loop_data = loop_node.data
        max_iter = min(loop_data.get("max_iterations", 100), 1000)
        body_edges = [e for e in workflow.edges if e.source == loop_node.id and e.source_handle == "body"]
        done_edges = [e for e in workflow.edges if e.source == loop_node.id and e.source_handle == "done"]

        if not body_edges or not done_edges:
            return done_edges[0] if done_edges else None

        loop_type = loop_data.get("loop_type", "count")
        if loop_type == "count":
            count = min(loop_data.get("count", 0), max_iter)
            for i in range(count):
                if self._stop_requested:
                    break
                self.variables["loop_index"] = i
                self.variables["loop_count"] = count
                await self._execute_subgraph(body_edges[0].target, loop_node.id, workflow)
        elif loop_type == "condition":
            for i in range(max_iter):
                if self._stop_requested:
                    break
                if not self._evaluate_condition(loop_data.get("condition", {})):
                    break
                self.variables["loop_index"] = i
                self.variables["loop_count"] = i + 1
                await self._execute_subgraph(body_edges[0].target, loop_node.id, workflow)

        return done_edges[0] if done_edges else None

    async def _execute_subgraph(self, entry_id: str, exit_id: str, workflow: Workflow):
        current = self._get_node(workflow, entry_id)
        visited: set[str] = set()
        while current and current.id != exit_id and current.id not in visited:
            visited.add(current.id)
            result = await self._execute_node(current, workflow)
            self.node_results[current.id] = result
            self._broadcast_node(current.id, result.status)
            if result.status in ("error", "failed"):
                break
            edge = self._find_edge(workflow, current.id)
            current = self._get_node(workflow, edge.target) if edge else None

    async def _execute_node(self, node: WorkflowNode, workflow: Workflow) -> NodeResult:
        result = NodeResult(node_id=node.id, node_type=node.type.value, node_label=node.label)
        result.started_at = datetime.now()
        start = time.monotonic()

        try:
            self._apply_input_mappings(node)

            if node.type == NodeType.START or node.type == NodeType.END:
                result.status = "passed"

            elif node.type == NodeType.TOOL_CALL:
                config_id = node.data.get("config_id")
                wrapper = self._get_wrapper(config_id)
                if not wrapper:
                    raise ValueError(f"MCP 连接未找到: {config_id or 'primary'}")
                tool_name = node.data["tool_name"]
                arguments = self._resolve_variables(node.data.get("arguments", {}))
                arguments = self._ensure_dict(arguments)
                result.request = {"name": tool_name, "arguments": arguments}
                call_result = await wrapper.call_tool(tool_name, arguments)
                result.response = call_result.model_dump(mode="json")
                result.status = "failed" if call_result.isError else "passed"
                self.variables["last_result"] = result.response
                self.variables["last_is_error"] = call_result.isError
                self._apply_output_mappings(node, result.response)

            elif node.type == NodeType.RESOURCE_READ:
                config_id = node.data.get("config_id")
                wrapper = self._get_wrapper(config_id)
                if not wrapper:
                    raise ValueError(f"MCP 连接未找到: {config_id or 'primary'}")
                uri = self._resolve_variables(node.data.get("uri", ""))
                result.request = {"uri": uri}
                read_result = await wrapper.read_resource(uri)
                result.response = read_result.model_dump(mode="json")
                result.status = "passed"
                self.variables["last_result"] = result.response
                self._apply_output_mappings(node, result.response)

            elif node.type == NodeType.PROMPT_GET:
                config_id = node.data.get("config_id")
                wrapper = self._get_wrapper(config_id)
                if not wrapper:
                    raise ValueError(f"MCP 连接未找到: {config_id or 'primary'}")
                name = node.data.get("name", "")
                arguments = self._resolve_variables(node.data.get("arguments", {}))
                arguments = self._ensure_dict(arguments)
                result.request = {"name": name, "arguments": arguments}
                prompt_result = await wrapper.get_prompt(name, arguments or None)
                result.response = prompt_result.model_dump(mode="json")
                result.status = "passed"
                self.variables["last_result"] = result.response
                self._apply_output_mappings(node, result.response)

            elif node.type == NodeType.ASSERTION:
                assertion_data = node.data.get("assertion")
                if assertion_data:
                    from backend.models.test_case import Assertion
                    assertion = Assertion(**assertion_data)
                    last_response = self.variables.get("last_result")
                    last_dur = 0.0
                    if self._last_node_id and self._last_node_id in self.node_results:
                        last_dur = self.node_results[self._last_node_id].duration_ms
                    ar = AssertionEngine.evaluate(
                        assertion, last_response, last_dur,
                        self.variables.get("last_is_error", False)
                    )
                    result.assertion_results.append(ar)
                    result.status = "passed" if ar.passed else "failed"
                else:
                    result.status = "error"
                    result.error_message = "断言节点缺少断言配置"

            elif node.type == NodeType.WAIT:
                seconds = float(node.data.get("seconds", 1.0))
                await asyncio.sleep(seconds)
                result.status = "passed"

            elif node.type == NodeType.VARIABLE:
                self._handle_variable(node.data)
                result.status = "passed"

            elif node.type == NodeType.CONDITION:
                met = self._evaluate_condition(node.data.get("expression", {}))
                result.status = "passed"
                result.response = {"condition_met": met}

            elif node.type == NodeType.LOOP:
                result.status = "passed"

        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            logger.error(f"Node {node.id} error: {e}", exc_info=True)

        result.duration_ms = (time.monotonic() - start) * 1000
        result.finished_at = datetime.now()
        self._last_node_id = node.id
        return result

    def _handle_variable(self, data: dict):
        action = data.get("action", "set")
        var_name = data.get("variable_name", "")
        if not var_name:
            return
        if action == "set":
            source = data.get("value_source", "last_result")
            if source == "last_result":
                val = self.variables.get("last_result")
                path = data.get("value_path", "")
                if path and val:
                    val = self._extract_path(val, path)
            elif source == "variable":
                val = self.variables.get(data.get("literal_value", ""), data.get("literal_value"))
            else:
                val = data.get("literal_value")
            self.variables[var_name] = val

    def _apply_input_mappings(self, node: WorkflowNode):
        mappings = node.data.get("_input_mappings", [])
        if not mappings:
            return
        raw_args = node.data.get("arguments", {})
        if isinstance(raw_args, str):
            try:
                arguments = json.loads(raw_args)
                if not isinstance(arguments, dict):
                    arguments = {}
            except (json.JSONDecodeError, TypeError):
                arguments = {}
        elif isinstance(raw_args, dict):
            arguments = dict(raw_args)
        else:
            arguments = {}
        for m in mappings:
            src_var = m.get("source_var", "")
            tgt_param = m.get("target_param", "")
            if not src_var or not tgt_param:
                continue
            val = self.variables.get(src_var)
            if val is not None:
                arguments[tgt_param] = val
        node.data["arguments"] = arguments

    def _apply_output_mappings(self, node: WorkflowNode, response: Any):
        mappings = node.data.get("_output_mappings", [])
        if not mappings:
            return
        for m in mappings:
            src_path = m.get("source_path", "response")
            tgt_var = m.get("target_var", "")
            if not tgt_var:
                continue
            if src_path == "response" or not src_path:
                self.variables[tgt_var] = response
                continue
            path = src_path
            if path.startswith("response."):
                path = path[len("response."):]
            elif path.startswith("response["):
                path = path[len("response"):]
            val = self._extract_path(response, path) if path else response
            if val is not None:
                self.variables[tgt_var] = val

    def _ensure_dict(self, value: Any) -> dict:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    def _extract_path(self, data: Any, path: str) -> Any:
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]
        current = data
        for part in parts:
            if current is None:
                return None
            if isinstance(current, str):
                try:
                    current = json.loads(current)
                except (json.JSONDecodeError, TypeError):
                    return None
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    def _evaluate_condition(self, expression: dict) -> bool:
        if not expression:
            return False
        var_name = expression.get("variable", "")
        operator = expression.get("operator", "eq")
        expected = expression.get("value")

        if var_name == "last_result":
            actual = self.variables.get("last_result")
        else:
            actual = self.variables.get(var_name)

        if operator in ("is_empty",):
            return actual is None or actual == "" or actual == []
        if operator in ("is_not_empty",):
            return actual is not None and actual != "" and actual != []
        if actual is None:
            return False

        if operator == "eq":
            return actual == expected
        if operator == "ne":
            return actual != expected
        try:
            if operator == "gt":
                return float(actual) > float(expected)
            if operator == "lt":
                return float(actual) < float(expected)
            if operator == "gte":
                return float(actual) >= float(expected)
            if operator == "lte":
                return float(actual) <= float(expected)
        except (ValueError, TypeError):
            return False
        if operator == "contains":
            return str(expected) in str(actual)
        if operator == "not_contains":
            return str(expected) not in str(actual)
        return False

    def _resolve_variables(self, value: Any) -> Any:
        if isinstance(value, str):
            pattern = r'\$\{([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_\[\]]+)*)\}'

            def replacer(match):
                ref = match.group(1)
                parts = re.split(r'\.|\[|\]', ref)
                parts = [p for p in parts if p]
                val = self.variables.get(parts[0])
                for part in parts[1:]:
                    if val is None:
                        return match.group(0)
                    if part.isdigit():
                        idx = int(part)
                        val = val[idx] if isinstance(val, list) and idx < len(val) else None
                    elif isinstance(val, dict):
                        val = val.get(part)
                    else:
                        return match.group(0)
                return str(val) if val is not None else match.group(0)

            return re.sub(pattern, replacer, value)
        elif isinstance(value, dict):
            return {k: self._resolve_variables(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_variables(item) for item in value]
        return value

    def _get_wrapper(self, config_id: str | None):
        if config_id:
            mgr = self.app_state.get_connection(config_id)
            return mgr.session_wrapper if mgr else None
        wrapper = self.app_state.get_session_wrapper()
        return wrapper

    def _find_edge(self, workflow: Workflow, source_id: str, handle: str | None = None) -> Any | None:
        for edge in workflow.edges:
            if edge.source == source_id:
                if handle is None and edge.source_handle is None:
                    return edge
                if handle and edge.source_handle == handle:
                    return edge
        if handle:
            for edge in workflow.edges:
                if edge.source == source_id and edge.source_handle is None:
                    return edge
        return None

    def _get_node(self, workflow: Workflow, node_id: str) -> WorkflowNode | None:
        for node in workflow.nodes:
            if node.id == node_id:
                return node
        return None

    def _broadcast_node(self, node_id: str, status: str):
        self.app_state.emit("workflow_node_status", {
            "node_id": node_id,
            "status": status,
        })
