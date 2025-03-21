import os
import openai
import logging
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, Mention

# 環境変数からLINE Botのアクセストークンとシークレットを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_USER_ID = os.getenv("LINE_BOT_USER_ID")  # BotのUser ID（Uから始まる）

# OpenAI APIキーを設定
openai.api_key = OPENAI_API_KEY

# Flaskアプリを作成
app = Flask(__name__)

# LINE Bot APIとWebhookHandlerをセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
        logging.error(f"❌ [ERROR] OpenAI API Request Failed: {e}")
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
        logging.error("❌ Invalid signature. Check your channel secret and access token.")
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

        # メンションがあるか確認
        mentioned_users = []
        if hasattr(event.message, "mention") and event.message.mention:
            mentioned_users = [m.user_id for m in event.message.mention.mentionees]

        # Botがメンションされたか確認
        if BOT_USER_ID not in mentioned_users:
            logging.debug("🚫 [DEBUG] Bot was not mentioned. Ignoring message.")
            return
        
        # メンション部分を削除
        for mention in event.message.mention.mentionees:
            user_message = user_message.replace(f"@{mention.user_id}", "").strip()

    # 翻訳を実行
    response_text = translate_message(user_message)
    logging.debug(f"📤 [DEBUG] Sent reply: {response_text}")

    # 返信を送信
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))

# サーバーを起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))