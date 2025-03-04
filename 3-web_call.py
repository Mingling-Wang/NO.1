import time
import os
import requests
import pyaudio
import wave
import vosk
import json
import pygame
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# 定义路径
vosk_model_path = "D:\\vosk\\vosk-model-small-cn-0.22"
WAVE_INPUT = "C:\\Users\\L\\Desktop\\表情\\audio\\what_you_sad_story.wav"
edge_driver_path = 'D:\\edgedriver_win64\\msedgedriver.exe' 
url = 'https://www.coze.cn/template/agent/7436703249849368588?'  # 目标网页 URL
# 图片数目
num_picture = 1
# 定义文本
text_state = "待机中···"
text_title = "无"
text_story = ["Hellow \n"]
# 定义录音参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5
# 定义颜色
white = (255, 255, 255)
blue  = (0,191,255)
black = (0, 0, 0)
red   = (255, 0, 0)
green = (0, 255, 0)
# 定义按钮
button_radius = 16  # 按钮的大小
button_y = 30
# 定义按钮0的参数,控制嘴的大小
button0_x = 20
button0_key = 0
button0_pos = (button0_x, button_y)
color_0 = green
# 定义按钮1的参数,控制嘴的大小
button1_x = 60
button1_key = 0
button1_pos = (button1_x, button_y)
color_1 = green
# 定义按钮2的参数,控制嘴的大小
button2_x = 100
button2_key = 0
button2_pos = (button2_x, button_y)
color_2 = green
# 设置窗口大小
width, height = 1000, 600

# 路径权限
new_permissions = 0o777
if os.path.exists(WAVE_INPUT):
    os.chmod(WAVE_INPUT, new_permissions)
if not os.path.exists('images'):
    os.makedirs('images')
    
# 初始化
p = pyaudio.PyAudio()                   
model = vosk.Model(vosk_model_path)     
rec = vosk.KaldiRecognizer(model, 16000)
pygame.mixer.init()                                     
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("绘本")

# 函数：文本直接显示函数
def blit_text1( num , text_t ,pos):
    font = pygame.font.SysFont('SimHei', num)
    text_state_surface = font.render(text_t, True, (255, 255, 255))
    screen.blit(text_state_surface, pos)

# 函数：长文字分割显示
def blit_text2(surface, text, pos, font, max_width, color=pygame.Color('white')): 
    words_list = []  
    for line in text:  
        words = line.split(' ') 
        words_list.extend(words)   
    x, y = pos
    word_last = " "
    for word in words_list:
        try:
            word_surface = font.render(word, True, color)
        except:
            continue
        word_width, word_height = word_surface.get_size()
        if word == "\n" and word_last != ("\n" or "\r"):
            x = pos[0]+ word_width  
            y += word_height 
        elif word == "\n":
            x = pos[0] + word_width
        else :
            if x + word_width > max_width:
                x = pos[0]  
                y += word_height  
            surface.blit(word_surface, (x, y))
            x += word_width
        word_last = word

# 函数：图片显示
def picture_desplay(picture_road, pos):
        picture_1 = pygame.image.load(picture_road)
        original_width, original_height = picture_1.get_size()
        f_p = round(125/original_width,2)
        picture_new = pygame.transform.scale(picture_1, (original_width * f_p, original_height * f_p))
        screen.blit(picture_new, pos)

# 函数：语音转文字
def wave_to_text(wav_file_path, model_path):
    model = vosk.Model(model_path)
    rec = vosk.KaldiRecognizer(model, 16000)
    wf = wave.open(wav_file_path, "rb")
    text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text += result["text"]
    final_result = json.loads(rec.FinalResult())
    text += final_result["text"]
    return text

# 函数：录音功能
def record_audio(filename):
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# 单击按钮
def click_button ( x0,x1,x2,x3 ):
    click_button1 = WebDriverWait(x0, x1).until(
        EC.element_to_be_clickable((x2, x3)))
    click_button1.click()
# 输入信息
def input_message ( x0,x1,x2,x3,x4,x5=False ):
    user_input = WebDriverWait(x0, x1).until(
        EC.presence_of_element_located((x2, x3))
    )
    user_input.send_keys(x4)
    if x5 == True :
        user_input.send_keys(Keys.RETURN)

# 网页操作
def web_call(path_wave):
    global text_story, num_picture
    service = Service(edge_driver_path)
    driver = webdriver.Edge(service=service)
    driver.get(url)
    try:
        click_button ( driver, 30, By.XPATH, "//span[text()='登录']" )
        click_button ( driver, 30, By.XPATH, "//span[text()='账号登录']" )
        input_message ( driver, 10, By.ID, 'Identity_input', '2104117542' )
        input_message ( driver, 10, By.ID, 'Password_input', 'Wang88888888' )
        click_button ( driver, 10, By.XPATH, "//span[text()='登录']" )
        print("已登录")
        text_title = wave_to_text( path_wave, vosk_model_path)
        input_message ( driver, 20, By.CSS_SELECTOR, "[data-testid='bot.ide.chat_area.chat_input.textarea']", text_title, True)
        print("输入完毕！")
    except Exception as e:
        print(f"{e}")
    time.sleep(10)
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        elements = soup.find_all(class_="container_a9149")
        for element in elements:
            text_story += element.text
            print(element.text)  # 打印元素内文本内容
            print(element.attrs)  # 打印元素所有属性
        print(f"故事内容：{text_story}")
    except Exception as e:
        print(f"未找到文字信息元素: {e}")
    try:   # 获取图片
        img_elements = driver.find_elements(By.TAG_NAME, 'img')
        for img in img_elements:
            img_url = img.get_attribute('src')
            if img_url:
                if not img_url.startswith('http'):
                    base_url = url.rsplit('/', 1)[0]
                    img_url = f"{base_url}/{img_url}"
                try:
                    img_response = requests.get(img_url)
                    if img_response.status_code == 200:
                        with open(f"C:\\Users\\L\\Desktop\\表情\\picture\\p{num_picture}.jpg", 'wb') as f:
                            f.write(img_response.content)
                            num_picture += 1
                        print(f"图片p{num_picture}下载成功")
                    else:
                        print(f"图片 {img_url} 下载失败，状态码: {img_response.status_code}")
                except requests.RequestException as e:
                    print(f"请求图片 {img_url} 失败，错误信息: {e}")
    except Exception as e:
        print(f"未找到图片元素: {e}")
    driver.quit()
button0_drag = False
button1_drag = False
button2_drag = False
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if (((mouse_x - button0_pos[0]) ** 2 + (mouse_y - button0_pos[1]) ** 2) ** 0.5<= button_radius):
                button0_drag = True
            elif (((mouse_x - button1_pos[0]) ** 2 + (mouse_y - button1_pos[1]) ** 2) ** 0.5<= button_radius):
                button1_drag = True
            elif (((mouse_x - button2_pos[0]) ** 2 + (mouse_y - button2_pos[1]) ** 2) ** 0.5<= button_radius):
                button2_drag = True
        elif event.type == pygame.MOUSEBUTTONUP:
            button0_drag = False
            button1_drag = False
            button2_drag = False
        if  button0_drag:
            if  button0_key == 0 :
                button0_key = 1
                color_0     = red  
        elif  button1_drag :
            if  button1_key == 0 :
                num_picture = 1
                button1_key = 1
                color_1     = red
        elif  button2_drag  :
            if  button2_key == 0 :
                button2_key = 1
                color_2     = red
    if button0_key == 0:    
        text_state = "运行中···"
        color_0     = green
    elif button0_key :    
        text_state = "录音中···"
    if button1_key == 0 :    
        text_state = "运行中···"
        color_1     = green
    elif button1_key :    
        text_state = "网页中···"
    # 绘制背景
    screen.fill(black)  
    pygame.draw.rect(screen, white, (120,0,2,60))
    pygame.draw.rect(screen, white, (0,60,width,2))
    pygame.draw.rect(screen, white, (490,60,2,540))
    pygame.draw.rect(screen, white, (360,0,2,60))
    # 显示状态文本  
    blit_text1( 36 , text_state,( 135 , 12 ) )
    # 显示故事内容
    font1 = pygame.font.SysFont('SimHei', 12)
    blit_text2(screen, text_story, (6, 60), font1, 490)
    # 显示标题文本
    blit_text1(20, text_title, (370, 15))
    # 绘制按钮
    pygame.draw.circle(screen, color_0, button0_pos, button_radius)
    pygame.draw.circle(screen, color_1, button1_pos, button_radius)
    pygame.draw.circle(screen, color_2, button2_pos, button_radius)
    # 图片显示
    i = 0
    for i in range(10):
        try:
            picture_desplay(f"C:\\Users\\L\\Desktop\\表情\\picture\\p{i+1}.jpg", (500+(i//4)*125,80+(i%4)*125))
        except:
            continue
    pygame.display.flip()
    if button0_key == 1 :    
        print("麦克风中···")
        record_audio(WAVE_INPUT)
        print("麦克风关闭！")
        button0_key = 0
    if button1_key == 1 :  
        web_call(WAVE_INPUT)
        button1_key = 0
    # if button2_key == 1 :    

    # 控制帧率
    pygame.time.Clock().tick(60)

