"""noteのハッシュタグRSSとキーワード検索から、ポケモンチャンピオンズのシングルバトル関連記事を集める。"""
import json, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from html import unescape

# 集めるハッシュタグ（# は不要）。増やしたいときはここに足す。
TAGS = [
    "ポケモンチャンピオンズ",
    "ポケチャン",
    "シングルバトル",
    "ポケモンシングル",
    "シングルバトル構築記事",
    "ポケモンチャンピオンズ構築記事",
]
# キーワード検索で集める（タグなし記事も対象）
SEARCH_KEYWORDS = ["ポケモンチャンピオンズ"]
# 記事のタイトル・冒頭・タグに、チャンピオンズが含まれるか。
NEED_GAME = re.compile(r"チャンピオンズ|ポケチャン|champions", re.I)
# 記事の本文・タイトルに「シングル」が含まれるかをチェック。
NEED_SINGLES = re.compile(r"シングル|singles?", re.I)

OUT = Path("docs/singles.json")
AUTHOR_CACHE_FILE = Path("docs/.author_cache.json")
JST = timezone(timedelta(hours=9))
DC = "{http://purl.org/dc/elements/1.1/}"


def load_author_cache():
    """著者名キャッシュを読み込む"""
    if AUTHOR_CACHE_FILE.exists():
        return json.loads(AUTHOR_CACHE_FILE.read_text("utf-8"))
    return {}


def save_author_cache(cache):
    """著者名キャッシュを保存"""
    AUTHOR_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), "utf-8")


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


def fetch_keyword(keyword, pages=2):
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

        for match in re.finditer(
            r'<a[^>]+href="(https://note\.com/[^/"]+/n/[^/"]+)"[^>]*>([^<]+)</a>',
            html
        ):
            link = match.group(1)
            title = unescape(match.group(2)).strip()

            if not title:
                continue

            # URLからユーザーIDを抽出
            author_match = re.search(r"https://note\.com/([^/]+)/", link)
            author = author_match.group(1) if author_match else ""

            # 日付を取得（個別ページにアクセス）
            try:
                req2 = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=10) as res2:
                    article_html = res2.read().decode("utf-8")

                date_match = re.search(
                    r'<time[^>]*datetime="(\d{4}-\d{2}-\d{2})',
                    article_html
                )
                date = date_match.group(1) if date_match else datetime.now(JST).date().isoformat()
            except Exception:
                date = datetime.now(JST).date().isoformat()

            yield {
                "link": link,
                "title": title,
                "author": author,
                "date": date,
                "summary": "",
            }


def main():
    author_cache = load_author_cache()

    found, ok = {}, 0
    for tag in TAGS:
        try:
            for a in fetch_tag(tag):
                entry = found.setdefault(a["link"], {**a, "tags": set()})
                entry["tags"].add(tag)
            ok += 1
        except Exception as e:
            print(f"取得失敗 #{tag}: {e}", file=sys.stderr)

    # キーワード検索でタグなし記事も取得
    for keyword in SEARCH_KEYWORDS:
        try:
            for a in fetch_keyword(keyword):
                if a["link"] not in found:
                    found[a["link"]] = {**a, "tags": set()}
            ok += 1
        except Exception as e:
            print(f"キーワード検索失敗 '{keyword}': {e}", file=sys.stderr)

    if ok == 0:
        sys.exit("すべてのタグで取得に失敗したため、更新しません。")

    # 著者名を取得（キャッシュから または プロフィールページからスクレイピング）
    for a in found.values():
        author_id = a["author"]
        if author_id:
            if author_id not in author_cache:
                author_cache[author_id] = fetch_author_name(author_id)
            a["author"] = author_cache[author_id]

    save_author_cache(author_cache)

    old = {}
    if OUT.exists():
        old = {a["link"]: a for a in json.loads(OUT.read_text("utf-8")).get("articles", [])}

    two_months_ago = (datetime.now(JST) - timedelta(days=60)).date()
    for a in found.values():
        text = " ".join([a["title"], a["summary"], *a["tags"]])
        # 「チャンピオンズ」または「構築記事」タグを含み、タイトル・本文に「シングル」を含む
        has_game = NEED_GAME.search(text) or "ポケモンチャンピオンズ構築記事" in a["tags"]
        has_singles = NEED_SINGLES.search(text)
        if has_game and has_singles and a["date"] >= str(two_months_ago):
            old[a["link"]] = {k: a[k] for k in ("link", "title", "author", "date")}

    articles = sorted(old.values(), key=lambda a: a["date"], reverse=True)
    OUT.write_text(
        json.dumps({"updated": datetime.now(JST).isoformat(timespec="minutes"), "articles": articles},
                   ensure_ascii=False, indent=1),
        "utf-8",
    )
    print(f"{len(articles)}件")


if __name__ == "__main__":
    main()
