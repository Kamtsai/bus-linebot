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

def background_task(user_id):
    try:
        bus_info = get_bus_arrival_times()
        info_list = bus_info.split('\n\n')
        
        cks_info = [info for info in info_list if '中正紀念堂' in info]
        xdal_info = [info for info in info_list if '信義大安路口' in info]
        
        cks_message = "中正紀念堂站資訊：\n" + '\n'.join(cks_info)
        xdal_message = "信義大安路口站資訊：\n" + '\n'.join(xdal_info)
        
        line_bot_api.push_message(user_id, TextSendMessage(text=cks_message))
        line_bot_api.push_message(user_id, TextSendMessage(text=xdal_message))
    except Exception as e:
        line_bot_api.push_message(user_id, TextSendMessage(text=f"抱歉，獲取公車資訊時發生錯誤：{str(e)}"))

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
    if event.message.text == "1":
        user_id = event.source.user_id
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="正在獲取公車資訊，請稍候...")
        )
        Thread(target=background_task, args=(user_id,)).start()
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入 '1' 來查詢公車到站時間。")
        )

if __name__ == "__main__":
    app.run()
