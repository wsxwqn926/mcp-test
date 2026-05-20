from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime
from typing import Any

from backend.client.session_wrapper import SessionWrapper
from backend.models.test_case import Assertion, AssertionType, StepType, TestCase, TestStep
from backend.models.test_result import AssertionResult, StepResult, TestRunResult
from backend.utils.logger import get_logger

logger = get_logger("test_runner")


class AssertionEngine:
    @staticmethod
    def evaluate(
        assertion: Assertion,
        response_data: dict[str, Any] | None,
        duration_ms: float,
        is_error: bool = False,
    ) -> AssertionResult:
        atype = assertion.type
        negate = assertion.negate

        try:
            if atype == AssertionType.STATUS_SUCCESS:
                passed = not is_error
                if negate:
                    passed = not passed
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=passed,
                    expected="success" if not negate else "error",
                    actual="error" if is_error else "success",
                    message="状态检查通过" if passed else "状态检查未通过",
                )

            if response_data is None:
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=False,
                    message="响应数据为空",
                )

            text_content = _extract_text_content(response_data)

            if atype == AssertionType.CONTENT_CONTAINS:
                expected = str(assertion.expected)
                actual_contains = expected in text_content
                passed = actual_contains if not negate else not actual_contains
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=passed,
                    expected=expected,
                    actual=text_content[:200],
                    message=f"内容{'包含' if passed else '不包含'} '{expected}'",
                )

            if atype == AssertionType.CONTENT_MATCHES:
                pattern = str(assertion.expected)
                matches = bool(re.search(pattern, text_content))
                passed = matches if not negate else not matches
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=passed,
                    expected=pattern,
                    actual=text_content[:200],
                    message=f"正则{'匹配' if passed else '不匹配'}",
                )

            if atype == AssertionType.CONTENT_NOT_EMPTY:
                passed = bool(text_content.strip())
                if negate:
                    passed = not passed
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=passed,
                    expected="非空" if not negate else "为空",
                    actual=f"长度 {len(text_content)}",
                    message="内容非空检查" + ("通过" if passed else "未通过"),
                )

            if atype == AssertionType.RESPONSE_TIME_LT:
                threshold = float(assertion.expected)
                passed = duration_ms < threshold
                if negate:
                    passed = not passed
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=passed,
                    expected=f"<{threshold}ms",
                    actual=f"{duration_ms:.1f}ms",
                    message=f"响应时间 {duration_ms:.1f}ms {'<' if passed else '>='} {threshold}ms",
                )

            if atype == AssertionType.JSON_FIELD_EQUALS:
                path = assertion.path or ""
                actual_val = _get_json_path(response_data, path)
                expected_val = assertion.expected
                passed = actual_val == expected_val
                if negate:
                    passed = not passed
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=passed,
                    expected=expected_val,
                    actual=actual_val,
                    message=f"JSON字段'{path}' {'匹配' if passed else '不匹配'}",
                )

            if atype == AssertionType.CONTENT_SCHEMA_VALID:
                try:
                    import jsonschema

                    schema = assertion.expected
                    jsonschema.validate(json.loads(text_content) if isinstance(text_content, str) else response_data, schema)
                    passed = True
                except Exception as e:
                    passed = False
                if negate:
                    passed = not passed
                return AssertionResult(
                    assertion_type=atype.value,
                    passed=passed,
                    message=f"Schema 检验{'通过' if passed else '未通过'}",
                )

            return AssertionResult(
                assertion_type=atype.value,
                passed=False,
                message=f"不支持的断言类型: {atype}",
            )

        except Exception as e:
            return AssertionResult(
                assertion_type=atype.value,
                passed=False,
                message=f"断言执行异常: {e}",
            )


class TestRunner:
    def __init__(self, session_wrapper: SessionWrapper):
        self._wrapper = session_wrapper
        self._assertion_engine = AssertionEngine()

    async def run_test(self, test_case: TestCase) -> TestRunResult:
        result = TestRunResult(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            total_steps=len(test_case.steps),
        )

        start_mono = time.monotonic()
        start_dt = datetime.now()

        last_response_data: dict[str, Any] | None = None
        last_duration_ms: float = 0.0
        last_is_error: bool = False

        for step in test_case.steps:
            step_result = await self._execute_step(
                step, last_response_data, last_duration_ms, last_is_error
            )
            result.step_results.append(step_result)

            if step_result.status == "passed":
                result.passed_steps += 1
            elif step_result.status == "failed":
                result.failed_steps += 1
            elif step_result.status == "error":
                result.failed_steps += 1
                result.status = "error"
                result.error_message = step_result.error_message
                break

            if step.type == StepType.TOOL_CALL and step_result.response:
                last_response_data = step_result.response
                last_duration_ms = step_result.duration_ms
                last_is_error = step_result.status == "failed"

        result.started_at = start_dt
        result.finished_at = datetime.now()
        result.duration_ms = (time.monotonic() - start_mono) * 1000

        if result.status != "error":
            result.status = "passed" if result.failed_steps == 0 else "failed"

        return result

    async def _execute_step(
        self,
        step: TestStep,
        last_response: dict[str, Any] | None,
        last_duration_ms: float,
        last_is_error: bool,
    ) -> StepResult:
        step_result = StepResult(
            step_id=step.id,
            step_name=step.name,
            step_type=step.type.value,
        )

        try:
            start = time.monotonic()

            if step.type == StepType.TOOL_CALL:
                if not step.tool_name:
                    raise ValueError("tool_call 步骤缺少 tool_name")
                step_result.request = {"name": step.tool_name, "arguments": step.arguments}
                call_result = await self._wrapper.call_tool(step.tool_name, step.arguments)
                step_result.duration_ms = (time.monotonic() - start) * 1000
                step_result.response = call_result.model_dump(mode="json")
                step_result.status = "failed" if call_result.isError else "passed"

            elif step.type == StepType.RESOURCE_READ:
                if not step.resource_uri:
                    raise ValueError("resource_read 步骤缺少 resource_uri")
                step_result.request = {"uri": step.resource_uri}
                read_result = await self._wrapper.read_resource(step.resource_uri)
                step_result.duration_ms = (time.monotonic() - start) * 1000
                step_result.response = read_result.model_dump(mode="json")
                step_result.status = "passed"

            elif step.type == StepType.PROMPT_GET:
                if not step.prompt_name:
                    raise ValueError("prompt_get 步骤缺少 prompt_name")
                step_result.request = {"name": step.prompt_name, "arguments": step.prompt_arguments}
                prompt_result = await self._wrapper.get_prompt(step.prompt_name, step.prompt_arguments)
                step_result.duration_ms = (time.monotonic() - start) * 1000
                step_result.response = prompt_result.model_dump(mode="json")
                step_result.status = "passed"

            elif step.type == StepType.ASSERTION:
                step_result.duration_ms = 0.0
                if step.assertion:
                    ref_response = last_response
                    ref_duration = last_duration_ms
                    ref_error = last_is_error
                    ar = self._assertion_engine.evaluate(
                        step.assertion, ref_response, ref_duration, ref_error
                    )
                    step_result.assertion_results.append(ar)
                    step_result.status = "passed" if ar.passed else "failed"
                else:
                    step_result.status = "error"
                    step_result.error_message = "assertion 步骤缺少断言引擎"

            elif step.type == StepType.WAIT:
                wait = step.wait_seconds or 1.0
                await asyncio.sleep(wait)
                step_result.duration_ms = wait * 1000
                step_result.status = "passed"

            else:
                step_result.status = "error"
                step_result.error_message = f"不支持的步骤类型: {step.type}"

        except Exception as e:
            step_result.status = "error"
            step_result.error_message = str(e)

        return step_result


def _extract_text_content(data: dict[str, Any]) -> str:
    if not data:
        return ""
    contents = data.get("content", [])
    parts = []
    for c in contents:
        if isinstance(c, dict) and "text" in c:
            parts.append(c["text"])
        elif isinstance(c, dict) and "data" in c:
            parts.append(str(c["data"]))
    return " ".join(parts) if parts else json.dumps(data, ensure_ascii=False, default=str)


def _get_json_path(data: dict[str, Any], path: str) -> Any:
    if not path:
        return data
    keys = path.strip("/").split("/")
    current: Any = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            try:
                current = current[int(key)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current
