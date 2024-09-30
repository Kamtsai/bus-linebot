import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from threading import Thread
from datetime import datetime

# 添加這行來確保 bus_scraper.py 可以被正確導入
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bus_scraper import get_bus_arrival_times

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

def background_task(user_id):
    try:
        logger.debug("開始執行背景任務")
        cks_info, xdal_info = get_bus_arrival_times()
        
        line_bot_api.push_message(user_id, TextSendMessage(text=cks_info.strip()))
        line_bot_api.push_message(user_id, TextSendMessage(text=xdal_info.strip()))
        
        logger.debug(f"已發送中正紀念堂信息和信義大安路口信息")
        
    except Exception as e:
        error_message = f"抱歉，獲取公車資訊時發生錯誤：{str(e)}"
        line_bot_api.push_message(user_id, TextSendMessage(text=error_message))
        logger.exception(f"背景任務執行錯誤: {str(e)}")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.debug(f"Received callback: {body}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    logger.debug(f"Received message: {event.message.text}")
    if event.message.text == "1":
        user_id = event.source.user_id
        logger.debug(f"User {user_id} requested bus information")
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
