# ADK Tools Pattern: SkillRuntime

Every ADK skill produced by this tool follows the `SkillRuntime` class convention.

## Class structure

```python
class SkillRuntime:
    def __init__(self, auth_client: AuthClient, db: Database):
        # All dependencies injected here — auth, DB, HTTP clients, etc.
        self.auth_client = auth_client
        self.db = db

    def tool_one(self, param: str) -> dict:
        """Docstring becomes the ADK tool description — write it clearly."""
        token = self.auth_client.get_token()
        return self.db.query(param, token)

    def tool_two(self, param: str, limit: int = 10) -> list[dict]:
        """Returns up to `limit` results for param."""
        return self.db.query_list(param, limit=limit)

    def get_tools(self) -> list:
        return [self.tool_one, self.tool_two]
```

## Rules

1. Every public method (except `get_tools`) must be listed in `adk_additional_tools` in SKILL.md
2. Every name in `adk_additional_tools` must be a public method — `quick_validate.py` enforces this
3. `get_tools()` returns bound methods — dependencies are captured in `self`, no args needed at call time
4. Docstrings become ADK tool descriptions — write them as descriptions, not code comments

## Project-level runtime_factory.py

```python
# runtime_factory.py — lives at project root, not inside a skill
from skills.account_movements.tools import SkillRuntime as AccountRuntime
from skills.transfer.tools import SkillRuntime as TransferRuntime
from myapp.clients import BankAuthClient, BankDB
import os


def build_runtimes() -> dict[str, object]:
    auth = BankAuthClient(api_key=os.environ["BANK_API_KEY"])
    db = BankDB(url=os.environ["DB_URL"])
    return {
        "account-movements": AccountRuntime(auth_client=auth, db=db),
        "transfer": TransferRuntime(auth_client=auth, db=db),
    }
```

## Per-skill evals/eval_factory.py

```python
# evals/eval_factory.py — mock runtime, no real credentials
from ..tools import SkillRuntime


def build_eval_runtime() -> SkillRuntime:
    return SkillRuntime(
        auth_client=MockBankAuth(token="test-token"),
        db=MockBankDB(fixtures_path="evals/fixtures/transactions.json"),
    )
```
