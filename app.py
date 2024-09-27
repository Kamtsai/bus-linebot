from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import logging
from bus_scraper import get_bus_arrival_times
from threading import Thread

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

def background_task(user_id):
    try:
        logger.debug("開始執行背景任務")
        bus_info = get_bus_arrival_times()
        logger.debug(f"獲取到的公車信息:\n{bus_info}")
        
        info_list = bus_info.split('\n\n')
        
        cks_info = "\n".join([info for info in info_list if '中正紀念堂' in info])
        xdal_info = "\n".join([info for info in info_list if '信義大安路口' in info])
        
        logger.debug(f"中正紀念堂信息:\n{cks_info}")
        logger.debug(f"信義大安路口信息:\n{xdal_info}")
        
        if cks_info:
            cks_message = "中正紀念堂站資訊（返程）：\n" + cks_info
            line_bot_api.push_message(user_id, TextSendMessage(text=cks_message))
            logger.debug(f"已發送中正紀念堂信息")
        else:
            line_bot_api.push_message(user_id, TextSendMessage(text="未找到中正紀念堂站資訊"))
            logger.debug("未找到中正紀念堂站資訊")
        
        if xdal_info:
            xdal_message = "信義大安路口站資訊（去程）：\n" + xdal_info
            line_bot_api.push_message(user_id, TextSendMessage(text=xdal_message))
            logger.debug(f"已發送信義大安路口信息")
        else:
            line_bot_api.push_message(user_id, TextSendMessage(text="未找到信義大安路口站資訊"))
            logger.debug("未找到信義大安路口站資訊")
        
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
    app.run(debug=True)
