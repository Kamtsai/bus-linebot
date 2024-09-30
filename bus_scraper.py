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
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "spnUpdateTime")))
        
        logger.debug("頁面加載完成")
        
        # 執行JavaScript來更新頁面數據
        driver.execute_script("queryDyna();")
        
        # 等待數據更新
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.ID, "spnUpdateTime"), ":")
        )
        
        route_info = driver.title.split(']')[0].strip('[')
        logger.debug(f"路線信息: {route_info}")
        
        target_stations = {
            "中正紀念堂": ("//a[contains(text(), '中正紀念堂')]/../following-sibling::td", "返程"),
            "信義大安路口": ("//a[contains(text(), '信義大安路口')]/../following-sibling::td", "去程")
        }
        
        info = {}
        for station, (xpath, direction) in target_stations.items():
            try:
                go_elements = driver.find_elements(By.XPATH, f"//tr[@class='ttego1' or @class='ttego2']//a[contains(text(), '{station}')]/../following-sibling::td")
                back_elements = driver.find_elements(By.XPATH, f"//tr[@class='tteback1' or @class='tteback2']//a[contains(text(), '{station}')]/../following-sibling::td")
                
                if station == "中正紀念堂" and back_elements:
                    time_info = back_elements[0].text.strip()
                    info[station] = f"返程: {time_info}"
                    logger.debug(f"目標站點信息: {station} (返程) → {time_info}")
                elif station == "信義大安路口" and go_elements:
                    time_info = go_elements[0].text.strip()
                    info[station] = f"去程: {time_info}"
                    logger.debug(f"目標站點信息: {station} (去程) → {time_info}")
                else:
                    info[station] = f"{direction}: 未找到資訊"
                    logger.warning(f"未找到站點 {station} 的信息")
            except Exception as e:
                logger.error(f"處理站點 {station} 時發生錯誤: {str(e)}")
                info[station] = f"{direction}: 處理時發生錯誤"

        result = f"{route_info}:\n" + "\n".join([f"{station}: {info}" for station, info in info.items()])
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
