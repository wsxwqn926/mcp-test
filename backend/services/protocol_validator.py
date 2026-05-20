from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.client.session_wrapper import SessionWrapper
from backend.utils.logger import get_logger

logger = get_logger("protocol_validator")


class ValidationCheckResult(BaseModel):
    check_id: str
    category: str
    description: str
    status: Literal["passed", "failed", "warning", "skipped"]
    details: str | None = None
    request: dict[str, Any] | None = None
    response: dict[str, Any] | None = None


class ValidationReport(BaseModel):
    server_name: str = ""
    server_version: str = ""
    protocol_version: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    results: list[ValidationCheckResult] = Field(default_factory=list)
    overall_status: Literal["compliant", "partial", "non_compliant"] = "compliant"


class ProtocolValidator:
    def __init__(self, session_wrapper: SessionWrapper):
        self._wrapper = session_wrapper

    async def run_validation(self) -> ValidationReport:
        report = ValidationReport()

        init_result = self._wrapper.initialize_result
        if init_result:
            info = init_result.serverInfo
            report.server_name = info.name if hasattr(info, "name") else ""
            report.server_version = info.version if hasattr(info, "version") else ""
            report.protocol_version = init_result.protocolVersion if hasattr(init_result, "protocolVersion") else ""

        await self._check_initialization(report)
        await self._check_tools(report)
        await self._check_resources(report)
        await self._check_prompts(report)
        await self._check_ping(report)
        await self._check_error_handling(report)

        report.total_checks = len(report.results)
        report.passed = sum(1 for r in report.results if r.status == "passed")
        report.failed = sum(1 for r in report.results if r.status == "failed")
        report.warnings = sum(1 for r in report.results if r.status == "warning")

        if report.failed == 0:
            report.overall_status = "compliant"
        elif report.failed <= 3:
            report.overall_status = "partial"
        else:
            report.overall_status = "non_compliant"

        return report

    async def _check_initialization(self, report: ValidationReport) -> None:
        init_result = self._wrapper.initialize_result

        report.results.append(ValidationCheckResult(
            check_id="init_completed",
            category="初始化",
            description="初始化握手完成",
            status="passed" if init_result else "failed",
            details="InitializeResult 已获取" if init_result else "未获取初始化结果",
        ))

        if not init_result:
            return

        report.results.append(ValidationCheckResult(
            check_id="protocol_version",
            category="初始化",
            description="协议版本已返回",
            status="passed" if report.protocol_version else "failed",
            details=f"版本: {report.protocol_version}" if report.protocol_version else "缺少 protocolVersion",
        ))

        info = init_result.serverInfo
        report.results.append(ValidationCheckResult(
            check_id="server_info",
            category="初始化",
            description="Server 信息完整 (name + version)",
            status="passed" if report.server_name and report.server_version else "warning",
            details=f"name={report.server_name}, version={report.server_version}",
        ))

        caps = init_result.capabilities
        report.results.append(ValidationCheckResult(
            check_id="capabilities",
            category="初始化",
            description="服务端能力声明完整",
            status="passed" if caps else "warning",
            details=f"capabilities 已获取: {bool(caps)}",
        ))

    async def _check_tools(self, report: ValidationReport) -> None:
        try:
            tools = await self._wrapper.list_tools(force_refresh=True)

            report.results.append(ValidationCheckResult(
                check_id="tools_list",
                category="工具",
                description="tools/list 返回成功",
                status="passed",
                details=f"返回 {len(tools)} 个工具",
            ))

            for i, tool in enumerate(tools[:10]):
                name_ok = bool(tool.name and len(tool.name) > 0)
                report.results.append(ValidationCheckResult(
                    check_id=f"tool_name_{i}",
                    category="工具",
                    description=f"工具名称非空: {tool.name}",
                    status="passed" if name_ok else "failed",
                ))

                schema_ok = bool(tool.inputSchema and isinstance(tool.inputSchema, dict))
                report.results.append(ValidationCheckResult(
                    check_id=f"tool_schema_{i}",
                    category="工具",
                    description=f"工具 inputSchema 已返回: {tool.name}",
                    status="passed" if schema_ok else "warning",
                    details="有 inputSchema" if schema_ok else "缺少 inputSchema",
                ))

                if i == 0 and tool.inputSchema:
                    try:
                        result = await self._wrapper.call_tool(tool.name, {})
                        report.results.append(ValidationCheckResult(
                            check_id="tool_response_format",
                            category="工具",
                            description=f"工具调用响应包含 content 列表",
                            status="passed" if hasattr(result, "content") and isinstance(result.content, list) else "failed",
                        ))
                    except Exception as e:
                        report.results.append(ValidationCheckResult(
                            check_id="tool_response_format",
                            category="工具",
                            description="工具调用响应格式",
                            status="warning",
                            details=f"调用失败 (可能是参数不匹配): {e}",
                        ))

        except Exception as e:
            report.results.append(ValidationCheckResult(
                check_id="tools_list",
                category="工具",
                description="tools/list 返回成功",
                status="failed",
                details=str(e),
            ))

    async def _check_resources(self, report: ValidationReport) -> None:
        try:
            resources = await self._wrapper.list_resources(force_refresh=True)
            report.results.append(ValidationCheckResult(
                check_id="resources_list",
                category="资源",
                description="resources/list 返回成功",
                status="passed",
                details=f"返回 {len(resources)} 个资源",
            ))

            for i, res in enumerate(resources[:5]):
                uri = getattr(res, "uri", "")
                report.results.append(ValidationCheckResult(
                    check_id=f"resource_uri_{i}",
                    category="资源",
                    description=f"资源 URI 已返回: {uri}",
                    status="passed" if uri else "failed",
                ))
        except Exception as e:
            report.results.append(ValidationCheckResult(
                check_id="resources_list",
                category="资源",
                description="resources/list 返回成功",
                status="warning",
                details=str(e),
            ))

    async def _check_prompts(self, report: ValidationReport) -> None:
        try:
            prompts = await self._wrapper.list_prompts(force_refresh=True)
            report.results.append(ValidationCheckResult(
                check_id="prompts_list",
                category="提示词",
                description="prompts/list 返回成功",
                status="passed",
                details=f"返回 {len(prompts)} 个提示词",
            ))

            for i, p in enumerate(prompts[:5]):
                report.results.append(ValidationCheckResult(
                    check_id=f"prompt_name_{i}",
                    category="提示词",
                    description=f"提示词名称非空: {p.name}",
                    status="passed" if p.name else "failed",
                ))
        except Exception as e:
            report.results.append(ValidationCheckResult(
                check_id="prompts_list",
                category="提示词",
                description="prompts/list 返回成功",
                status="warning",
                details=str(e),
            ))

    async def _check_ping(self, report: ValidationReport) -> None:
        try:
            await self._wrapper.send_ping()
            report.results.append(ValidationCheckResult(
                check_id="ping",
                category="连接",
                description="ping/pong 心跳正常",
                status="passed",
            ))
        except Exception as e:
            report.results.append(ValidationCheckResult(
                check_id="ping",
                category="连接",
                description="ping/pong 心跳正常",
                status="failed",
                details=str(e),
            ))

    async def _check_error_handling(self, report: ValidationReport) -> None:
        try:
            result = await self._wrapper.call_tool("__nonexistent_tool_12345__", {})
            is_error = result.isError if hasattr(result, "isError") else False
            report.results.append(ValidationCheckResult(
                check_id="unknown_tool_error",
                category="错误处理",
                description="调用不存在的工具返回错误",
                status="passed" if is_error else "failed",
                details="正确返回 isError=True" if is_error else "未返回错误标识",
            ))
        except Exception as e:
            report.results.append(ValidationCheckResult(
                check_id="unknown_tool_error",
                category="错误处理",
                description="调用不存在的工具返回错误",
                status="passed",
                details=f"抛出异常: {e}",
            ))
