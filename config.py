"""スクレイピング設定"""
import os
from datetime import timedelta

# Python バージョン設定
PYTHON_VERSION = "3.12"

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
CACHE_EXPIRE_DAYS = int(os.getenv("NOTE_CACHE_EXPIRE_DAYS", "30"))

# User-Agent リスト（ローテーション用）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "note-matome/1.0",
]

# ログレベル
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 設定値の検証
if TIMEOUT_RSS <= 0:
    raise ValueError("TIMEOUT_RSS は 0 より大きい値である必要があります")
if TIMEOUT_PAGE <= 0:
    raise ValueError("TIMEOUT_PAGE は 0 より大きい値である必要があります")
if TIMEOUT_AUTHOR <= 0:
    raise ValueError("TIMEOUT_AUTHOR は 0 より大きい値である必要があります")
if PAGINATING_DELAY < 0:
    raise ValueError("PAGINATING_DELAY は 0 以上の値である必要があります")
if PAGES_MANUAL <= 0:
    raise ValueError("PAGES_MANUAL は 0 より大きい値である必要があります")
if PAGES_AUTO <= 0:
    raise ValueError("PAGES_AUTO は 0 より大きい値である必要があります")
if CACHE_EXPIRE_DAYS <= 0:
    raise ValueError("CACHE_EXPIRE_DAYS は 0 より大きい値である必要があります")

