# ポケチャン ダブルバトル note記事まとめ

noteのハッシュタグRSSから、ポケモンチャンピオンズのダブルバトル関連記事のリンクを毎日集めて一覧にします。
サーバー・APIキー・費用は不要です。

## 公開手順（GitHub、すべて無料）
1. GitHubで新しいリポジトリを作成し、このフォルダの中身をすべてアップロードする（`.github` フォルダも忘れずに）。
2. Settings → Pages → Source を「Deploy from a branch」、Branch を `main` / `/docs` にして保存。
3. Actions タブ → 「update」→ Run workflow で初回の取得を実行する。
4. 数分後、`https://ユーザー名.github.io/リポジトリ名/` で公開されます。以後、毎朝7時（日本時間）に自動更新されます。

## カスタマイズ
- 集めるタグ・絞り込み条件：`fetch.py` の先頭（TAGS / NEED_GAME / NEED_DOUBLES）
- 実行時刻：`.github/workflows/update.yml` の cron（UTC表記）
