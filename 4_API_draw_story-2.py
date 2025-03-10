import requests
import json
import uuid
import re
import wave
import vosk
import pygame
import pyaudio
import time
from pyttsx3 import init

# 定义路径
vosk_model_path = "D:\\vosk\\vosk-model-small-cn-0.22"
WAVE_INPUT = "C:\\Users\\L\\Desktop\\表情\\audio\\what_you_sad_story.wav"
# 定义扣子令牌
YOUR_BOT_ID = "7478702234465779749"
YOUR_COZE_TOKEN = "pat_FQ6Oh7ruUwOM7c0FH8emVhusI9Un0KJ6djDvQC7AJSU1q6kd9uuekoLCRx5lljfA"
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
# 定义按钮3的参数,控制嘴的大小
button3_x = 140
button3_key = 0
button3_pos = (button3_x, button_y)
color_3 = green
# 设置窗口大小
width, height = 1000, 600
# 定义文本
text_title = "无"
text_all   = []
text_story = []
image_url  = []

# 初始化
p = pyaudio.PyAudio()                   
model = vosk.Model(vosk_model_path)     
rec = vosk.KaldiRecognizer(model, 16000)
pygame.mixer.init()                                     
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("绘本")

# 定义扣子结构体
class ChatBot:
    def __init__(self):
        self.messages = []
        self.input_value = ''
        self.conversation_id = None
        self.bot_id = YOUR_BOT_ID 
        self.user_id = self.generate_uuid() 
    def generate_uuid(self):
        return str(uuid.uuid4())
    def send_message(self):
        message = self.input_value
        if not message:
            return
        if not self.conversation_id:
            self.create_empty_conversation(self.send_message)
            return
        self.messages.append({'role': 'user', 'content': message})
        self.input_value = ''
        access_token = YOUR_COZE_TOKEN 
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'conversation_id': self.conversation_id,  
            'bot_id': self.bot_id, 
            'user_id': self.user_id,
            'stream': True,  # 是否启用流式返回
            'auto_save_history': False, # 是否自动保存历史记录
            'additional_messages': [
                {
                    'role': 'user',
                    'content': message,
                    'content_type': 'text'
                }
            ]
        }
        response = requests.post('https://api.coze.cn/v3/chat', headers=headers, json=data, stream=True)
        try:
            response.raise_for_status()  
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('event:'):
                        event_type = decoded_line.split(':', 1)[1].strip()
                    elif decoded_line.startswith('data:'):
                        event_data = decoded_line.split(':', 1)[1].strip()
                        self.handle_event(event_type, event_data)
        except:
            print('error1')
    def handle_event(self, event_type, event_data):
        if event_type == 'conversation.chat.created':
            data = json.loads(event_data)
            print('对话已创建:', data)
        elif event_type == 'conversation.message.delta':
            data = json.loads(event_data)
            if data.get('role') == 'assistant':
                self.messages.append({'role': 'assistant', 'content': data.get('content')})
                text_all.append(data.get('content')) 
    def create_empty_conversation(self, callback):
        access_token = YOUR_COZE_TOKEN  
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post('https://api.coze.cn/v1/conversation/create', headers=headers)
        try:
            response.raise_for_status()  
            res_data = response.json()
            if res_data.get('code') == 0:
                self.conversation_id = res_data['data']['id']
                self.messages.append({'role': 'system', 'content': f'空会话已创建，ID: {self.conversation_id}'})
                if callback:
                    callback() 
        except :
            print('error2')

# 函数：重新开始，数据刷新
def restart():
    global text_all,text_story,image_url,text_title
    text_title = '无'
    text_all   = []
    text_story = []
    image_url  = []

# 函数：获取图片网址
def filter_pic(text_list):
    text = ''.join(text_list)
    pattern1 = r'\((.*?)\)'
    matches = re.findall(pattern1, text)
    if matches:
        print("图片网址:", matches)
    else:
        print("未找到图片网址。")
    return matches

# 函数：图片下载
def download_image(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"图片下载成功，保存路径: {save_path}")
    except :
        print(f"图片下载错误")

# 函数：图片显示
def picture_desplay(picture_road, pos, target_height):
        picture_1 = pygame.image.load(picture_road)
        original_width  = picture_1.get_width()
        original_height = picture_1.get_height()
        f_p = round(target_height/original_height,2)
        picture_new = pygame.transform.scale(picture_1, (original_width * f_p, original_height * f_p))
        screen.blit(picture_new, pos)

# 函数：故事处理
def filter_text(text_list):
    result = []
    pattern = re.compile(r'[\u4e00-\u9fa5，。！？：；、“”‘’,;\'\"\n]')
    for text in text_list:
        text = text.replace('\n\n', '\n')
        filtered_chars = pattern.findall(text)
        filtered_text = ''.join(filtered_chars)
        result.append(filtered_text)
    final_text = ''.join(result)
    return final_text

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
    
# 函数：录音功能
def record_audio(filename):
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
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

# main
button0_drag = False
button1_drag = False
button2_drag = False
button3_drag = False
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
            elif (((mouse_x - button3_pos[0]) ** 2 + (mouse_y - button3_pos[1]) ** 2) ** 0.5<= button_radius):
                button3_drag = True
        elif event.type == pygame.MOUSEBUTTONUP:
            button0_drag = False
            button1_drag = False
            button2_drag = False
            button3_drag = False
        if  button0_drag:
            if  button0_key == 0 :
                restart()
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
        elif  button3_drag  :
            if  button3_key == 0 :
                button3_key = 1
                color_3     = red
    if button0_key == 0:    
        text_state = "运行中···"
        color_0     = green
    elif button0_key :    
        text_state = "录音中···"
    if button1_key == 0 :    
        color_1     = green
    elif button1_key :    
        text_state = "故事中···"
    if button3_key == 0 :    
        color_3     = green
    elif button3_key :    
        text_state = "朗读中···"
    # 绘制背景
    screen.fill(black)  
    pygame.draw.rect(screen, white, (160,0,2,60))
    pygame.draw.rect(screen, white, (0,60,width,2))
    pygame.draw.rect(screen, white, (790,60,2,540))
    pygame.draw.rect(screen, white, (400,0,2,60))
    # 显示状态文本  
    blit_text1( 36 , text_state,( 170 , 12 ) )
    # 显示故事内容
    font1 = pygame.font.SysFont('SimHei', 12)
    blit_text2(screen, text_story, (6, 60), font1, 780)
    # 显示标题文本
    blit_text1(22, text_title, (410, 18))
    # 绘制按钮
    pygame.draw.circle(screen, color_0, button0_pos, button_radius)
    pygame.draw.circle(screen, color_1, button1_pos, button_radius)
    pygame.draw.circle(screen, color_2, button2_pos, button_radius)
    pygame.draw.circle(screen, color_3, button3_pos, button_radius)
    # 图片显示
    if button2_key == 1:
        for i in range(5):
            picture_desplay(f"C:\\Users\\L\\Desktop\\表情\\picture\\image{i + 1}.png", (800,80+(i)*100), 100)
    # 窗口刷新
    pygame.display.flip()
    pygame.time.Clock().tick(60)
    # 录音
    if button0_key == 1 :    
        print("麦克风中···")
        record_audio(WAVE_INPUT)
        print("麦克风关闭！")
        text_title = wave_to_text( WAVE_INPUT, vosk_model_path)
        print(f"text_title：{text_title}")
        button0_key = 0
    # 个人令牌访问扣子
    if button1_key == 1 :  
        start_time1 = time.time()
        chat_bot = ChatBot()
        chat_bot.input_value = text_title
        chat_bot.send_message()
        end_time1 = time.time()
        image_url = filter_pic(text_all)
        text_story = filter_text(text_all)
        for num_picture, url in enumerate(image_url):
            download_image(url, f"C:\\Users\\L\\Desktop\\表情\\picture\\image{num_picture + 1}.png")
        run_time1 = end_time1 - start_time1
        print(f'扣子会话时间：{round(run_time1,2)}s')
        button1_key = 0
    # 朗读文字
    if button3_key == 1:
        engine = init()
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'zh' in voice.languages:
                engine.setProperty('voice', voice.id)
                break
        engine.setProperty('rate', 200)
        engine.setProperty('volume', 1.0)
        story_text = ''.join(text_story)
        engine.say(story_text)
        engine.runAndWait()
        button3_key = 0 

