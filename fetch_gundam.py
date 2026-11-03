"""noteのハッシュタグRSSとキーワード検索から、ガンダムカードゲーム関連記事を集める。"""
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import config
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
    "ガンダムカードゲーム",
    "ガンダムカード",
    "GCG",
    "ガンダム",
]
# キーワード検索で集める（タグなし記事も対象）
SEARCH_KEYWORDS = ["ガンダムカードゲーム", "GCG", "#ガンダムカードゲーム"]
# 記事のタイトル・冒頭・タグに、ガンダムカードゲームが含まれるか。
NEED_GAME = re.compile(r"ガンダムカードゲーム|G-TCG|GTCG|ガンダムカード|GCG", re.I)

OUT = Path(f"{config.CACHE_DIR}/gundam.json")
AUTHOR_CACHE_FILE = Path(config.AUTHOR_CACHE_FILE)


def main():
    # 手動実行判定：--full フラグが指定されている場合
    is_manual = "--full" in sys.argv
    fetch_pages = 20 if is_manual else 15

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

    # キーワード検索でタグなし記事も取得（手動実行は1ヶ月分、自動実行は2ヶ月分を確保するため15ページまで取得）
    for keyword in SEARCH_KEYWORDS:
        try:
            for a in fetch_keyword(keyword, pages=fetch_pages, fetch_body=True):
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

    # 記事の日付範囲を決定（手動実行は1週間、自動実行は2日前から）
    days_back = 7 if is_manual else 2
    threshold = (datetime.now(JST) - timedelta(days=days_back)).date()
    for a in found.values():
        title_and_body = " ".join([a["title"], a.get("body", "")])
        # タイトルと本文に、ガンダムカードゲーム関連の表記が含まれているかチェック
        has_game = NEED_GAME.search(title_and_body) is not None
        if has_game and a["date"] >= str(threshold):
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
