import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_bus_arrival_time(url, station_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    print(f"使用 ChromeDriver 路徑: {chromedriver_path}")
    
    service = Service(executable_path=chromedriver_path)
    route_info = "未知路線"  # 初始化 route_info

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
        
        inbound = directions[1].text.strip().split('\n')[0]
        
        outbound_stations = []
        inbound_times = []
        
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                station = cells[0].text.strip().split('\n')[0]
                if station and not station.isdigit() and "分" not in station:
                    outbound_stations.append(station)
                time_info = cells[1].text.strip().split('\n')
                inbound_times.extend([t for t in time_info if "分" in t or t in ["將到站", "進站中", "未發車"]])
        
        target_index = -1
        for i, station in enumerate(outbound_stations):
            if station_name in station:
                target_index = i
                break
        
        if target_index != -1 and target_index < len(inbound_times):
            return f"{route_info}: {station_name} → {inbound} 實時信息: {inbound_times[target_index]}"
        
        return f"{route_info}: 未找到 {station_name} 站資訊或對應的時間信息"
    
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return f"{route_info}: 處理過程中發生錯誤 - {str(e)}"
    
    finally:
        if 'driver' in locals():
            driver.quit()

def get_bus_arrival_times(station_name):
    urls = [
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=17869",
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=15708",
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=10841",
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=10873"
    ]
    
    results = []
    for url in urls:
        result = get_bus_arrival_time(url, station_name)
        results.append(result)
    
    return "\n".join(results)

if __name__ == "__main__":
    print(get_bus_arrival_times("中正紀念堂"))
