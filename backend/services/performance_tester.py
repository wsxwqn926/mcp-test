from __future__ import annotations

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from backend.client.session_wrapper import SessionWrapper
from backend.utils.logger import get_logger

logger = get_logger("performance_tester")


@dataclass
class LatencyStats:
    min_ms: float = 0.0
    max_ms: float = 0.0
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    std_dev_ms: float = 0.0


@dataclass
class PerformanceReport:
    test_type: str = "latency"
    tool_name: str = ""
    arguments: dict[str, Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latency_stats: LatencyStats = field(default_factory=LatencyStats)
    qps: float | None = None
    errors: list[str] = field(default_factory=list)
    raw_latencies: list[float] = field(default_factory=list)


class PerformanceTester:
    def __init__(self, session_wrapper: SessionWrapper):
        self._wrapper = session_wrapper

    async def run_latency_test(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        iterations: int = 50,
        warmup: int = 3,
    ) -> PerformanceReport:
        report = PerformanceReport(
            test_type="latency",
            tool_name=tool_name,
            arguments=arguments,
            started_at=datetime.now(),
        )

        for i in range(warmup):
            try:
                await self._wrapper.call_tool(tool_name, arguments)
            except Exception:
                pass

        latencies: list[float] = []
        for i in range(iterations):
            try:
                start = time.monotonic()
                result = await self._wrapper.call_tool(tool_name, arguments)
                elapsed = (time.monotonic() - start) * 1000

                report.total_requests += 1
                if hasattr(result, "isError") and result.isError:
                    report.failed_requests += 1
                    report.errors.append(f"#{i+1}: isError=True")
                else:
                    report.successful_requests += 1
                latencies.append(elapsed)
            except Exception as e:
                report.total_requests += 1
                report.failed_requests += 1
                report.errors.append(f"#{i+1}: {e}")

        report.raw_latencies = latencies
        report.latency_stats = _compute_stats(latencies)
        if latencies:
            total_time = sum(latencies) / 1000.0
            report.qps = report.successful_requests / total_time if total_time > 0 else 0
        report.finished_at = datetime.now()

        return report

    async def run_concurrency_test(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        concurrency: int = 5,
        requests_per_worker: int = 10,
    ) -> PerformanceReport:
        report = PerformanceReport(
            test_type="concurrency",
            tool_name=tool_name,
            arguments=arguments,
            started_at=datetime.now(),
        )

        async def worker():
            local_latencies: list[float] = []
            for _ in range(requests_per_worker):
                try:
                    start = time.monotonic()
                    result = await self._wrapper.call_tool(tool_name, arguments)
                    elapsed = (time.monotonic() - start) * 1000
                    if hasattr(result, "isError") and result.isError:
                        report.failed_requests += 1
                        report.errors.append(f"isError=True")
                    else:
                        report.successful_requests += 1
                    local_latencies.append(elapsed)
                except Exception as e:
                    report.failed_requests += 1
                    report.errors.append(str(e))
                report.total_requests += 1
            return local_latencies

        overall_start = time.monotonic()
        results = await asyncio.gather(*[worker() for _ in range(concurrency)])
        overall_elapsed = (time.monotonic() - overall_start) * 1000

        all_latencies = []
        for lat in results:
            all_latencies.extend(lat)

        report.raw_latencies = all_latencies
        report.latency_stats = _compute_stats(all_latencies)
        report.qps = report.total_requests / (overall_elapsed / 1000) if overall_elapsed > 0 else 0
        report.finished_at = datetime.now()

        return report


def _compute_stats(latencies: list[float]) -> LatencyStats:
    if not latencies:
        return LatencyStats()

    sorted_lat = sorted(latencies)
    n = len(sorted_lat)

    return LatencyStats(
        min_ms=sorted_lat[0],
        max_ms=sorted_lat[-1],
        avg_ms=statistics.mean(sorted_lat),
        p50_ms=sorted_lat[int(n * 0.5)],
        p95_ms=sorted_lat[min(int(n * 0.95), n - 1)],
        p99_ms=sorted_lat[min(int(n * 0.99), n - 1)],
        std_dev_ms=statistics.stdev(sorted_lat) if n > 1 else 0,
    )
