import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_logs(start_time, end_time, log_names, output_format):
    """
    gcloud logging readコマンドを実行してログを取得する
    """
    base_cmd = [
        "gcloud",
        "logging",
        "read",
    ]

    # フィルタの構築
    filters = []
    if start_time:
        filters.append(f"timestamp >= '{start_time}'")
    if end_time:
        filters.append(f"timestamp <= '{end_time}'")

    if log_names:
        log_name_filters = [f'logName:"{name}"' for name in log_names]
        filters.append(f"({' OR '.join(log_name_filters)})")

    # gcloudコマンドの組み立て
    cmd = base_cmd + [ " AND ".join(filters) ]

    # 出力フォーマットの指定
    if output_format == "text":
        cmd.append("--format=value(timestamp,textPayload)")
    else: # default to json
        cmd.append("--format=json")

    # コマンドの実行
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        return None, e.stderr

@app.route('/logs', methods=['GET'])
def logs():
    """
    Webリクエストを受け取り、ログを返す
    """
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    log_names_str = request.args.get('log_names', "")
    output_format = request.args.get('format', 'json')

    log_names = log_names_str.split(',') if log_names_str else []

    logs, error = get_logs(start_time, end_time, log_names, output_format)

    if error:
        return jsonify({"error": error}), 500

    if output_format == "text":
        return logs, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    else:
        # JSON文字列をPythonのリストに変換して返す
        import json
        try:
            return jsonify(json.loads(logs)), 200
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to decode logs as JSON", "raw_output": logs}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
