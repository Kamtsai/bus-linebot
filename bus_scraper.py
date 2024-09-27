import os
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_minutes(info):
    match = re.search(r'(\d+)分', info)
    if match:
        return f"{match.group(1)}分鐘後到達"
    return info

def clean_arrival_info(info):
    logger.info(f"清理到站信息: {info}")
    info = re.sub(r'[A-Z]{3}-\d{4}', '', info).strip()
    if '分' in info:
        return extract_minutes(info)
    if info in ['將到站', '進站中']:
        return info
    if re.match(r'\d+站', info):
        return f"{info}後到達"
    if info in ['南港分局(向陽)', '永春高中', '臺北車站', '捷運昆陽站', '青年公園']:
        return '終點站'
    return info

def get_bus_arrival_time(url, station_name, direction):
    logger.info(f"開始處理 URL: {url}")
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
        logger.info("啟動 Chrome 瀏覽器")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info(f"訪問 URL: {url}")
        driver.get(url)
        
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        except TimeoutException:
            logger.error("頁面加載超時")
            return f"{route_info}: 頁面加載超時"
        
        route_info = driver.title.split(']')[0].strip('[') if driver.title else "未知路線"
        logger.info(f"獲取到路線信息: {route_info}")
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        logger.info(f"找到 {len(tables)} 個表格")
        
        target_table = None
        for table in tables:
            if "往" in table.text:
                target_table = table
                break
        
        if not target_table:
            logger.error("未找到包含路線信息的表格")
            return f"{route_info}: 未找到路線信息表格"
        
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        logger.info(f"目標表格有 {len(rows)} 行")
        
        if len(rows) < 2:
            logger.error("表格行數不足")
            return f"{route_info}: 表格結構不符合預期"
        
        directions = rows[0].find_elements(By.TAG_NAME, "td")
        if len(directions) < 2:
            logger.warning("無法從表格獲取方向信息，使用默認值")
            outbound = "去程"
            inbound = "返程"
        else:
            outbound = directions[0].text.strip().split('\n')[0]
            inbound = directions[1].text.strip().split('\n')[0]
        logger.info(f"去程: {outbound}, 返程: {inbound}")
        
        target_column = 1 if direction == "返程" else 0
        info_column = 0 if direction == "返程" else 1
        
        logger.info(f"搜索站點: {station_name}")
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                current_station = cells[target_column].text.strip()
                if station_name in current_station:
                    arrival_info = clean_arrival_info(cells[info_column].text.strip())
                    direction_text = inbound if direction == "返程" else outbound
                    logger.info(f"找到站點: {current_station}, 到站信息: {arrival_info}")
                    return f"{route_info}: {current_station} → {direction} ({direction_text}) 實時信息: {arrival_info}"
        
        # 如果沒有找到完全匹配的站名，嘗試部分匹配
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                current_station = cells[target_column].text.strip()
                if any(part in current_station for part in station_name.split()):
                    arrival_info = clean_arrival_info(cells[info_column].text.strip())
                    direction_text = inbound if direction == "返程" else outbound
                    logger.info(f"找到部分匹配站點: {current_station}, 到站信息: {arrival_info}")
                    return f"{route_info}: {current_station} → {direction} ({direction_text}) 實時信息: {arrival_info}"
        
        logger.warning(f"未找到站點: {station_name}")
        return f"{route_info}: 未找到 {station_name} 站資訊或對應的時間信息"
    
    except Exception as e:
        logger.error(f"發生錯誤: {str(e)}", exc_info=True)
        return f"{route_info}: 處理過程中發生錯誤 - {str(e)}"
    
    finally:
        if 'driver' in locals():
            logger.info("關閉瀏覽器")
            driver.quit()

def get_bus_arrival_times():
    logger.info("開始獲取公車到站時間")
    urls = [
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=17869",  # 88區
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=15708",  # 信義幹線
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=10841",  # 0東
        "https://pda5284.gov.taipei/MQS/route.jsp?rid=10873"   # 20
    ]
    
    results = []
    for url in urls:
        result_cks = get_bus_arrival_time(url, "中正紀念堂", "返程")
        result_xdal = get_bus_arrival_time(url, "信義大安路口", "去程")
        results.append(result_cks)
        results.append(result_xdal)
    
    logger.info("完成獲取公車到站時間")
    return "\n\n".join(results)

if __name__ == "__main__":
    print(get_bus_arrival_times())
