import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_bus_arrival_time(url, station_name, direction):
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
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        route_info = driver.title.split(']')[0].strip('[') if driver.title else "未知路線"
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        if len(tables) < 3:
            return f"{route_info}: 未找到足夠的表格"
        
        target_table = tables[2]
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        
        if len(rows) < 2:
            return f"{route_info}: 表格結構不符合預期"
        
        directions = rows[0].find_elements(By.TAG_NAME, "td")
        if len(directions) < 2:
            return f"{route_info}: 無法獲取方向信息"
        
        outbound = directions[0].text.strip().split('\n')[0]
        inbound = directions[1].text.strip().split('\n')[0]
        
        target_direction = 1 if direction == "返程" else 0
        
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                current_station = cells[target_direction].text.strip().split('\n')[0]
                if station_name in current_station:
                    arrival_time = cells[1-target_direction].text.strip().split('\n')[0]
                    return f"{route_info}: {station_name} → {inbound if direction == '返程' else outbound} 實時信息: {arrival_time}"
        
        # 如果沒有找到，嘗試在另一個方向尋找
        other_direction = 0 if target_direction == 1 else 1
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                current_station = cells[other_direction].text.strip().split('\n')[0]
                if station_name in current_station:
                    arrival_time = cells[1-other_direction].text.strip().split('\n')[0]
                    return f"{route_info}: {station_name} → {outbound if direction == '返程' else inbound} 實時信息: {arrival_time} (注意: 在{'去程' if direction == '返程' else '返程'}方向找到)"
        
        return f"{route_info}: 未找到 {station_name} 站資訊或對應的時間信息"
    
    except Exception as e:
        return f"{route_info}: 處理過程中發生錯誤 - {str(e)}"
    
    finally:
        if 'driver' in locals():
            driver.quit()

def get_bus_arrival_times():
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
    
    return "\n\n".join(results)

if __name__ == "__main__":
    print(get_bus_arrival_times())
