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


class TestFileSizeSettings:
    """ファイルサイズ設定のテスト"""

    def test_default_max_file_size_mb(self):
        """デフォルトのファイルサイズ上限が50MBであること"""
        s = Settings()
        assert s.max_file_size_mb == 50

    def test_max_file_size_is_int(self):
        """ファイルサイズ上限がint型であること"""
        s = Settings()
        assert isinstance(s.max_file_size_mb, int)

    def test_max_file_size_env_override(self, monkeypatch):
        """環境変数でファイルサイズ上限を変更できること"""
        monkeypatch.setenv("MAX_FILE_SIZE_MB", "100")
        s = Settings()
        assert s.max_file_size_mb == 100
