import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from pytz import timezone

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_minutes(time_info):
    if '分' in time_info:
        return time_info
    elif '將到站' in time_info or '進站中' in time_info:
        return time_info
    else:
        return '未發車'

def clean_route_name(route_info):
    return route_info.replace('(公車雙向轉乘優惠)', '').strip()

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
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "spnUpdateTime")))
        
        logger.debug("頁面加載完成")
        
        # 執行JavaScript來更新頁面數據
        driver.execute_script("queryDyna();")
        
        # 等待數據更新
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.ID, "spnUpdateTime"), ":")
        )
        
        route_info = clean_route_name(driver.title.split(']')[0].strip('['))
        logger.debug(f"路線信息: {route_info}")
        
        target_stations = {
            "中正紀念堂": ("返程", "tteback"),
            "信義大安路口": ("去程", "ttego")
        }
        
        info = {station: {} for station in target_stations}
        for station, (direction, class_prefix) in target_stations.items():
            try:
                elements = driver.find_elements(By.XPATH, f"//tr[contains(@class, '{class_prefix}')]//a[contains(text(), '{station}')]/../following-sibling::td")
                if elements:
                    time_info = elements[0].text.strip()
                    processed_time = extract_minutes(time_info)
                    info[station][route_info] = processed_time
                    logger.debug(f"目標站點信息: {station} ({direction}) → {processed_time}")
                else:
                    info[station][route_info] = "未找到資訊"
                    logger.warning(f"未找到站點 {station} 的信息")
            except Exception as e:
                logger.error(f"處理站點 {station} 時發生錯誤: {str(e)}")
                info[station][route_info] = "處理時發生錯誤"

        return info
    
    except Exception as e:
        logger.exception(f"發生錯誤: {str(e)}")
        return {station: {route_info: f"處理過程中發生錯誤 - {str(e)}"} for station in target_stations}
    
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
    
    results = {"中正紀念堂": {}, "信義大安路口": {}}
    for url in urls:
        result = get_bus_info(url)
        for station in result:
            results[station].update(result[station])
    
    # 使用台北時區
    taipei_tz = timezone('Asia/Taipei')
    current_time = datetime.now(taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    cks_info = f"資訊更新時間: {current_time}\n\n中正紀念堂站資訊（返程）：\n"
    for route, time in results["中正紀念堂"].items():
        cks_info += f"{route}: {time}\n"
    
    xdal_info = f"資訊更新時間: {current_time}\n\n信義大安路口站資訊（去程）：\n"
    for route, time in results["信義大安路口"].items():
        xdal_info += f"{route}: {time}\n"
    
    logger.info("完成獲取公車到站時間")
    logger.debug(f"中正紀念堂站資訊:\n{cks_info}")
    logger.debug(f"信義大安路口站資訊:\n{xdal_info}")
    return cks_info, xdal_info

if __name__ == "__main__":
    cks_info, xdal_info = get_bus_arrival_times()
    print(cks_info)
    print("\n" + "="*50 + "\n")
    print(xdal_info)
