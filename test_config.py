"""設定とユニットテスト"""
import sys
import unittest
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

import config


class TestConfig(unittest.TestCase):
    """設定値のテスト"""

    def test_timeout_values_positive(self):
        """タイムアウト値が正の値であることを確認"""
        self.assertGreater(config.TIMEOUT_RSS, 0)
        self.assertGreater(config.TIMEOUT_PAGE, 0)
        self.assertGreater(config.TIMEOUT_AUTHOR, 0)

    def test_paginating_delay_non_negative(self):
        """ページング遅延が 0 以上であることを確認"""
        self.assertGreaterEqual(config.PAGINATING_DELAY, 0)

    def test_pages_values_positive(self):
        """ページ取得数が正の値であることを確認"""
        self.assertGreater(config.PAGES_MANUAL, 0)
        self.assertGreater(config.PAGES_AUTO, 0)

    def test_cache_expire_days_positive(self):
        """キャッシュ有効期限が正の値であることを確認"""
        self.assertGreater(config.CACHE_EXPIRE_DAYS, 0)

    def test_user_agents_not_empty(self):
        """User-Agent リストが空でないことを確認"""
        self.assertGreater(len(config.USER_AGENTS), 0)

    def test_log_level_valid(self):
        """ログレベルが有効な値であることを確認"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.assertIn(config.LOG_LEVEL, valid_levels)

    def test_python_version_format(self):
        """Python バージョンのフォーマットが正しいことを確認"""
        parts = config.PYTHON_VERSION.split(".")
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[0].isdigit())
        self.assertTrue(parts[1].isdigit())

    def test_cache_dir_exists(self):
        """キャッシュディレクトリが存在することを確認"""
        cache_dir = Path(config.CACHE_DIR)
        self.assertTrue(cache_dir.exists() or cache_dir.parent.exists())

    def test_config_validation(self):
        """設定値の検証が正しく機能することを確認"""
        # これは config.py の読み込み時に実行される
        # エラーが発生していないことを確認
        self.assertIsNotNone(config)


class TestCommonFunctions(unittest.TestCase):
    """common モジュールのテスト"""

    def setUp(self):
        """テスト前の準備"""
        import common
        self.common = common

    def test_get_random_user_agent(self):
        """ランダム User-Agent 取得のテスト"""
        user_agent = self.common._get_random_user_agent()
        self.assertIsInstance(user_agent, str)
        self.assertGreater(len(user_agent), 0)
        self.assertIn(user_agent, config.USER_AGENTS)

    def test_load_nonexistent_cache(self):
        """存在しないキャッシュの読み込みテスト"""
        from pathlib import Path
        nonexistent_file = Path("/nonexistent/path/.cache.json")
        cache = self.common.load_author_cache(nonexistent_file)
        self.assertEqual(cache, {})

    def test_cache_file_path_types(self):
        """キャッシュファイルパスの型テスト"""
        from pathlib import Path

        # Path オブジェクトでの呼び出し
        cache1 = self.common.load_author_cache(Path(config.AUTHOR_CACHE_FILE))
        self.assertIsInstance(cache1, dict)

        # None での呼び出し（デフォルト）
        cache2 = self.common.load_author_cache(None)
        self.assertIsInstance(cache2, dict)


if __name__ == "__main__":
    unittest.main()
