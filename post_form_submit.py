from flask import Flask, Blueprint, request, jsonify
import os
import requests
import json
from get_email import get_email_info

form_submit_bp = Blueprint('form_submit_bp', __name__)
# APIキーやトークンなどの設定
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

@form_submit_bp.route('/form_submit', methods=['POST'])
def form_submit():
    form_data = request.json
    employee_name = form_data['name']
                    
    employee_response  = get_email_info(employee_name.replace(" ", ""))

    if employee_response.status_code != 200:
        return jsonify({"error": "Failed to retrieve employee data"}), 500
    # バイト列を辞書に変換
    employee_data = json.loads(employee_response.data.decode('utf-8'))
    print(employee_data)
    # employee_data['TotalOvertimeHours']の結果がnoneの場合、空文字を代入
    if not employee_data['TotalOvertimeHours']:
        employee_data['TotalOvertimeHours'] = ""

    formatted_response = format_response(form_data, employee_data['TotalOvertimeHours'])
    json_response = do_chatgpt(formatted_response)

    if not json_response:
        return jsonify({"error": "Failed to get response from ChatGPT"}), 500

    # 成功したレスポンスの処理
    try:
        data = json.loads(json_response['choices'][0]['message']['function_call']['arguments'])
        post_message_to_slack(data, form_data, employee_data)
        # 以下の値のみ返す
        returnValue = {
            "全体的な感情評価": data["全体的な感情評価"],
            "エンゲージメント": data["エンゲージメント"],
            "満足度": data["満足度"],
            "励み": data["励み"],
            "自己効力感": data["自己効力感"],
            "ストレスと圧力": data["ストレスと圧力"],
            "所属感": data["所属感"],
            "社会的支援": data["社会的支援"],
            "成長と発展": data["成長と発展"],
            "総評": data["総評"]}
        return jsonify(returnValue), 200
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return jsonify({"error": "Invalid JSON content received from ChatGPT"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def do_chatgpt(content):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": content},
        ],
        "functions": [
            {
                "name": "generate_json",
                "description": "Generate JSON response based on provided content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "全体的な感情評価": {"type": "number"},
                        "エンゲージメント": {"type": "number"},
                        "満足度": {"type": "number"},
                        "励み": {"type": "number"},
                        "自己効力感": {"type": "number"},
                        "ストレスと圧力": {"type": "number"},
                        "所属感": {"type": "number"},
                        "社会的支援": {"type": "number"},
                        "成長と発展": {"type": "number"},
                        "総評": {"type": "string"}
                    },
                    "required": ["全体的な感情評価", "エンゲージメント", "満足度", "励み", "自己効力感", "ストレスと圧力", "所属感", "社会的支援", "成長と発展", "総評"]
                }
            }
        ],
        "function_call": {"name": "generate_json"}
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")  # エラーメッセージを出力
        return None

def format_response(form_data, total_overtime_hours):
    response = f"""
今月担当した主な業務と取り組み内容：{form_data.get('task', '')}
今月自身の評価できること：{form_data.get('self_assessment', '')}
翌月以降、改善したいこと：{form_data.get('improvements', '')}
他のメンバーの働きで評価したいこと：{form_data.get('team_evaluation', '未記入')}
自己研鑽していること：{form_data.get('self_development', '未記入')}
自分の業務遂行(1~10で評価)：{form_data.get('performance', '')}
自身の成長(1~10で評価)：{form_data.get('growth', '')}
作業のやりがい(1~10で評価)：{form_data.get('satisfaction', '')}
周囲の人とのコミュニケーションの取りやすさ(1~10で評価)：{form_data.get('communication', '')}
今月の残業時間については{total_overtime_hours}時間です

以下の指標を1.0から10.0のスケールで評価してください
エンゲージメント
満足度
励み
自己効力感
ストレスと圧力
所属感
社会的支援
成長と発展
総評は簡潔にテキストで記載してください。
"""
    return response

def post_message_to_slack(data, form_data, employee_data):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    text = f"""
今月の{form_data['name']}さんは以下の通りです
◆AIの評価：
  {data["総評"]}
◆今月担当した主な業務と取り組み内容：
  {form_data.get('task', '')}
◆今月自身の評価できること：
  {form_data.get('self_assessment', '')}
◆翌月以降、改善したいこと：
  {form_data.get('improvements', '')}
◆他のメンバーの働きで評価したいこと：
  {form_data.get('team_evaluation', '未記入')}
◆自己研鑽していること：
  {form_data.get('self_development', '未記入')}
◆業務遂行能力としての自己評価(1~10)：
  {form_data.get('performance', '')}
◆自身の成長(1~10)：
  {form_data.get('growth', '')}
◆作業のやりがい(1~10)：
  {form_data.get('satisfaction', '')}
◆周囲の人とのコミュニケーションのとりやすさ(1~10)：
  {form_data.get('communication', '')}
◆今月の残業時間：
  {employee_data['TotalOvertimeHours']}h
"""
    # enokitee_dataにEmailが含まれていない場合
    if not employee_data['Email']:
        payload = {
        "channel": SLACK_CHANNEL,
        "text": text
    }
    else:
        email = employee_data["Email"]
        payload = {
            "channel": SLACK_CHANNEL,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "メールを送信"
                            },
                            "url": f"mailto:{email}?subject=月次報告の入力ありがとうございました。&body={text}"  # メーラーを起動するリンク
                        }
                    ]
                }
            ]
        }

    # リクエスト送信
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # レスポンスをJSONデコード
    if response.text:
        try:
            response_data = response.json()
            print(f"Slack API response JSON: {response_data}")
            return response_data
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            return None
    else:
        print("Slack API returned an empty response.")
        return None


if __name__ == '__main__':
    app.run(debug=True)
