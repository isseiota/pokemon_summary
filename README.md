# カードゲーム note記事まとめ

noteのハッシュタグRSSとキーワード検索から、ポケモンチャンピオンズとガンダムカードゲームの関連記事のリンクを毎日集めて一覧にします。
サーバー・APIキー・費用は不要です。

## 公開手順（GitHub、すべて無料）
1. GitHubで新しいリポジトリを作成し、このフォルダの中身をすべてアップロードする（`.github` フォルダも忘れずに）。
2. Settings → Pages → Source を「Deploy from a branch」、Branch を `main` / `/docs` にして保存。
3. Actions タブ → 「update」→ Run workflow で初回の取得を実行する。
4. 数分後、`https://ユーザー名.github.io/リポジトリ名/` で公開されます。以後、毎朝 6:00（日本時間）に自動更新されます。

## カスタマイズ

### 取得する記事の設定

#### ポケモン記事（`fetch_singles.py` / `fetch_doubles.py`）
- `TAGS`: ハッシュタグから取得する記事
- `SEARCH_KEYWORDS`: キーワード検索で取得する記事（タグなし記事も対象）
- `NEED_GAME` / `NEED_SINGLES` / `NEED_DOUBLES`: フィルタリング条件

#### ガンダムカードゲーム記事（`fetch_gundam.py`）
- `TAGS`: ハッシュタグから取得する記事
- `SEARCH_KEYWORDS`: キーワード検索で取得する記事
- `NEED_GAME`: フィルタリング条件

### 実行環境の設定

#### 実行時刻の変更
`.github/workflows/update.yml` の `cron` 設定を編集（UTC表記）

```yaml
schedule:
  - cron: "0 21 * * *"  # UTC 21:00 = JST 6:00
```

#### Python バージョンの指定
`.python-version` ファイルで管理

```
3.12
```

### 環境変数での動作調整

#### ローカル実行時の設定例

```bash
# ログレベルを DEBUG に設定
LOG_LEVEL=DEBUG python fetch_singles.py

# ページ取得数を変更（デフォルト: 自動 15、手動 20）
NOTE_PAGES_AUTO=10 python fetch_singles.py

# タイムアウト時間を変更（秒単位、デフォルト: 30）
NOTE_TIMEOUT_RSS=60 python fetch_singles.py

# キャッシュの有効期限を変更（日数、デフォルト: 30）
NOTE_CACHE_EXPIRE_DAYS=7 python fetch_singles.py

# ページング遅延を変更（秒単位、デフォルト: 2.5）
NOTE_PAGINATING_DELAY=3.0 python fetch_singles.py
```

#### 手動実行時の詳細取得（ガンダムカードゲーム）

```bash
python fetch_gundam.py --full
# 通常の 20 ページから 15 ページ（2 ヶ月分）を 20 ページ（1 ヶ月分）に増加
# 日付範囲が 2 日前から 7 日前に変更
```

## ログ出力の確認

### ローカル実行時のログレベル

```bash
# INFO（デフォルト）
LOG_LEVEL=INFO python fetch_singles.py

# DEBUG（詳細ログ）
LOG_LEVEL=DEBUG python fetch_singles.py

# WARNING（警告以上のみ）
LOG_LEVEL=WARNING python fetch_singles.py
```

### GitHub Actions での実行ログ確認

1. GitHub リポジトリの「Actions」タブを開く
2. 「update」ワークフローをクリック
3. 最新の実行結果を確認
4. 「Run fetch_singles」などのステップを展開してログを確認

## テストの実行

設定値の検証とユニットテストを実行

```bash
python -m pytest test_config.py -v
# または
python -m unittest test_config.py
```

## トラブルシューティング

### スクリプトがエラーで停止する

- ログレベルを DEBUG に変更して詳細を確認
  ```bash
  LOG_LEVEL=DEBUG python fetch_singles.py
  ```

- タイムアウト値を増加
  ```bash
  NOTE_TIMEOUT_PAGE=20 python fetch_singles.py
  ```

### キャッシュが古い情報のまま

- キャッシュファイル（`docs/.author_cache.json`）を削除
  ```bash
  rm docs/.author_cache.json
  ```

- キャッシュの有効期限を短縮
  ```bash
  NOTE_CACHE_EXPIRE_DAYS=1 python fetch_singles.py
  ```

### GitHub Actions が実行されない

1. ワークフローが有効か確認（`.github/workflows/update.yml`）
2. Actions → 「update」で手動実行を試す
3. Settings → Actions → General で権限設定を確認

## 技術詳細

- **言語**: Python 3.12
- **主要ライブラリ**: urllib, xml.etree
- **キャッシュ**: JSON ファイル（著者名キャッシュ）
- **自動実行**: GitHub Actions（毎日 UTC 21:00）
- **エラーハンドリング**: リトライ機能付き（最大 2 回）
- **レート制限対策**: User-Agent ローテーション、遅延機能
