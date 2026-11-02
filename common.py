"""noteのスクレイピング共通関数"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

JST = timezone(timedelta(hours=9))
DC = "{http://purl.org/dc/elements/1.1/}"


def load_author_cache(cache_file):
	"""著者名キャッシュを読み込む"""
	if cache_file.exists():
		return json.loads(cache_file.read_text("utf-8"))
	return {}


def save_author_cache(cache, cache_file):
	"""著者名キャッシュを保存"""
	cache_file.write_text(json.dumps(cache, ensure_ascii=False), "utf-8")


def fetch_author_name(author_id):
	"""note.com のプロフィールページから著者名を取得"""
	try:
		url = f"https://note.com/{author_id}"
		req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
		with urllib.request.urlopen(req, timeout=10) as res:
			html = res.read().decode("utf-8")

		# プロフィール名を抽出（<h1>や<meta name="description">など複数のパターンを試す）
		match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
		if match:
			name = match.group(1).strip()
			if name and name != author_id:
				return name

		# 別パターン：<title> から取得
		match = re.search(r'<title>([^|<]+)', html)
		if match:
			name = match.group(1).strip()
			if name and name != author_id:
				return name
	except Exception as e:
		print(f"著者名取得失敗 {author_id}: {e}", file=sys.stderr)

	return author_id


def fetch_tag(tag):
	"""ハッシュタグRSSから記事を取得"""
	url = f"https://note.com/hashtag/{urllib.parse.quote(tag)}/rss"
	req = urllib.request.Request(url, headers={"User-Agent": "note-matome/1.0"})
	with urllib.request.urlopen(req, timeout=30) as res:
		root = ET.fromstring(res.read())
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

		yield {
			"link": link,
			"title": (item.findtext("title") or "").strip(),
			"author": author,
			"date": date,
			"summary": re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()[:200],
		}


def fetch_keyword(keyword, pages=5, fetch_body=False):
	"""キーワード検索で記事を取得（タグなし記事も対象）"""
	for page in range(1, pages + 1):
		url = f"https://note.com/search?q={urllib.parse.quote(keyword)}&sort=new&page={page}"
		req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
		try:
			with urllib.request.urlopen(req, timeout=30) as res:
				html = res.read().decode("utf-8")
		except Exception as e:
			print(f"キーワード検索失敗 '{keyword}' (page {page}): {e}", file=sys.stderr)
			continue

		found_articles = False
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
				req2 = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
				with urllib.request.urlopen(req2, timeout=10) as res2:
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

				article = {
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

				yield article

			except Exception as e:
				print(f"記事処理エラー {link}: {e}", file=sys.stderr)

		# 次のページへ行く前に遅延（note.comへの負荷軽減）
		if found_articles and page < pages:
			time.sleep(2)
