from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from bus_scraper import get_bus_arrival_times
from threading import Thread

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

def background_task(reply_token):
    try:
        bus_info = get_bus_arrival_times()
        line_bot_api.reply_message(reply_token, TextSendMessage(text=bus_info))
    except Exception as e:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"抱歉，獲取公車資訊時發生錯誤：{str(e)}"))

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
    if event.message.text == "公車資訊":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="正在獲取公車資訊，請稍候...")
        )
        Thread(target=background_task, args=(event.reply_token,)).start()
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入 '公車資訊' 來查詢公車到站時間。")
        )

if __name__ == "__main__":
    app.run()
