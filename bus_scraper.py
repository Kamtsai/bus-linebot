import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        logger.debug(f"找到 {len(tables)} 個表格")
        
        if len(tables) < 3:
            logger.error("未找到足夠的表格")
            return "未找到足夠的表格"
        
        target_table = tables[2]
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        logger.debug(f"目標表格有 {len(rows)} 行")
        
        if len(rows) < 2:
            logger.error("表格行數不足")
            return "表格結構不符合預期"
        
        route_info = driver.title.split(']')[0].strip('[') if ']' in driver.title else "未知路線"
        info = [f"{route_info}:"]
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                station = cells[0].text.strip()
                time = cells[1].text.strip()
                info.append(f"{station} → {time}")
        
        return "\n".join(info)
    
    except Exception as e:
        logger.exception(f"發生錯誤: {str(e)}")
        return f"處理過程中發生錯誤 - {str(e)}"
    
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
    
    logger.info("完成獲取公車到站時間")
    return "\n\n".join(results)

if __name__ == "__main__":
    try:
        print("正在獲取公車資訊，請稍候...")
        output = get_bus_arrival_times()
        print(output)
    except Exception as e:
        error_msg = f"獲取公車資訊時發生錯誤：{str(e)}"
        logger.exception(error_msg)
        print(error_msg)
