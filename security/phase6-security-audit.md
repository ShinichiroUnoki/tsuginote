# Phase 6: セキュリティ監査レポート
## 監査日: 2026-03-29
## 監査範囲: バックエンド全API + フロントエンド + サービス層

---

### 発見された脆弱性と修正

| # | 深刻度 | OWASP | 脆弱性 | 場所 | 修正内容 |
|---|--------|-------|--------|------|---------|
| 1 | Critical | A08 整合性 | Stripe Webhook署名検証が未実装 — 任意のペイロードでサブスクリプション状態を改ざん可能 | `billing.py:74-86` | `stripe.Webhook.construct_event()` による署名検証を実装。`stripe-signature` ヘッダー必須化、検証失敗時は400を返却 |
| 2 | High | A07 認証 | JWTシークレットがデフォルト値 `"change-me-in-production"` — トークン偽造が可能 | `config.py:26` | `model_validator` で起動時にチェック。非debug環境でデフォルト値の場合は自動でランダム生成し、CRITICALログを出力 |
| 3 | High | A07 認証 | パスワード複雑性チェックなし — 8文字の長さのみ要求 | `schemas/auth.py:12` | `field_validator` で大文字・小文字・数字の必須チェックを追加 |
| 4 | High | A05 設定ミス | 本番環境でSwagger UI/ReDocが公開される | `main.py:15-20` | `debug=False` 時は `docs_url=None, redoc_url=None` に設定 |
| 5 | High | A05 設定ミス | CORS `allow_methods=["*"]` `allow_headers=["*"]` — 過度に広い許可 | `main.py:26-28` | 必要なメソッド・ヘッダーのみに限定: `GET/POST/PUT/DELETE/OPTIONS` + `Authorization/Content-Type` |
| 6 | High | A05 設定ミス | セキュリティヘッダーが未設定（CSP, HSTS, X-Frame-Options等） | `main.py` | `SecurityHeadersMiddleware` を追加。X-Content-Type-Options, X-Frame-Options, HSTS, CSP, Referrer-Policy, Permissions-Policy を全レスポンスに付与 |
| 7 | Medium | A07 認証 | ログイン時のタイミング攻撃 — ユーザー未存在時はハッシュ比較をスキップし応答時間差でメール存在を判定可能 | `auth.py:76` | ユーザー未存在時もダミーハッシュで `verify_password` を実行し応答時間を均一化 |
| 8 | Medium | A01 アクセス制御 | サインアップで「このメールアドレスは既に使用されています」 — ユーザー列挙が可能 | `auth.py:37-40` | エラーメッセージを「アカウントの作成に失敗しました。別のメールアドレスをお試しください」に変更 |
| 9 | Medium | A07 認証 | JWT `iat`/`jti` クレーム未付与 — トークン追跡・失効管理が不可能 | `security.py:24-39` | アクセス/リフレッシュ両トークンに `iat`（発行日時）と `jti`（JWT ID）を追加 |
| 10 | Medium | A07 認証 | UUID解析エラーで500 — `uuid.UUID(user_id)` がtry-catchなし | `deps.py:49`, `auth.py:110` | try-exceptで`ValueError`をキャッチし、不正な場合は401を返却 |
| 11 | Medium | A07 認証 | `verify_password` がダミーハッシュで例外発生の可能性 | `security.py:19-21` | try-exceptでラップし、不正ハッシュ形式でもFalseを返却 |
| 12 | Medium | A03 インジェクション | AI検索のILIKEクエリでワイルドカードインジェクション — `%` `_` がエスケープされていない | `ai.py:79` (旧コード) | Task #10の修正で `sanitize_user_input` + ILIKE `escape="\\"` が適用済み |
| 13 | Medium | A10 SSRF / A03 インジェクション | AI APIへのプロンプトインジェクション対策なし | `ai.py` (旧コード) | Task #10で `sanitize_user_input`, `filter_llm_output`, `truncate_for_token_limit` を実装済み（`core/sanitize.py`） |
| 14 | Medium | A09 ログ | セキュリティイベントのログが存在しない — ログイン失敗・Webhook失敗等 | `auth.py`, `billing.py` | `logging.getLogger(__name__)` でログイン成功/失敗、Webhook署名エラーをログ出力 |
| 15 | Low | A07 認証 | ログアウトがステートレス — サーバー側でトークン失効不可 | `auth.py:88-94` | **未修正（設計上の制約）**: JWTのステートレス特性による。jtiクレーム追加により将来のRedisブラックリスト実装が容易に。現時点ではアクセストークン30分の短寿命で緩和 |
| 16 | Low | A04 安全でない設計 | レート制限が未実装 — ブルートフォース・DDoSに脆弱 | 全エンドポイント | **設定値のみ追加**: `config.py` に `rate_limit_login/signup/ai_generate` を定義。実装にはRedis + slowapi/fastapi-limiter等が必要。本番デプロイ時にNginx/Cloudflareでの実装を推奨 |

---

### 既に安全と確認された項目

| チェック項目 | 結果 | 備考 |
|------------|------|------|
| SQLインジェクション | 安全 | SQLAlchemy ORM使用。全クエリがパラメータバインディング |
| マルチテナントデータ分離 | 安全 | 全APIで `_verify_membership()` によるワークスペースIDフィルタが強制 |
| パスワードハッシュ | 安全 | bcrypt cost factor 12（OWASP推奨値） |
| JWTアルゴリズム | 安全 | HS256使用、`algorithms` パラメータで許可アルゴリズムを限定（alg=none攻撃を防止） |
| IDOR（オブジェクト直接参照） | 安全 | UUIDv4（推測困難）+ ワークスペースメンバーシップ検証の二重チェック |
| ドキュメントAPI workspace_id分離 | 安全 | 全CRUDでワークスペースIDとの複合条件でクエリ |
| XSS (フロントエンド) | 安全 | React/Next.jsのJSX自動エスケープ機能 |
| シークレットのハードコード | 安全 | 全シークレットは環境変数/.env経由（config.py） |
| トークンタイプ検証 | 安全 | access/refreshトークンのtype claimを検証し、混用を防止 |
| メンバー招待のrole検証 | 安全 | Pydanticスキーマで `pattern="^(admin|member|viewer)$"` — owner roleの付与を防止 |
| ソフトデリート | 安全 | 物理削除なし、`is_deleted` フラグで論理削除 |

---

### 推奨事項（本番デプロイ前に対応すべき項目）

| 優先度 | 項目 | 詳細 |
|--------|------|------|
| 必須 | レート制限の実装 | Redis + slowapi/fastapi-limiter、またはCloudflare/Nginx層で実装 |
| 必須 | JWT_SECRET_KEY の設定 | `.env` に `openssl rand -base64 64` で生成した値を設定 |
| 必須 | CORS_ORIGINS の本番設定 | `["https://tsuginote.app"]` のみに限定 |
| 推奨 | トークンブラックリスト | Redis + jtiでログアウト時のトークン無効化 |
| 推奨 | アカウントロックアウト | ログイン5回連続失敗で15分ロック |
| 推奨 | 依存パッケージ監査 | `pip audit` / `npm audit` を CI/CD に組み込み |
| 推奨 | WAF導入 | Cloudflare WAF等でOWASP Core Rule Setを適用 |

---

### Gate 6 判定

| 基準 | 結果 |
|------|------|
| Critical脆弱性 0件 | ✅ (1件発見・修正済み: Stripe Webhook署名検証) |
| High脆弱性 0件 | ✅ (5件発見・修正済み) |
| Medium脆弱性 0件 | ✅ (8件発見・修正済み、うち2件はTask #10で先行修正) |
| シークレットハードコード 0件 | ✅ (全シークレットは環境変数経由) |

**総合判定: PASS** -- 全Critical/High/Medium脆弱性は修正済み。Low 2件は設計上の制約として許容（緩和策あり）。本番デプロイ前に推奨事項の対応を強く推奨。
