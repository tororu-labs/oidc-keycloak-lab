# iam-lab-study

IAM、OIDC、OAuth 2.0、Keycloak、BFF / Backend API 構成を手を動かしながら学ぶための個人用ラボリポジトリです。

## 現在の進捗

- `docs/01` から `docs/08` までの最小ハンズオンを完了済み
- Keycloak の GUI 設定、FastAPI による OIDC ログイン、BFF / Backend API 分離まで確認済み
- token 検証・異常系（docs/07）と audience 検証（docs/08）まで実装済み
- `docs/Reference/` を作成し、起動手順、構成整理、トラブルシューティングを切り出し済み
- Next.js 連携は未着手

## 読み進め方

- まず `docs/01` から `docs/08` を順に読む
- 詳しい背景や共通手順は `docs/Reference/` を参照する
- 試行錯誤や途中整理は `notes/` に残し、再利用価値が高いものは後で `docs/Reference/` へ移す

## ディレクトリ

- `docs/`: 順番に進める Setup と、整理済みの Reference を置く
- `notes/`: 学習途中の記録、比較、仮説、調査メモを置く
- `apps/`: 検証用アプリを置く
- `infra/`: Keycloak などの起動構成を置く
- `scripts/`: 補助スクリプトを置く
- `scratch/`: 一時メモや作業用ファイルを置く

## 次のテーマ

- `docs/Reference/01_LocalStartup.md` から `04_ClientAndTokenRoles.md` の育成
- `docs/05` と `docs/06` の軽量化と Reference への寄せ直し
- Next.js を使った SPA / BFF 構成への拡張

## 参照用ドキュメント

- [00_Glossary.md](docs/Reference/00_Glossary.md)
- [01_LocalStartup.md](docs/Reference/01_LocalStartup.md)
- [02_AuthFlowArchitecture.md](docs/Reference/02_AuthFlowArchitecture.md)
- [03_Troubleshooting.md](docs/Reference/03_Troubleshooting.md)
- [04_ClientAndTokenRoles.md](docs/Reference/04_ClientAndTokenRoles.md)
