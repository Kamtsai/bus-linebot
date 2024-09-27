import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_bus_info(url):
    logger.debug(f"開始處理 URL: {url}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    
    service = Service(executable_path=chromedriver_path)

    try:
        logger.debug("啟動 Chrome 瀏覽器")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.debug(f"訪問 URL: {url}")
        driver.get(url)
        
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        except TimeoutException:
            logger.error("頁面加載超時")
            return "頁面加載超時"
        
        logger.debug("頁面加載完成")
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        route_info = soup.title.string.strip('[]')
        logger.debug(f"路線信息: {route_info}")
        
        target_stations = {
            "中正紀念堂": "inbound",
            "信義大安路口": "outbound"
        }
        info = {station: {} for station in target_stations}
        
        # 嘗試找到包含公車資訊的表格
        tables = soup.find_all('table')
        logger.debug(f"找到 {len(tables)} 個表格")
        
        target_table = None
        for table in tables:
            if '去程' in table.text and '返程' in table.text:
                target_table = table
                break
        
        if not target_table:
            logger.error("未找到包含公車資訊的表格")
            return f"{route_info}: 未找到包含公車資訊的表格"
        
        rows = target_table.find_all('tr')
        
        direction_names = [td.text.strip() for td in rows[0].find_all('td')]
        outbound_name, inbound_name = direction_names[:2]
        
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) >= 2:
                outbound_station = cells[0].text.strip()
                outbound_time = cells[1].text.strip()
                
                if outbound_station in target_stations and target_stations[outbound_station] == "outbound":
                    info[outbound_station][outbound_name] = outbound_time if outbound_time else "無班次資訊"
                    logger.debug(f"目標站點信息: {outbound_station} ({outbound_name}) → {outbound_time}")
                
                if len(cells) > 2:
                    inbound_station = cells[-2].text.strip()
                    inbound_time = cells[-1].text.strip()
                    if inbound_station in target_stations and target_stations[inbound_station] == "inbound":
                        info[inbound_station][inbound_name] = inbound_time if inbound_time else "無班次資訊"
                        logger.debug(f"目標站點信息: {inbound_station} ({inbound_name}) → {inbound_time}")

        result = f"{route_info}:\n"
        for station, directions in info.items():
            if directions:
                result += f"{station}:\n"
                for direction, time in directions.items():
                    result += f"  {direction}: {time}\n"
            else:
                result += f"{station}: 當前無班次資訊\n"

        logger.debug(f"處理結果:\n{result}")
        return result.strip()
    
    except Exception as e:
        logger.exception(f"發生錯誤: {str(e)}")
        return f"{route_info}: 處理過程中發生錯誤 - {str(e)}"
    
    finally:
        if 'driver' in locals():
            logger.debug("關閉瀏覽器")
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
        result = get_bus_info(url)
        results.append(result)
    
    final_result = "\n\n".join(results)
    logger.info("完成獲取公車到站時間")
    logger.debug(f"最終結果:\n{final_result}")
    return final_result

if __name__ == "__main__":
    print(get_bus_arrival_times())
