from flask import Flask, Blueprint, request, jsonify
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from pypdf import PdfReader, PdfWriter
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents.models import QueryType
import logging
import requests
import os
import openai  # OpenAIパッケージのインポート
import urllib.parse
import re

# 環境変数から設定を取得
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")

openai.api_type = "azure"
openai.api_base = azure_endpoint
openai.api_version = "2023-05-01"
openai.api_key = api_key


service_name = os.getenv("AZURE_AI_SEARCH_SERVICE_NAME")
index_name = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")
api_version = "2020-06-30"
query_key = os.getenv("AZURE_AI_SEARCH_QUERY_KEY")
search_url = f"https://{service_name}.search.windows.net/indexes/{index_name}/docs/search?api-version={api_version}"


# ログ設定
logging.basicConfig(level=logging.DEBUG)

# Azure Cognitive Searchの設定
search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

search_client = SearchClient(endpoint=search_endpoint,
                             index_name=index_name,
                             credential=AzureKeyCredential(search_api_key))

# Blueprintの設定
aj_search_bp = Blueprint('aj_search_bp', __name__)

@aj_search_bp.route('/search_attendance', methods=['GET'])
def search_attendance():
    raw_query = request.args.get('q')

    headers = {
        "Content-Type": "application/json",
        "api-key": query_key
    }
    search_payload = {
        'search': raw_query,
        'select': 'content',
        'top': 10,  # 必要に応じて関連度の高い結果の数を調整
        'highlight': 'content'  # ハイライトを有効にする
    }
    # HTTP POSTリクエストを送信
    response = requests.post(search_url, headers=headers, json=search_payload)
    response.raise_for_status()
    
    reply = do_chatgpt(raw_query,extract_highlights(response.json()))
    logging.info(f"reply: {reply}")
    return jsonify(reply['choices'][0]['message']['content'])

def create_prompt(context, query):
    header = "What is Diploblastic and Triploblastic Organisation"
    return header + context + "\n\n" + query + "\n"

def preprocess_content(content):
    max_length = 1000
    return content[:max_length]

# ハイライト情報のみを抽出し、<em>タグを削除する関数
def extract_highlights(results):
    top_results = sorted(results['value'], key=lambda x: x['@search.score'], reverse=True)[:5]
    logging.info(f"top_results: {top_results}")
    
    highlights = []
    for doc in top_results:
        if '@search.highlights' in doc:
            for highlight in doc['@search.highlights']['content']:
                clean_text = re.sub(r'<.*?>', '', highlight)  # <em>タグを削除
                highlights.append(clean_text.replace("\n", "").replace("\r", ""))
    
    return "\n".join(highlights)

def do_chatgpt(raw_query,content):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": f"""あなたは会社の総務部門の優秀な社員です。
             社員からの問い合わせに社内ルールに照らし合わせて的確に簡潔に回答する必要があります。
             手続きが必要だと思われる問い合わせには社内規定にのっとって手続きを案内してください。"""},
            {"role": "user", "content": f"""{raw_query} 
             という問い合わせに対して以下の情報から回答を作成してください
             ---------------------------------------------
             {content}"""},
        ],
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")  # エラーメッセージを出力
        return None

# Flaskアプリケーションの設定
app = Flask(__name__)
app.register_blueprint(aj_search_bp)

if __name__ == '__main__':
    app.run(debug=True)
