import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def clean_arrival_info(info):
    print(f"清理到站信息: {info}")
    info = re.sub(r'[A-Z]{3}-\d{4}', '', info).strip()
    if info in ['南港分局(向陽)', '南港花園社區二', '瑞湖街口', '永春高中']:
        return '尚未發車'
    if '分' in info or info in ['將到站', '進站中']:
        return info
    return '尚未發車'

def get_bus_arrival_time(url, station_name, direction):
    print(f"開始處理 URL: {url}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    
    service = Service(executable_path=chromedriver_path)
    route_info = "未知路線"

    try:
        print("啟動 Chrome 瀏覽器")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"訪問 URL: {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        route_info = driver.title.split(']')[0].strip('[') if driver.title else "未知路線"
        print(f"獲取到路線信息: {route_info}")
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"找到 {len(tables)} 個表格")
        
        if len(tables) < 3:
            print("表格數量不足")
            return f"{route_info}: 未找到足夠的表格"
        
        target_table = tables[2]
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        print(f"目標表格有 {len(rows)} 行")
        
        if len(rows) < 2:
            print("表格行數不足")
            return f"{route_info}: 表格結構不符合預期"
        
        directions = rows[0].find_elements(By.TAG_NAME, "td")
        if len(directions) < 2:
            print("無法獲取方向信息")
            return f"{route_info}: 無法獲取方向信息"
        
        outbound = directions[0].text.strip().split('\n')[0]
        inbound = directions[1].text.strip().split('\n')[0]
        print(f"去程: {outbound}, 返程: {inbound}")
        
        target_column = 1 if direction == "返程" else 0
        info_column = 0 if direction == "返程" else 1
        
        print(f"搜索站點: {station_name}")
        for i, row in enumerate(rows[1:], 1):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                current_station = cells[target_column].text.strip()
                print(f"檢查第 {i} 行: {current_station}")
                if station_name in current_station:
                    arrival_info = clean_arrival_info(cells[info_column].text.strip())
                    direction_text = inbound if direction == "返程" else outbound
                    print(f"找到站點: {station_name}, 到站信息: {arrival_info}")
                    return f"{route_info}: {station_name} → {direction_text} 實時信息: {arrival_info}"
        
        print("在整個表格中搜索站點")
        for i, row in enumerate(rows[1:], 1):
            cells = row.find_elements(By.TAG_NAME, "td")
            for j, cell in enumerate(cells):
                if station_name in cell.text:
                    adjacent_cell = cells[1-j]  # 如果站名在第0列，取第1列；反之亦然
                    arrival_info = clean_arrival_info(adjacent_cell.text.strip())
                    direction_text = inbound if direction == "返程" else outbound
                    print(f"在整個表格中找到站點: {station_name}, 到站信息: {arrival_info}")
                    return f"{route_info}: {station_name} → {direction_text} 實時信息: {arrival_info}"
        
        print(f"未找到站點: {station_name}")
        return f"{route_info}: 未找到 {station_name} 站資訊或對應的時間信息"
    
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        return f"{route_info}: 處理過程中發生錯誤 - {str(e)}"
    
    finally:
        if 'driver' in locals():
            print("關閉瀏覽器")
            driver.quit()

def get_bus_arrival_times():
    print("開始獲取公車到站時間")
    urls = [
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=17869",
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=15708",
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=10841",
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=10873"
    ]
    
    results = []
    for url in urls:
        result_cks = get_bus_arrival_time(url, "中正紀念堂", "返程")
        result_xdal = get_bus_arrival_time(url, "信義大安路口", "去程")
        results.append(result_cks)
        results.append(result_xdal)
    
    print("完成獲取公車到站時間")
    return "\n\n".join(results)

if __name__ == "__main__":
    print(get_bus_arrival_times())
