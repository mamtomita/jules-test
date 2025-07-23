# Google Cloud Log Exporter

This is a Flask application designed to be deployed on Google Cloud Run. It provides an API endpoint to export logs from Google Cloud Logging based on specified criteria.

## Features

-   Filter logs by a time range (`start_time` and `end_time`).
-   Filter logs by one or more log names (`log_names`).
-   Specify the output format as either `json` or `text`.
-   Deployable as a serverless container on Cloud Run.

## Files

-   `main.py`: The main Flask application file.
-   `Dockerfile`: Configuration file to build the Docker container.
-   `requirements.txt`: Python dependencies.

## Deployment to Cloud Run

1.  **Prerequisites:**
    -   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated.
    -   A Google Cloud Project with the Cloud Run and Cloud Build APIs enabled.

2.  **Set your Project ID:**
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```
    Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

3.  **Build the container image using Cloud Build:**
    ```bash
    gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/log-exporter
    ```

4.  **Deploy to Cloud Run:**
    ```bash
    gcloud run deploy log-exporter-service \\
        --image gcr.io/YOUR_PROJECT_ID/log-exporter \\
        --platform managed \\
        --region YOUR_REGION \\
        --allow-unauthenticated
    ```
    -   Replace `YOUR_REGION` with your desired region (e.g., `asia-northeast1`).
    -   **Note:** `--allow-unauthenticated` makes the service publicly accessible. For production, consider using IAM-based authentication.

5.  **Grant Permissions to the Service Account:**
    The Cloud Run service needs permission to read logs.

    First, get the email of the service account used by your Cloud Run service:
    ```bash
    SERVICE_ACCOUNT=$(gcloud run services describe log-exporter-service --platform managed --region YOUR_REGION --format 'value(spec.template.spec.serviceAccountName)')
    ```

    Then, grant the `Logging Viewer` role to that service account:
    ```bash
    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\
        --member="serviceAccount:$SERVICE_ACCOUNT" \\
        --role="roles/logging.viewer"
    ```

## API Usage

Once deployed, you can access the service via its URL. Send a GET request to the `/logs` endpoint with the following query parameters.

### Endpoint

`/logs`

### Query Parameters

-   `project_id` ( **required** ): Your Google Cloud Project ID.
-   `start_time` (optional): The start of the time range in RFC3339 UTC "Zulu" format. Example: `2025-07-23T00:00:00Z`
-   `end_time` (optional): The end of the time range in RFC3339 UTC "Zulu" format. Example: `2025-07-23T23:59:59Z`
-   `log_names` (optional): A comma-separated list of log names to filter by.
-   `format` (optional): The output format. Can be `json` (default) or `text`.

### Example Request

```
https://log-exporter-service-xxxxxxxx-an.a.run.app/logs?project_id=your-gcp-project&start_time=2025-07-23T00:00:00Z&end_time=2025-07-23T23:59:59Z&log_names=cloudaudit.googleapis.com%2Factivity,run.googleapis.com%2Fstdout&format=text
```
