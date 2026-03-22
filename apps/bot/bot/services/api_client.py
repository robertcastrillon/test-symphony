import httpx


class UnlinkedUserError(Exception):
    """Raised when a Telegram user has not linked their account."""


class BotApiClient:
    """HTTP client for communicating with the ChronoTrack API."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def authenticate(self, telegram_chat_id: int | str) -> str:
        """Fetch API token for a linked user.

        Raises UnlinkedUserError if the chat_id is not linked to any account.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/telegram/token",
                json={"telegram_chat_id": str(telegram_chat_id)},
            )
        if response.status_code == 404:
            raise UnlinkedUserError(
                f"No account linked for telegram_chat_id={telegram_chat_id}"
            )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]

    async def get_active_session(self, token: str) -> dict | None:
        """Return the active session or None if there is none."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/sessions",
                params={"active": "true"},
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if isinstance(items, list) and items:
            return items[0]
        return None

    async def stop_session(self, token: str) -> dict:
        """Stop the current active session and return the stopped session."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/sessions/stop",
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        return response.json()

    async def create_manual_session(self, token: str, data: dict) -> dict:
        """Create a manual time entry session."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/sessions",
                json=data,
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        return response.json()

    async def get_report(self, token: str, period: str = "week") -> dict:
        """Get the summary report for the given period."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/reports/summary",
                params={"period": period},
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        return response.json()

    async def link_account(self, email: str, telegram_chat_id: int | str) -> dict:
        """Link a Telegram chat ID to a user account by email."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/telegram/link",
                json={"email": email, "telegram_chat_id": str(telegram_chat_id)},
            )
        return response
