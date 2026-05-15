import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import SkillRuntime


class MockBankSession:
    """HTTP session mock returning fixture data."""

    ACCOUNTS = [
        {"id": "ACC-001", "name": "Main Checking", "type": "checking"},
        {"id": "ACC-002", "name": "Savings", "type": "savings"},
    ]

    BALANCES = {
        "ACC-001": {"account": "ACC-001", "balance": 1250.75, "currency": "EUR"},
        "ACC-002": {"account": "ACC-002", "balance": 8420.00, "currency": "EUR"},
    }

    def get(self, url: str):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        if url.endswith("/accounts"):
            response.json.return_value = self.ACCOUNTS
        else:
            account = url.split("/balance/")[-1]
            data = self.BALANCES.get(account, {"error": "account not found"})
            response.json.return_value = data
        return response


def build_eval_runtime() -> SkillRuntime:
    """Return SkillRuntime with mock HTTP session — no real API needed."""
    return SkillRuntime(base_url="http://mock-bank.local", session=MockBankSession())
