"""noteのハッシュタグRSSとキーワード検索から、ポケモンチャンピオンズのシングルバトル関連記事を集める。"""
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from common import (
    load_author_cache,
    save_author_cache,
    fetch_author_name,
    fetch_tag,
    fetch_keyword,
    JST,
)

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




def main():
    author_cache = load_author_cache(AUTHOR_CACHE_FILE)

    found, ok = {}, 0
    for tag in TAGS:
        try:
            for a in fetch_tag(tag):
                entry = found.setdefault(a["link"], {**a, "tags": set()})
                entry["tags"].add(tag)
            ok += 1
        except Exception as e:
            print(f"取得失敗 #{tag}: {e}", file=sys.stderr)

    # キーワード検索でタグなし記事も取得（2ヶ月分を確保するため15ページまで取得）
    for keyword in SEARCH_KEYWORDS:
        try:
            for a in fetch_keyword(keyword, pages=15):
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

    save_author_cache(author_cache, AUTHOR_CACHE_FILE)

    old = {}
    if OUT.exists():
        old = {a["link"]: a for a in json.loads(OUT.read_text("utf-8")).get("articles", [])}

    # 前日以降の記事を取得（自動実行は毎日朝7時）
    yesterday = (datetime.now(JST) - timedelta(days=1)).date()
    for a in found.values():
        text = " ".join([a["title"], a["summary"], *a["tags"]])
        # 「チャンピオンズ」または「構築記事」タグを含み、タイトル・本文に「シングル」を含む
        has_game = NEED_GAME.search(text) or "ポケモンチャンピオンズ構築記事" in a["tags"]
        has_singles = NEED_SINGLES.search(text)
        if has_game and has_singles and a["date"] >= str(yesterday):
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
