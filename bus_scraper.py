def get_bus_info(url):
    # ... (前面的代碼保持不變)

    target_stations = {
        "中正紀念堂": "inbound",
        "信義大安路口": "outbound"
    }
    info = {station: {} for station in target_stations}
    
    for row in rows[1:]:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 2:
            outbound_station = cells[0].text.strip()
            inbound_station = cells[-2].text.strip() if len(cells) > 2 else ""
            outbound_time = cells[1].text.strip()
            inbound_time = cells[-1].text.strip() if len(cells) > 2 else ""
            
            if outbound_station in target_stations and target_stations[outbound_station] == "outbound":
                info[outbound_station][outbound_name] = outbound_time
                logger.debug(f"目標站點信息: {outbound_station} ({outbound_name}) → {outbound_time}")
            
            if inbound_station in target_stations and target_stations[inbound_station] == "inbound":
                info[inbound_station][inbound_name] = inbound_time
                logger.debug(f"目標站點信息: {inbound_station} ({inbound_name}) → {inbound_time}")

    result = f"{route_info}:\n"
    for station, directions in info.items():
        if directions:
            result += f"{station}:\n"
            for direction, time in directions.items():
                result += f"  {direction}: {time}\n"
        else:
            result += f"{station}: 當前無班次\n"

    logger.debug(f"處理結果:\n{result}")
    return result.strip()

# ... (其餘代碼保持不變)
