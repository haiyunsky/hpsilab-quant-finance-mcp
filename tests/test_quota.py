import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_quant_finance_mcp.quota import (
    LOCAL_REQUESTS_PER_MINUTE,
    BurstRateLimiter,
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
        self.limiter = BurstRateLimiter(
            wall_time=lambda: self.clock.wall,
            monotonic=lambda: self.clock.monotonic,
        )

    def test_ten_requests_per_rolling_minute(self):
        for _ in range(LOCAL_REQUESTS_PER_MINUTE):
            self.assertIsNone(self.limiter.check_and_consume("key", "analyze_stock"))

        violation = self.limiter.check_and_consume("key", "analyze_stock")
        self.assertEqual((violation.limit, violation.window), (10, "minute"))

        self.clock.advance(60)
        self.assertIsNone(self.limiter.check_and_consume("key", "analyze_stock"))

    def test_no_day_scoped_gate_survives(self):
        # Credits are the unit of entitlement, and this process can see neither
        # a balance nor a plan. A Pro key spending 15,000 Credits must not be
        # stopped here at the Free tier's old 100/day and 20/tool/day numbers.
        for hour in range(24):
            for _ in range(LOCAL_REQUESTS_PER_MINUTE):
                self.assertIsNone(self.limiter.check_and_consume("key", "get_iv_radar"))
            self.clock.advance(60)

        self.assertIsNone(self.limiter.check_and_consume("key", "get_iv_radar"))

    def test_limit_is_per_api_key(self):
        for _ in range(LOCAL_REQUESTS_PER_MINUTE):
            self.assertIsNone(self.limiter.check_and_consume("key_one", "analyze_stock"))

        self.assertIsNotNone(self.limiter.check_and_consume("key_one", "analyze_stock"))
        self.assertIsNone(self.limiter.check_and_consume("key_two", "analyze_stock"))

    def test_local_rejection_does_not_construct_downstream_client(self):
        for _ in range(LOCAL_REQUESTS_PER_MINUTE):
            self.assertIsNone(self.limiter.check_and_consume("hpsi_test", "analyze_stock"))

        client_factory = mock.Mock(side_effect=AssertionError("must not send a request"))
        result = QuantFinanceService(
            credential_provider=StaticCredentialProvider(),
            client_factory=client_factory,
            quota_limiter=self.limiter,
        ).call("analyze_stock", "NVDA")

        self.assertEqual(result["status_code"], 429)
        self.assertEqual(result["error"], "rate_limit_exceeded")
        self.assertEqual(result["used"], 10)
        self.assertEqual(result["remaining"], 0)
        self.assertEqual(result["window"], "minute")
        self.assertTrue(result["reset_at"].endswith("Z"))
        self.assertEqual(result["details"]["limit"], 10)
        self.assertEqual(result["details"]["reset_at"], result["reset_at"])
        client_factory.assert_not_called()

    def test_rate_limit_carries_no_conversion_guidance(self):
        # A 429 is resolved by waiting. Selling a plan to a caller whose
        # problem clears itself inside a minute is the exact confusion the
        # hosted contract removed from its own 429 on 2026-08-08.
        for _ in range(LOCAL_REQUESTS_PER_MINUTE):
            self.limiter.check_and_consume("hpsi_test", "analyze_stock")

        result = QuantFinanceService(
            credential_provider=StaticCredentialProvider(),
            client_factory=mock.Mock(side_effect=AssertionError("must not send a request")),
            quota_limiter=self.limiter,
        ).call("analyze_stock", "NVDA")

        for absent in ("upgrade", "next_action", "register", "upgrade_hint", "accepts"):
            self.assertNotIn(absent, result)
        self.assertEqual(
            result["next_actions"],
            [{"type": "retry_after", "seconds": 60}],
        )


if __name__ == "__main__":
    unittest.main()
