import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_quant_finance_mcp.quota import (
    FREE_REQUESTS_PER_DAY,
    FREE_REQUESTS_PER_MINUTE,
    FREE_REQUESTS_PER_TOOL_PER_DAY,
    FreeTierQuotaLimiter,
)
from hpsilab_quant_finance_mcp.service import QuantFinanceService


class FakeClock:
    def __init__(self):
        self.wall = 1_800_000_000.0
        self.monotonic = 10_000.0

    def advance(self, seconds):
        self.wall += seconds
        self.monotonic += seconds


class StaticCredentialProvider:
    def get_api_key(self):
        return "hpsi_test"


class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.limiter = FreeTierQuotaLimiter(
            wall_time=lambda: self.clock.wall,
            monotonic=lambda: self.clock.monotonic,
        )

    def test_ten_requests_per_rolling_minute(self):
        for _ in range(FREE_REQUESTS_PER_MINUTE):
            self.assertIsNone(self.limiter.check_and_consume("key", "analyze_stock"))

        violation = self.limiter.check_and_consume("key", "analyze_stock")
        self.assertEqual((violation.limit, violation.window), (10, "minute"))

        self.clock.advance(60)
        self.assertIsNone(self.limiter.check_and_consume("key", "analyze_stock"))

    def test_twenty_requests_per_tool_per_utc_day(self):
        for _ in range(FREE_REQUESTS_PER_TOOL_PER_DAY):
            self.assertIsNone(self.limiter.check_and_consume("key", "get_iv_radar"))
            self.clock.advance(6.1)

        violation = self.limiter.check_and_consume("key", "get_iv_radar")
        self.assertEqual((violation.limit, violation.window, violation.tool), (20, "day", "get_iv_radar"))

    def test_one_hundred_total_requests_per_utc_day(self):
        for tool_number in range(5):
            for _ in range(FREE_REQUESTS_PER_TOOL_PER_DAY):
                self.assertIsNone(self.limiter.check_and_consume("key", f"tool_{tool_number}"))
                self.clock.advance(6.1)

        violation = self.limiter.check_and_consume("key", "tool_6")
        self.assertEqual((violation.limit, violation.window), (FREE_REQUESTS_PER_DAY, "day"))
        self.assertIsNone(violation.tool)

    def test_daily_counters_reset_at_next_utc_day(self):
        for _ in range(FREE_REQUESTS_PER_TOOL_PER_DAY):
            self.assertIsNone(self.limiter.check_and_consume("key", "get_monte_carlo"))
            self.clock.advance(6.1)

        self.assertIsNotNone(self.limiter.check_and_consume("key", "get_monte_carlo"))
        self.clock.advance(86_400)
        self.assertIsNone(self.limiter.check_and_consume("key", "get_monte_carlo"))

    def test_local_rejection_does_not_construct_downstream_client(self):
        for _ in range(FREE_REQUESTS_PER_MINUTE):
            self.assertIsNone(self.limiter.check_and_consume("hpsi_test", "analyze_stock"))

        client_factory = mock.Mock(side_effect=AssertionError("must not send a request"))
        result = QuantFinanceService(
            credential_provider=StaticCredentialProvider(),
            client_factory=client_factory,
            quota_limiter=self.limiter,
        ).call("analyze_stock", "NVDA")

        self.assertEqual(result["status_code"], 429)
        self.assertEqual(result["details"]["limit"], 10)
        client_factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
