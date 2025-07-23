import subprocess
from flask import Flask, request, jsonify
import json
import shlex
import os
from datetime import datetime
import pytz

app = Flask(__name__)

def convert_jst_to_utc_rfc3339(jst_time_str):
    """
    JST文字列をUTCのRFC3339形式に変換
    """
    if not jst_time_str:
        return None
    try:
        jst = pytz.timezone('Asia/Tokyo')
        # JSTとして解釈
        dt_jst = jst.localize(datetime.strptime(jst_time_str, "%Y/%m/%d %H:%M:%S"))
        # UTCに変換
        dt_utc = dt_jst.astimezone(pytz.utc)
        return dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, TypeError):
        # 不正なフォーマットの場合はNoneを返す
        return None

def get_logs(start_time, end_time, log_names, output_format, project_id):
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
    utc_start_time = convert_jst_to_utc_rfc3339(start_time)
    utc_end_time = convert_jst_to_utc_rfc3339(end_time)

    if utc_start_time:
        filters.append(f"timestamp >= '{utc_start_time}'")
    if utc_end_time:
        filters.append(f"timestamp <= '{utc_end_time}'")

    if log_names:
        log_name_filters = [f'logName:"{name}"' for name in log_names]
        filters.append(f"({' OR '.join(log_name_filters)})")

    cmd = base_cmd + [ " AND ".join(filters) ]

    if project_id:
        cmd.extend(["--project", project_id])

    if output_format == "text":
        cmd.append("--format=value(timestamp,textPayload)")
    else:
        cmd.append("--format=json")

    try:
        safe_cmd = [shlex.quote(c) for c in cmd]
        result = subprocess.run(' '.join(safe_cmd), capture_output=True, text=True, check=True, shell=True)
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        return None, f"Command failed with error: {e.stderr}"
    except Exception as e:
        return None, str(e)


@app.route('/logs', methods=['GET'])
def logs():
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({"error": "project_id is a required parameter."}), 400

    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    log_names_str = request.args.get('log_names', "")
    output_format = request.args.get('format', 'json')

    log_names = log_names_str.split(',') if log_names_str else []

    logs_data, error = get_logs(start_time, end_time, log_names, output_format, project_id)

    if error:
        return jsonify({"error": error}), 500

    if output_format == "text":
        return logs_data, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    else:
        try:
            log_entries = [json.loads(line) for line in logs_data.strip().split('\\n') if line]
            return jsonify(log_entries), 200
        except json.JSONDecodeError:
            try:
                return jsonify(json.loads(logs_data)), 200
            except json.JSONDecodeError:
                return jsonify({"error": "Failed to decode logs as JSON", "raw_output": logs_data}), 500
        except Exception as e:
            return jsonify({"error": str(e), "raw_output": logs_data}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
