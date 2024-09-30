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

    route_info = "未知路線"  # 初始化 route_info

    try:
        logger.debug("啟動 Chrome 瀏覽器")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.debug(f"訪問 URL: {url}")
        driver.get(url)
        
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "spnUpdateTime")))
        except TimeoutException:
            logger.error("頁面加載超時")
            return "頁面加載超時"
        
        logger.debug("頁面加載完成")
        
        route_info = driver.title.strip('[]')
        logger.debug(f"路線信息: {route_info}")
        
        # 執行JavaScript來更新頁面數據
        driver.execute_script("queryDyna();")
        
        # 等待數據更新，但不使用 staleness_of
        try:
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element((By.ID, "spnUpdateTime"), ":")
            )
        except TimeoutException:
            logger.warning("等待數據更新超時，繼續處理")
        
        # 保存完整的 HTML 內容
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.debug("已保存頁面源代碼到 page_source.html")
        
        target_stations = {
            "中正紀念堂": "inbound",
            "信義大安路口": "outbound"
        }
        info = {station: {} for station in target_stations}
        
        for station in target_stations:
            try:
                station_element = driver.find_element(By.XPATH, f"//a[contains(text(), '{station}')]")
                parent_row = station_element.find_element(By.XPATH, "./ancestor::tr")
                time_cell = parent_row.find_element(By.XPATH, "./td[2]")
                arrival_time = time_cell.text.strip()
                
                direction = "去程" if target_stations[station] == "outbound" else "返程"
                info[station][direction] = arrival_time if arrival_time else "無班次資訊"
                logger.debug(f"目標站點信息: {station} ({direction}) → {arrival_time}")
            except NoSuchElementException:
                logger.warning(f"未找到站點 {station} 的信息")
                info[station]["無方向"] = "未找到站點信息"

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
