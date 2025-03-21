from flask import Flask, request, abort
import os
import openai
from linebot.v3.messaging import MessagingApi, TextMessage
from linebot.v3.webhook import WebhookHandler, MessageEvent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# OpenAI APIキーを設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# LINE Bot API 設定
line_bot_api = MessagingApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    print("📥 [DEBUG] Received request:", body)  # 🔍 受信したリクエストをログ出力

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ [ERROR] Invalid Signature Error")  # 🔍 エラー出力
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    print("📩 [DEBUG] Received message:", user_message)  # 🔍 受信メッセージをログ出力

    # メッセージが「翻訳：」で始まる場合 → 日本語をシンハラ語に翻訳
    if user_message.startswith("翻訳："):
        original_text = user_message.replace("翻訳：", "").strip()
        print("🔄 [DEBUG] Translating:", original_text)  # 🔍 翻訳するテキストをログ出力

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "日本語をシンハラ語に翻訳してください。"},
                    {"role": "user", "content": original_text}
                ],
                temperature=0.2,
            )

            reply = response.choices[0].message.content.strip()
            print("✅ [DEBUG] Translation response:", reply)  # 🔍 翻訳結果をログ出力

        except Exception as e:
            print("❌ [ERROR] OpenAI Translation Error:", str(e))  # 🔍 エラーログ
            reply = "翻訳中にエラーが発生しました。"

    # それ以外のメッセージ → シンハラ語で返信
    else:
        print("🗣️ [DEBUG] AI response request for:", user_message)  # 🔍 AI応答リクエスト

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "シンハラ語で答えてください。"},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
            )

            reply = response.choices[0].message.content.strip()
            print("✅ [DEBUG] AI response:", reply)  # 🔍 AIの応答をログ出力

        except Exception as e:
            print("❌ [ERROR] OpenAI Chat Error:", str(e))  # 🔍 エラーログ
            reply = "エラーが発生しました。"

    # LINE に返信を送信
    try:
        line_bot_api.reply_message(
            event.reply_token,
            [TextMessage(text=reply)]
        )
        print("📤 [DEBUG] Reply sent successfully!")  # 🔍 返信成功のログ
    except Exception as e:
        print("❌ [ERROR] LINE Reply Error:", str(e))  # 🔍 LINE返信エラー

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))