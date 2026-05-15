import requests


class SkillRuntime:
    def __init__(self, base_url: str, session: requests.Session = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def get_accounts(self) -> list[dict]:
        """Returns the list of all bank accounts for the current user."""
        response = self.session.get(f"{self.base_url}/accounts")
        response.raise_for_status()
        return response.json()

    def get_balance(self, account: str) -> dict:
        """Returns the current balance for the specified account identifier."""
        response = self.session.get(f"{self.base_url}/balance/{account}")
        response.raise_for_status()
        return response.json()

    def get_tools(self) -> list:
        return [self.get_accounts, self.get_balance]
