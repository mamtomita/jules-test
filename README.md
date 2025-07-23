# Google Cloud Log Exporter

これはGoogle Cloud Runへのデプロイを想定したFlaskアプリケーションです。指定された条件に基づいてGoogle Cloud LoggingからログをエクスポートするためのAPIエンドポイントを提供します。

## 主な機能

-   期間 (`start_time` と `end_time`) に基づくログのフィルタリング
-   1つまたは複数のログ名 (`log_names`) に基づくログのフィルタリング
-   出力形式を `json` または `text` で指定可能
-   Cloud Run上でサーバーレスコンテナとしてデプロイ可能

## ファイル構成

-   `main.py`: Flaskアプリケーションのメインファイル
-   `Dockerfile`: Dockerコンテナをビルドするための設定ファイル
-   `requirements.txt`: Pythonの依存ライブラリ

## Cloud Runへのデプロイ手順

1.  **前提条件:**
    -   ローカルマシンに [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) がインストールされ、認証が完了していること。
    -   Cloud RunとCloud Build APIが有効化されたGoogle Cloudプロジェクトがあること。

2.  **プロジェクトIDの設定:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```
    `YOUR_PROJECT_ID` を実際のGCPプロジェクトIDに置き換えてください。

3.  **Cloud Build を使用してコンテナイメージをビルド:**
    ```bash
    gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/log-exporter
    ```

4.  **Cloud Runへデプロイ:**
    ```bash
    gcloud run deploy log-exporter-service \\
        --image gcr.io/YOUR_PROJECT_ID/log-exporter \\
        --platform managed \\
        --region YOUR_REGION \\
        --allow-unauthenticated
    ```
    -   `YOUR_REGION` を希望のリージョン（例: `asia-northeast1`）に置き換えてください。
    -   **【重要】** `--allow-unauthenticated` フラグはサービスを公開します。本番環境では、IAMを使用した認証を検討してください。

5.  **サービスアカウントへの権限付与:**
    Cloud Runサービスがログを読み取るためには権限が必要です。

    まず、Cloud Runサービスが使用するサービスアカウントのメールアドレスを取得します。
    ```bash
    SERVICE_ACCOUNT=$(gcloud run services describe log-exporter-service --platform managed --region YOUR_REGION --format 'value(spec.template.spec.serviceAccountName)')
    ```

    次に、そのサービスアカウントに `Logging Viewer` ロールを付与します。
    ```bash
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\
        --member="serviceAccount:$SERVICE_ACCOUNT" \\
        --role="roles/logging.viewer"
    ```

## APIの使用方法

デプロイが完了すると、サービスのURLが表示されます。そのURLの `/logs` エンドポイントに対して、以下のクエリパラメータを付けてGETリクエストを送信します。

### エンドポイント

`/logs`

### クエリパラメータ

-   `project_id` ( **必須** ): ログを取得したいGCPプロジェクトID。
-   `start_time` (任意): 期間の開始時刻 (RFC3339 UTC "Zulu" 形式)。 例: `2025-07-23T00:00:00Z`
-   `end_time` (任意): 期間の終了時刻 (RFC3339 UTC "Zulu" 形式)。 例: `2025-07-23T23:59:59Z`
-   `log_names` (任意): フィルタリングしたいログ名をカンマ区切りで指定。
-   `format` (任意): 出力形式。`json` (デフォルト) または `text` を指定。

### リクエスト例

```
https://log-exporter-service-xxxxxxxx-an.a.run.app/logs?project_id=your-gcp-project&start_time=2025-07-23T00:00:00Z&end_time=2025-07-23T23:59:59Z&log_names=cloudaudit.googleapis.com%2Factivity,run.googleapis.com%2Fstdout&format=text
```
