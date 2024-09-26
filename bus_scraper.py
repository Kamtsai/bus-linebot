import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def clean_arrival_info(info):
    # 移除车牌号
    info = re.sub(r'[A-Z]{3}-\d{4}', '', info).strip()
    # 处理特殊情况
    if '南港分局' in info:
        return '尚未发车'
    return info

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
    route_info = "未知路线"

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        route_info = driver.title.split(']')[0].strip('[') if driver.title else "未知路线"
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        if len(tables) < 3:
            return f"{route_info}: 未找到足够的表格"
        
        target_table = tables[2]
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        
        if len(rows) < 2:
            return f"{route_info}: 表格结构不符合预期"
        
        directions = rows[0].find_elements(By.TAG_NAME, "td")
        if len(directions) < 2:
            return f"{route_info}: 无法获取方向信息"
        
        outbound = directions[0].text.strip().split('\n')[0]
        inbound = directions[1].text.strip().split('\n')[0]
        
        target_column = 1 if direction == "返程" else 0
        info_column = 0 if direction == "返程" else 1
        
        for i, row in enumerate(rows[1:], 1):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                current_station = cells[target_column].text.strip()
                if station_name in current_station:
                    arrival_info = clean_arrival_info(cells[info_column].text.strip())
                    direction_text = inbound if direction == "返程" else outbound
                    return f"{route_info}: {station_name} → {direction_text} 实时信息: {arrival_info}"
        
        # 如果没有找到站点，尝试在整个表格中搜索
        for i, row in enumerate(rows[1:], 1):
            cells = row.find_elements(By.TAG_NAME, "td")
            for cell in cells:
                if station_name in cell.text:
                    adjacent_cell = cells[0] if cell == cells[1] else cells[1]
                    arrival_info = clean_arrival_info(adjacent_cell.text.strip())
                    direction_text = inbound if direction == "返程" else outbound
                    return f"{route_info}: {station_name} → {direction_text} 实时信息: {arrival_info}"
        
        return f"{route_info}: 未找到 {station_name} 站资讯或对应的时间信息"
    
    except Exception as e:
        return f"{route_info}: 处理过程中发生错误 - {str(e)}"
    
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
        result_cks = get_bus_arrival_time(url, "中正纪念堂", "返程")
        result_xdal = get_bus_arrival_time(url, "信义大安路口", "去程")
        results.append(result_cks)
        results.append(result_xdal)
    
    return "\n\n".join(results)

if __name__ == "__main__":
    print(get_bus_arrival_times())
