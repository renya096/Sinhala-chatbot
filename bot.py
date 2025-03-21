import os
import openai
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Flask アプリのセットアップ
app = Flask(__name__)

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI API クライアントの設定
client = openai.Client(api_key=OPENAI_API_KEY)

# LINE Bot のセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 翻訳ロジック
def translate_text(user_text):
    """
    日本語ならシンハラ語へ翻訳
    シンハラ語なら日本語へ翻訳
    """
    prompt = f"""
    あなたは翻訳AIです。
    **日本語ならシンハラ語に翻訳** し、**シンハラ語なら日本語に翻訳** してください。

    入力: {user_text}
    翻訳:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "あなたは翻訳AIです。"},
                      {"role": "user", "content": prompt}]
        )
        translated_text = response.choices[0].message.content.strip()
        return translated_text
    except Exception as e:
        print(f"[ERROR] OpenAI API Request Failed: {e}")
        return "翻訳に失敗しました。"

# LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

# LINE メッセージイベントのハンドラー
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    sender_type = event.source.type  # user, group, room のどれか
    group_id = event.source.group_id if sender_type == "group" else None

    print(f"📥 [DEBUG] User Message: {user_text} (from {sender_type})")

    # ボットがメンションされたときのみ反応（グループ対応）
    if sender_type == "group" and f"@{bot_display_name}" not in user_text:
        print("📤 [DEBUG] Ignored message (not mentioned)")
        return  # グループチャットでは、ボットがメンションされたときのみ反応

    translated_text = translate_text(user_text)

    # 返信メッセージを送信
    reply_message = TextSendMessage(text=translated_text)
    line_bot_api.reply_message(event.reply_token, reply_message)
    print(f"📤 [DEBUG] Sent reply: {translated_text}")

# アプリの起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)