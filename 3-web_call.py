import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui

edge_driver_path = 'D:\\edgedriver_win64\\msedgedriver.exe'  # 驱动路径
service = Service(edge_driver_path)
driver = webdriver.Edge(service=service)

# 打开目标网页
url = 'https://www.coze.cn/template/agent/7436703249849368588?'  # 目标网页 URL
driver.get(url)

def click_botton ( x1,x2,x3 ):
    click_button1 = WebDriverWait(driver, x1).until(
        EC.element_to_be_clickable((x2, x3)))
    click_button1.click()

def input_botton ( x1,x2,x3,x4 ):
    username_input = WebDriverWait(driver, x1).until(
        EC.presence_of_element_located((x2, x3))
    )
    username_input.send_keys(x4)

# 登录
try:
    click_botton ( 10, By.XPATH, "//span[text()='登录']" )
    click_botton ( 20, By.XPATH, "//span[text()='账号登录']" )
    input_botton ( 10, By.ID, 'Identity_input', '2104117542' )
    input_botton ( 10, By.ID, 'Password_input', 'Wang88888888' )
    click_botton ( 10, By.XPATH, "//span[text()='登录']" )
    print("已登录")
except Exception as e:
    print(f"登录失败: {e}")
# 输入
try:
    text_title = "小兔子的勇敢与冒险"
    input_botton ( 10, By.CSS_SELECTOR, "[data-testid='bot.ide.chat_area.chat_input.textarea']", text_title)

    print("输入完毕！")
except Exception as e:
    print(f"输入失败: {e}")

time.sleep(50)
# # 等待反馈信息元素出现
# try:
#     feedback_element = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.CLASS_NAME, 'icon-icon icon-icon-coz_microphone text-18px'))
#     )
#     feedback_text = feedback_element.text
#     print(f"获取到的反馈信息: {feedback_text}")
# except Exception as e:
#     print(f"未找到反馈信息元素: {e}")

# 关闭浏览器
driver.quit()