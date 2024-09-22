from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from bus_scraper import get_bus_arrival_times

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

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
    user_message = event.message.text.strip()
    if user_message == "1":
        try:
            bus_info = get_bus_arrival_times("1")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=bus_info)
            )
        except Exception as e:
            error_message = f"抱歉，獲取公車資訊時發生錯誤：{str(e)}"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=error_message)
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入 '1' 來查詢中正紀念堂公車資訊。")
        )

if __name__ == "__main__":
    app.run()
