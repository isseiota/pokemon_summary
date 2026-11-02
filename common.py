"""noteのスクレイピング共通関数"""
import json
import logging
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Generator, Optional, Dict, Any

import config

# ロギング設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

JST = timezone(timedelta(hours=9))
DC = "{http://purl.org/dc/elements/1.1/}"


def _get_random_user_agent() -> str:
	"""ランダムな User-Agent を取得"""
	return random.choice(config.USER_AGENTS)


def _is_cache_expired(cache_file: Path) -> bool:
	"""キャッシュが有効期限切れかどうかを判定"""
	if not cache_file.exists():
		return True

	file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
	return file_age > timedelta(days=config.CACHE_EXPIRE_DAYS)


def load_author_cache(cache_file: Optional[Path] = None) -> Dict[str, str]:
	"""著者名キャッシュを読み込む"""
	if cache_file is None:
		cache_file = Path(config.AUTHOR_CACHE_FILE)
	else:
		cache_file = Path(cache_file)

	# キャッシュの有効期限をチェック
	if _is_cache_expired(cache_file):
		logger.info(f"キャッシュが有効期限切れです: {cache_file}")
		return {}

	if cache_file.exists():
		try:
			content = cache_file.read_text("utf-8")
			cache = json.loads(content)
			logger.info(f"著者名キャッシュを読み込み: {len(cache)}件")
			return cache
		except json.JSONDecodeError as e:
			logger.warning(f"著者名キャッシュが破損しています。リセットします: {e}")
			return {}
		except Exception as e:
			logger.error(f"著者名キャッシュの読み込みに失敗: {e}")
			return {}
	return {}


def save_author_cache(cache: Dict[str, str], cache_file: Optional[Path] = None) -> None:
	"""著者名キャッシュを保存"""
	if cache_file is None:
		cache_file = Path(config.AUTHOR_CACHE_FILE)
	else:
		cache_file = Path(cache_file)

	try:
		# ディレクトリが存在しない場合は自動作成
		cache_file.parent.mkdir(parents=True, exist_ok=True)
		cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), "utf-8")
		logger.info(f"著者名キャッシュを保存: {len(cache)}件")
	except Exception as e:
		logger.error(f"著者名キャッシュの保存に失敗: {e}")


def fetch_author_name(author_id: str, max_retries: int = 2) -> str:
	"""note.com のプロフィールページから著者名を取得"""
	for attempt in range(max_retries):
		try:
			url = f"https://note.com/{author_id}"
			req = urllib.request.Request(url, headers={"User-Agent": _get_random_user_agent()})
			with urllib.request.urlopen(req, timeout=config.TIMEOUT_AUTHOR) as res:
				html = res.read().decode("utf-8")

			# プロフィール名を抽出（<h1>や<meta name="description">など複数のパターンを試す）
			match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
			if match:
				name = match.group(1).strip()
				if name and name != author_id:
					logger.debug(f"著者名取得成功: {author_id} -> {name}")
					return name

			# 別パターン：<title> から取得
			match = re.search(r'<title>([^|<]+)', html)
			if match:
				name = match.group(1).strip()
				if name and name != author_id:
					logger.debug(f"著者名取得成功: {author_id} -> {name}")
					return name
		except urllib.error.URLError as e:
			if attempt < max_retries - 1:
				logger.debug(f"著者名取得リトライ {author_id} ({attempt + 1}/{max_retries}): {e}")
				time.sleep(1)
			else:
				logger.warning(f"著者名取得失敗 {author_id}: {e}")
		except Exception as e:
			logger.warning(f"著者名取得エラー {author_id}: {e}")

	return author_id


def fetch_tag(tag: str, max_retries: int = 2) -> Generator[Dict[str, Any], None, None]:
	"""ハッシュタグRSSから記事を取得"""
	for attempt in range(max_retries):
		try:
			url = f"https://note.com/hashtag/{urllib.parse.quote(tag)}/rss"
			req = urllib.request.Request(url, headers={"User-Agent": _get_random_user_agent()})
			with urllib.request.urlopen(req, timeout=config.TIMEOUT_RSS) as res:
				root = ET.fromstring(res.read())

			count = 0
			for item in root.iter("item"):
				link = (item.findtext("link") or "").strip()
				if not link:
					continue
				parts = urllib.parse.urlsplit(link)
				link = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
				try:
					date = parsedate_to_datetime(item.findtext("pubDate")).astimezone(JST).date().isoformat()
				except Exception:
					date = datetime.now(JST).date().isoformat()

				# 著者情報：RSS から取得、またはURLからユーザーIDを抽出
				author = (item.findtext(f"{DC}creator") or "").strip()
				if not author:
					match = re.search(r"https://note\.com/([^/]+)/", link)
					author = match.group(1) if match else ""

				count += 1
				yield {
					"link": link,
					"title": (item.findtext("title") or "").strip(),
					"author": author,
					"date": date,
					"summary": re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()[:200],
				}

			logger.info(f"タグ '{tag}' から {count}件の記事を取得")
			return

		except ET.ParseError as e:
			logger.warning(f"RSS XML パースエラー (タグ: {tag}, 試行: {attempt + 1}/{max_retries}): {e}")
			if attempt < max_retries - 1:
				time.sleep(1)
		except urllib.error.URLError as e:
			logger.warning(f"RSS 取得失敗 (タグ: {tag}, 試行: {attempt + 1}/{max_retries}): {e}")
			if attempt < max_retries - 1:
				time.sleep(1)
		except Exception as e:
			logger.error(f"タグ取得エラー '{tag}': {e}")
			return

	logger.error(f"タグ取得失敗 (すべてのリトライ完了): {tag}")


def fetch_keyword(
	keyword: str,
	pages: int = 5,
	fetch_body: bool = False,
	max_retries: int = 2
) -> Generator[Dict[str, Any], None, None]:
	"""キーワード検索で記事を取得（タグなし記事も対象）"""
	total_count = 0
	for page in range(1, pages + 1):
		url = f"https://note.com/search?q={urllib.parse.quote(keyword)}&sort=new&page={page}"
		req = urllib.request.Request(url, headers={"User-Agent": _get_random_user_agent()})

		for attempt in range(max_retries):
			try:
				with urllib.request.urlopen(req, timeout=config.TIMEOUT_PAGE) as res:
					html = res.read().decode("utf-8")
				break
			except urllib.error.URLError as e:
				if attempt < max_retries - 1:
					logger.debug(f"キーワード検索リトライ '{keyword}' (page {page}, 試行 {attempt + 1}/{max_retries})")
					time.sleep(1)
				else:
					logger.warning(f"キーワード検索失敗 '{keyword}' (page {page}): {e}")
					continue
			except Exception as e:
				logger.error(f"キーワード検索エラー '{keyword}' (page {page}): {e}")
				continue

		found_articles = False
		page_count = 0
		for match in re.finditer(r'href="(https://note\.com/[^/"]+/n/[^"]+)"', html):
			link = match.group(1)
			if not link or "/n/" not in link:
				continue

			found_articles = True

			# URLからユーザーIDを抽出
			author_match = re.search(r"https://note\.com/([^/]+)/", link)
			author = author_match.group(1) if author_match else ""

			# 日付を取得（個別ページにアクセス）
			try:
				req2 = urllib.request.Request(link, headers={"User-Agent": _get_random_user_agent()})
				with urllib.request.urlopen(req2, timeout=config.TIMEOUT_PAGE) as res2:
					article_html = res2.read().decode("utf-8")

				# タイトルを取得
				title_match = re.search(r'<title>([^|<]+)', article_html)
				title = title_match.group(1).strip() if title_match else ""

				# タイトルがキーワードを含むかチェック
				if not title or keyword not in title:
					continue

				# 日付を取得（複数のパターンを試す）
				date_match = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})', article_html)
				if not date_match:
					date_match = re.search(r'<time[^>]*datetime="(\d{4}-\d{2}-\d{2})', article_html)
				date = date_match.group(1) if date_match else datetime.now(JST).date().isoformat()

				article: Dict[str, Any] = {
					"link": link,
					"title": title,
					"author": author,
					"date": date,
					"summary": "",
				}

				if fetch_body:
					body = re.sub(r"<script[^>]*>.*?</script>", "", article_html, flags=re.DOTALL)
					body = re.sub(r"<[^>]+>", "", body)
					article["body"] = body

				page_count += 1
				total_count += 1
				yield article

			except Exception as e:
				logger.debug(f"記事処理エラー {link}: {e}")

		# 次のページへ行く前に遅延（note.comへの負荷軽減）
		if found_articles and page < pages:
			logger.debug(f"ページング遅延: {config.PAGINATING_DELAY}秒")
			time.sleep(config.PAGINATING_DELAY)

		logger.info(f"キーワード '{keyword}' ページ {page}: {page_count}件")

	logger.info(f"キーワード '{keyword}' 合計取得: {total_count}件")
