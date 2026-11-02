"""スクレイピング設定"""
import os
from datetime import timedelta

# タイムアウト設定（秒）
TIMEOUT_RSS = int(os.getenv("NOTE_TIMEOUT_RSS", "30"))
TIMEOUT_PAGE = int(os.getenv("NOTE_TIMEOUT_PAGE", "10"))
TIMEOUT_AUTHOR = int(os.getenv("NOTE_TIMEOUT_AUTHOR", "10"))

# ページング設定
PAGINATING_DELAY = float(os.getenv("NOTE_PAGINATING_DELAY", "2.5"))
PAGES_MANUAL = int(os.getenv("NOTE_PAGES_MANUAL", "20"))
PAGES_AUTO = int(os.getenv("NOTE_PAGES_AUTO", "15"))

# キャッシュ設定
CACHE_DIR = "docs"
AUTHOR_CACHE_FILE = f"{CACHE_DIR}/.author_cache.json"

# User-Agent リスト（ローテーション用）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "note-matome/1.0",
]

# ログレベル
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
