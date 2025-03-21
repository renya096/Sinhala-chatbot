import os
import json
import openai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 環境変数の読み込み
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# デバッグ用ログ
print(f"✅ [DEBUG] OpenAI API Key: {'Set' if OPENAI_API_KEY else 'Not Set'}")
print(f"✅ [DEBUG] LINE Access Token: {'Set' if LINE_CHANNEL_ACCESS_TOKEN else 'Not Set'}")
print(f"✅ [DEBUG] LINE Secret: {'Set' if LINE_CHANNEL_SECRET else 'Not Set'}")

# Flask アプリの作成
app = Flask(__name__)

# LINE Bot API の設定
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI のクライアント設定
openai.api_key = OPENAI_API_KEY

# LINE Webhook のエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    # LINE からのリクエストを取得
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print(f"📥 [DEBUG] Received request: {body}")  # 受信リクエストを表示

    # WebhookHandler に処理を渡す
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ [ERROR] Invalid Signature")
        abort(400)

    return 'OK'

# メッセージイベントのハンドリング
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    print(f"📥 [DEBUG] User Message: {user_message}")

    # OpenAI に翻訳リクエストを送る
    translated_text = get_openai_response(user_message)

    # LINE に返信
    if translated_text:
        reply_message = TextSendMessage(text=translated_text)
        line_bot_api.reply_message(event.reply_token, reply_message)
        print(f"📤 [DEBUG] Sent reply: {translated_text}")
    else:
        print("❌ [ERROR] No response from OpenAI")

# OpenAI API を呼び出す関数
def get_openai_response(user_message):
    try:
        print(f"📤 [DEBUG] Sending request to OpenAI: {user_message}")

        response = openai.ChatCompletion.create(
            model="gpt-4o",  # 必要に応じて `gpt-3.5-turbo` などに変更
            messages=[{"role": "user", "content": user_message}]
        )

        openai_reply = response["choices"][0]["message"]["content"]
        print(f"✅ [DEBUG] OpenAI Response: {openai_reply}")
        return openai_reply

    except Exception as e:
        print(f"❌ [ERROR] OpenAI API Request Failed: {e}")
        return "エラーが発生しました。"

# Flask アプリの起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)