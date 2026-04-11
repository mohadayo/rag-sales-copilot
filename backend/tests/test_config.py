"""config モジュールのユニットテスト"""

from app.core.config import Settings


class TestTimeoutSettings:
    """タイムアウト設定のテスト"""

    def test_default_openai_timeout(self):
        """デフォルトのOpenAIタイムアウトが30秒であること"""
        s = Settings()
        assert s.openai_timeout == 30.0

    def test_default_openai_connect_timeout(self):
        """デフォルトのOpenAI接続タイムアウトが10秒であること"""
        s = Settings()
        assert s.openai_connect_timeout == 10.0

    def test_timeout_settings_are_float(self):
        """タイムアウト設定がfloat型であること"""
        s = Settings()
        assert isinstance(s.openai_timeout, float)
        assert isinstance(s.openai_connect_timeout, float)
