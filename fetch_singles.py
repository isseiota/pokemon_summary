"""noteのハッシュタグRSSから、ポケモンチャンピオンズのシングルバトル関連記事を集める。"""
import json, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# 集めるハッシュタグ（# は不要）。増やしたいときはここに足す。
TAGS = [
    "ポケモンチャンピオンズ",
    "ポケチャン",
    "シングルバトル",
    "ポケモンシングル",
    "シングルバトル構築記事",
    "ポケモンチャンピオンズ構築記事",
]
# 記事のタイトル・冒頭・タグに、チャンピオンズが含まれるか。
NEED_GAME = re.compile(r"チャンピオンズ|ポケチャン|champions", re.I)
# 記事の本文・タイトルに「シングル」が含まれるかをチェック。
NEED_SINGLES = re.compile(r"シングル|singles?", re.I)

OUT = Path("docs/singles.json")
JST = timezone(timedelta(hours=9))
DC = "{http://purl.org/dc/elements/1.1/}"


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
        yield {
            "link": link,
            "title": (item.findtext("title") or "").strip(),
            "author": (item.findtext(f"{DC}creator") or "").strip(),
            "date": date,
            "summary": re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()[:200],
        }


def main():
    found, ok = {}, 0
    for tag in TAGS:
        try:
            for a in fetch_tag(tag):
                entry = found.setdefault(a["link"], {**a, "tags": set()})
                entry["tags"].add(tag)
            ok += 1
        except Exception as e:
            print(f"取得失敗 #{tag}: {e}", file=sys.stderr)
    if ok == 0:
        sys.exit("すべてのタグで取得に失敗したため、更新しません。")

    old = {}
    if OUT.exists():
        old = {a["link"]: a for a in json.loads(OUT.read_text("utf-8")).get("articles", [])}

    one_month_ago = (datetime.now(JST) - timedelta(days=30)).date()
    for a in found.values():
        text = " ".join([a["title"], a["summary"], *a["tags"]])
        # 「チャンピオンズ」または「構築記事」タグを含み、タイトル・本文に「シングル」を含む
        has_game = NEED_GAME.search(text) or "ポケモンチャンピオンズ構築記事" in a["tags"]
        has_singles = NEED_SINGLES.search(text)
        if has_game and has_singles and a["date"] >= str(one_month_ago):
            old[a["link"]] = {k: a[k] for k in ("link", "title", "author", "date")}

    articles = sorted(old.values(), key=lambda a: a["date"], reverse=True)[:3000]
    OUT.write_text(
        json.dumps({"updated": datetime.now(JST).isoformat(timespec="minutes"), "articles": articles},
                   ensure_ascii=False, indent=1),
        "utf-8",
    )
    print(f"{len(articles)}件")


if __name__ == "__main__":
    main()
