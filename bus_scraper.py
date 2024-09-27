def get_bus_info(url):
    # ... (前面的代碼保持不變)

    info = {}
    found_stations = set()
    
    for row in rows[1:]:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 2:
            outbound_station = cells[0].text.strip()
            inbound_station = cells[-2].text.strip() if len(cells) > 2 else ""
            outbound_time = cells[1].text.strip()
            inbound_time = cells[-1].text.strip() if len(cells) > 2 else ""
            
            if outbound_station in target_stations and target_stations[outbound_station] == "outbound":
                info[f"{outbound_station} ({outbound_name})"] = outbound_time
                found_stations.add(outbound_station)
                logger.debug(f"目標站點信息: {outbound_station} ({outbound_name}) → {outbound_time}")
            
            if inbound_station in target_stations and target_stations[inbound_station] == "inbound":
                info[f"{inbound_station} ({inbound_name})"] = inbound_time
                found_stations.add(inbound_station)
                logger.debug(f"目標站點信息: {inbound_station} ({inbound_name}) → {inbound_time}")

    result = f"{route_info}:\n"
    for station in target_stations:
        if station in found_stations:
            if station in [key.split(' (')[0] for key in info]:
                result += "\n".join([f"{k} → {v}" for k, v in info.items() if k.startswith(station)])
                result += "\n"
            else:
                result += f"{station}: 當前無班次\n"
        else:
            result += f"{station}: 未找到站點信息\n"

    logger.debug(f"處理結果:\n{result}")
    return result.strip()

# ... (其餘代碼保持不變)
