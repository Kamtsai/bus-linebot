def background_task(user_id):
    try:
        logger.debug("開始執行背景任務")
        bus_info = get_bus_arrival_times()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(f"獲取到的公車信息:\n{bus_info}")
        
        info_list = bus_info.split('\n\n')
        
        time_message = f"資訊更新時間: {current_time}\n\n"
        
        cks_info = "中正紀念堂站資訊（返程）：\n"
        xdal_info = "信義大安路口站資訊（去程）：\n"
        
        for route_info in info_list:
            route_lines = route_info.split('\n')
            route_name = route_lines[0]
            cks_info += f"{route_name}\n"
            xdal_info += f"{route_name}\n"
            
            for line in route_lines[1:]:
                if '中正紀念堂' in line:
                    cks_info += f"{line}\n"
                elif '信義大安路口' in line:
                    xdal_info += f"{line}\n"
            
            cks_info += "\n"
            xdal_info += "\n"
        
        cks_message = time_message + cks_info
        xdal_message = time_message + xdal_info
        
        line_bot_api.push_message(user_id, TextSendMessage(text=cks_message.strip()))
        line_bot_api.push_message(user_id, TextSendMessage(text=xdal_message.strip()))
        
        logger.debug(f"已發送中正紀念堂信息和信義大安路口信息")
        
    except Exception as e:
        error_message = f"抱歉，獲取公車資訊時發生錯誤：{str(e)}"
        line_bot_api.push_message(user_id, TextSendMessage(text=error_message))
        logger.exception(f"背景任務執行錯誤: {str(e)}")

# ... (其餘代碼保持不變)
