import os
import unittest
from unittest.mock import AsyncMock, patch

from app.config import get_settings
from app.main import health


class HealthTests(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    async def test_health_exposes_release_id_without_secrets(self) -> None:
        with patch.dict(os.environ, {"RELEASE_ID": "v0.2.0-beta-test"}):
            get_settings.cache_clear()
            with patch("app.main.check_database_connection", new=AsyncMock(return_value=True)):
                response = await health()

        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["database"], "ok")
        self.assertEqual(response["release"], "v0.2.0-beta-test")
        self.assertNotIn("telegram_bot_token", response)
        self.assertNotIn("jwt_secret", response)
