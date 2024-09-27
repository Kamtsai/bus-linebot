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

def clean_arrival_info(info):
    logger.info(f"清理到站信息: {info}")
    info = re.sub(r'[A-Z]{3}-\d{4}', '', info).strip()
    if '分' in info:
        return info
    if info in ['將到站', '進站中']:
        return info
    if re.match(r'\d+站', info):
        return f"{info}後到達"
    if info in ['南港分局(向陽)', '永春高中', '臺北車站', '捷運昆陽站', '青年公園']:
        return '終點站'
    return info

def get_bus_arrival_time(url, station_names):
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
            return {station: f"{route_info}: 頁面加載超時" for station in station_names}
        
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
            return {station: f"{route_info}: 未找到路線信息表格" for station in station_names}
        
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        logger.info(f"目標表格有 {len(rows)} 行")
        
        if len(rows) < 2:
            logger.error("表格行數不足")
            return {station: f"{route_info}: 表格結構不符合預期" for station in station_names}
        
        directions = rows[0].find_elements(By.TAG_NAME, "td")
        if len(directions) < 2:
            logger.warning("無法從表格獲取方向信息，使用默認值")
            outbound = "去程"
            inbound = "返程"
        else:
            outbound = directions[0].text.strip().split('\n')[0]
            inbound = directions[1].text.strip().split('\n')[0]
        logger.info(f"去程: {outbound}, 返程: {inbound}")
        
        results = {}
        for station_name in station_names:
            found = False
            logger.info(f"搜索站點: {station_name}")
            for row in rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    current_station = cells[0].text.strip()
                    if station_name in current_station:
                        arrival_info = clean_arrival_info(cells[1].text.strip())
                        logger.info(f"找到站點: {current_station}, 到站信息: {arrival_info}")
                        results[station_name] = f"{arrival_info}"
                        found = True
                        break
            if not found:
                logger.warning(f"未找到站點: {station_name}")
                results[station_name] = "未找到站點信息"
        
        return results
    
    except Exception as e:
        logger.error(f"發生錯誤: {str(e)}", exc_info=True)
        return {station: f"處理過程中發生錯誤 - {str(e)}" for station in station_names}
    
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
    
    station_names = ["信義大安路口", "中正紀念堂"]
    results = {station: [] for station in station_names}
    
    for url in urls:
        route_results = get_bus_arrival_time(url, station_names)
        for station in station_names:
            results[station].append(route_results[station])
    
    logger.info("完成獲取公車到站時間")
    return results

def format_results(results):
    formatted_results = []
    for station, times in results.items():
        formatted_times = [str(time) if time is not None else "資訊不可用" for time in times]
        formatted_results.append(f"{station}: {', '.join(formatted_times)}")
    return "\n".join(formatted_results)

if __name__ == "__main__":
    try:
        results = get_bus_arrival_times()
        formatted_output = format_results(results)
        print(formatted_output)
    except Exception as e:
        print(f"獲取公車資訊時發生錯誤：{str(e)}")
