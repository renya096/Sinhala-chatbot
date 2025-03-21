from flask import Flask, request, abort
import os
from openai import OpenAI
from linebot.v3.messaging import MessagingApi, TextMessage
from linebot.v3.webhook import WebhookHandler, MessageEvent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# OpenAI APIクライアント作成
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# LINE Bot API 設定
line_bot_api = MessagingApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # メッセージが「翻訳：」で始まる場合 → 日本語をシンハラ語に翻訳
    if user_message.startswith("翻訳："):
        original_text = user_message.replace("翻訳：", "").strip()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "日本語をシンハラ語に翻訳してください。"},
                {"role": "user", "content": original_text}
            ],
            temperature=0.2,
        )

        reply = response.choices[0].message.content.strip()

    # それ以外のメッセージ → シンハラ語で返信
    else:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "シンハラ語で答えてください。"},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
        )

        reply = response.choices[0].message.content.strip()

    # LINE に返信を送信
    line_bot_api.reply_message(
        event.reply_token,
        [TextMessage(text=reply)]
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))