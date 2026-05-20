from fastapi import APIRouter, HTTPException

from ..services.performance_tester import PerformanceTester
from .state import app_state

router = APIRouter()


@router.post("/latency")
async def run_latency_test(body: dict):
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")

    tester = PerformanceTester(wrapper)
    report = await tester.run_latency_test(
        tool_name=body.get("tool_name", ""),
        arguments=body.get("arguments"),
        iterations=body.get("iterations", 50),
        warmup=body.get("warmup", 3),
    )
    return _report_to_dict(report)


@router.post("/concurrency")
async def run_concurrency_test(body: dict):
    wrapper = app_state.get_session_wrapper()
    if not wrapper:
        raise HTTPException(400, "Not connected to MCP server")

    tester = PerformanceTester(wrapper)
    report = await tester.run_concurrency_test(
        tool_name=body.get("tool_name", ""),
        arguments=body.get("arguments"),
        concurrency=body.get("concurrency", 5),
        requests_per_worker=body.get("requests_per_worker", 10),
    )
    return _report_to_dict(report)


def _report_to_dict(report) -> dict:
    return {
        "test_type": report.test_type,
        "tool_name": report.tool_name,
        "arguments": report.arguments,
        "started_at": report.started_at.isoformat(),
        "finished_at": report.finished_at.isoformat(),
        "total_requests": report.total_requests,
        "successful_requests": report.successful_requests,
        "failed_requests": report.failed_requests,
        "qps": report.qps,
        "latency_stats": {
            "min_ms": report.latency_stats.min_ms,
            "max_ms": report.latency_stats.max_ms,
            "avg_ms": report.latency_stats.avg_ms,
            "p50_ms": report.latency_stats.p50_ms,
            "p95_ms": report.latency_stats.p95_ms,
            "p99_ms": report.latency_stats.p99_ms,
            "std_dev_ms": report.latency_stats.std_dev_ms,
        },
        "raw_latencies": report.raw_latencies,
        "errors": report.errors,
    }
