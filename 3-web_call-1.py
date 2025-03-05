import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def click_button(driver, timeout, locator_strategy, locator_value):
    try:
        # 等待元素可点击
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((locator_strategy, locator_value))
        )
        element.click()
    except Exception as e:
        print(f"点击元素失败，定位方式: {locator_strategy}，定位值: {locator_value}，错误信息: {e}")
def input_text(driver, timeout, locator_strategy, locator_value, text):
    try:
        # 等待元素存在
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((locator_strategy, locator_value))
        )
        element.send_keys(text)
    except Exception as e:
        print(f"输入文本失败，定位方式: {locator_strategy}，定位值: {locator_value}，错误信息: {e}")
def download_images(driver, url, save_folder='images'):
    i = 0
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    try:
        img_elements = driver.find_elements(By.TAG_NAME, 'img')
        for img in img_elements:
            img_url = img.get_attribute('src')
            if img_url:
                if not img_url.startswith('http'):
                    base_url = url.rsplit('/', 1)[0]
                    img_url = f"{base_url}/{img_url}"
                try:
                    img_response = requests.get(img_url)
                    print(img_response.status_code)
                    if img_response.status_code == 200:
                        with open(f"C:\\Users\\L\\Desktop\\表情\\picture\\x{i}.jpg", 'wb') as f:
                            f.write(img_response.content)
                            i += 1
                        print(f"图片下载成功")
                    else:
                        print(f"图片 {img_url} 下载失败，状态码: {img_response.status_code}")
                except requests.RequestException as e:
                    print(f"请求图片 {img_url} 失败，错误信息: {e}")
    except Exception as e:
        print(f"未找到图片元素: {e}")

edge_driver_path = 'D:\\edgedriver_win64\\msedgedriver.exe'
service = Service(edge_driver_path)
driver = webdriver.Edge(service=service)
url = 'https://www.coze.cn/template/agent/7436703249849368588?'
driver.get(url)
try:
    click_button(driver, 20, By.XPATH, "//span[text()='登录']")
    click_button(driver, 20, By.XPATH, "//span[text()='账号登录']")
    input_text(driver, 10, By.ID, 'Identity_input', '2104117542')
    input_text(driver, 10, By.ID, 'Password_input', 'Wang88888888')
    click_button(driver, 10, By.XPATH, "//span[text()='登录']")
    print("已登录")
except Exception as e:
    print(f"登录失败: {e}")
try:
    text_title = "小猪的勇敢与冒险"
    input_text(driver, 20, By.CSS_SELECTOR, "[data-testid='bot.ide.chat_area.chat_input.textarea']", text_title)
    print("输入完毕！")
except Exception as e:
    print(f"输入失败: {e}")
time.sleep(10)

download_images(driver, url,"C:\\Users\\L\\Desktop\\表情\\picture")

driver.quit()