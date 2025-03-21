import os
import openai
import logging
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 環境変数からLINE Botのアクセストークンとシークレットを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI APIキーを設定
openai.api_key = OPENAI_API_KEY

# Flaskアプリを作成
app = Flask(__name__)

# LINE Bot APIとWebhookHandlerをセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Botの表示名（メンション用）
BOT_DISPLAY_NAME = "@翻訳Bot GoodFlowMarket"  # ← Botの名前をここに設定 (LINE公式アカウントでの表示名)

# ログ設定
logging.basicConfig(level=logging.DEBUG)

# 翻訳関数
def translate_message(text):
    """ 日本語をシンハラ語へ、シンハラ語を日本語へ翻訳する関数 """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Translate Japanese to Sinhala and Sinhala to Japanese automatically."},
                {"role": "user", "content": text}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"OpenAI API Request Failed: {e}")
        return "翻訳に失敗しました"

# Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    """ LINEのWebhookエンドポイント """
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    logging.debug(f"📥 [DEBUG] Received request: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("Invalid signature. Check your channel secret and access token.")
        return jsonify({"status": "error"}), 400

    return jsonify({"status": "ok"}), 200

# LINEのメッセージイベントを処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ メッセージイベントを処理する """
    user_message = event.message.text
    source_type = event.source.type

    # グループメッセージの場合
    if source_type == "group":
        logging.debug(f"📥 [DEBUG] User Message: {user_message} (from group)")
        
        # Botへのメンションが含まれているかチェック
        if f"@{BOT_DISPLAY_NAME}" in user_message:
            # メンション部分を削除
            user_message = user_message.replace(f"@{BOT_DISPLAY_NAME}", "").strip()
        else:
            # メンションがなければ何もしない
            return

    # 翻訳を実行
    response_text = translate_message(user_message)
    logging.debug(f"📤 [DEBUG] Sent reply: {response_text}")

    # 返信を送信
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))

# サーバーを起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
