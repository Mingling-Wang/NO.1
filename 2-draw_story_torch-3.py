import asyncio
import base64
import json
import wave
import torch
import pygame
import time
import os
import numpy as np
import soundfile as sf
from scipy.signal import resample
import websockets
import pyaudio
from diffusers import StableDiffusionPipeline
import translators as ts
import json
from transformers import pipeline

# 定义路径
WAVE_INPUT = "C:\\Users\\L\\Desktop\\表情\\audio\\what_you_sad_story.wav"
WAVE_OUTPUT = "C:\\Users\\L\\Desktop\\表情\\audio\\what_you_receive_story.wav"
IMAGE_OUTPUT1 = "C:\\Users\\L\\Desktop\\表情\\picture\\generated_image1.png"
IMAGE_OUTPUT2 = "C:\\Users\\L\\Desktop\\表情\\picture\\generated_image2.png"
IMAGE_OUTPUT3 = "C:\\Users\\L\\Desktop\\表情\\picture\\generated_image3.png"
IMAGE_OUTPUT4 = "C:\\Users\\L\\Desktop\\表情\\picture\\generated_image4.png"
# 定义颜色
white = (255, 255, 255)
blue  = (0,191,255)
black = (0, 0, 0)
red   = (255, 0, 0)
green = (0, 255, 0)
# 定义文本
text_state = "待机中···"
text_title = "无"
text_story = ["你好"]

# 设置窗口大小
width, height = 1000, 600

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

# 定义录音参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 6

# 使用 os.chmod() 函数修改文件权限
new_permissions = 0o777
if os.path.exists(WAVE_INPUT):
    os.chmod(WAVE_INPUT, new_permissions)
if os.path.exists(WAVE_OUTPUT):
    os.chmod(WAVE_OUTPUT, new_permissions)
if os.path.exists(IMAGE_OUTPUT1):
    os.chmod(IMAGE_OUTPUT1, new_permissions)
if os.path.exists(IMAGE_OUTPUT2):
    os.chmod(IMAGE_OUTPUT2, new_permissions)
if os.path.exists(IMAGE_OUTPUT3):
    os.chmod(IMAGE_OUTPUT3, new_permissions)
if os.path.exists(IMAGE_OUTPUT4):
    os.chmod(IMAGE_OUTPUT4, new_permissions)

# 初始化文字摘要模型
summarizer = pipeline("summarization", model="fnlp/bart-large-chinese")
# 初始化图片生成模型
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "runwayml/stable-diffusion-v1-5"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
pipe = pipe.to(device)
# 初始化pygame和混音器
pygame.mixer.init()                    
p = pyaudio.PyAudio()                   
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("绘本")

# 函数：长文字分割翻译
def translate_long_text(text, from_lang='zh', to_lang='en'):
    def split_text(text, max_length=5000):
        chunks = []
        while len(text) > max_length:
            chunk = text[:max_length]
            chunks.append(chunk)
            text = text[max_length:]
        chunks.append(text)
        return chunks
    chunks = split_text(text)
    translated_text = ""
    for chunk in chunks:
        translated_text += ts.translate_text(chunk, from_language=from_lang, to_language=to_lang)
    return translated_text

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
        word_surface = font.render(word, True, color)
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

# 函数：生成四幅图片
def picture_produce(text):
        text_t = ""
        try :
            text_t = " ".jion(text)
        except:
            text_t = text
        print(text_t)
        start_time3 = time.time()
        length_text = len(text_t)
        if length_text < 4:
            raise ValueError("输入文本过短，无法分割为四部分")
        part_length = length_text // 4
        text_picture1 = text_t[0 : part_length]
        text_picture2 = text_t[part_length : part_length*2]
        text_picture3 = text_t[part_length*2 : part_length*3]
        text_picture4 = text_t[part_length*3 : length_text]
        print(text_picture1)
        print(text_picture2)
        summary1 = summarizer(text_picture1, max_length=60, min_length=10, do_sample=False)
        summary2 = summarizer(text_picture2, max_length=60, min_length=10, do_sample=False)
        summary3 = summarizer(text_picture3, max_length=60, min_length=10, do_sample=False)
        summary4 = summarizer(text_picture4, max_length=60, min_length=10, do_sample=False)
        translation1 = translate_long_text(summary1[0]['summary_text'])
        translation2 = translate_long_text(summary2[0]['summary_text'])
        translation3 = translate_long_text(summary3[0]['summary_text'])                                         
        translation4 = translate_long_text(summary4[0]['summary_text'])  
        image1 = pipe(translation1).images[0]
        image2 = pipe(translation2).images[0]
        image3 = pipe(translation3).images[0]
        image4 = pipe(translation4).images[0]
        image1.save(IMAGE_OUTPUT1)
        image2.save(IMAGE_OUTPUT2)
        image3.save(IMAGE_OUTPUT3)
        image4.save(IMAGE_OUTPUT4)
        end_time3 = time.time()
        run_time3 = end_time3 - start_time3
        print(f"图片生成时间: {run_time3} 秒")
        print("图片已生成！")                                         

# 函数：图片显示
def picture_desplay(picture_road, pos):
        picture_1 = pygame.image.load(picture_road)
        original_width, original_height = picture_1.get_size()
        f_p = round(250/original_width,2)
        picture_new = pygame.transform.scale(picture_1, (original_width * f_p, original_height * f_p))
        screen.blit(picture_new, pos)

def resample_audio(audio_data, original_sample_rate, target_sample_rate):
    number_of_samples = round(
        len(audio_data) * float(target_sample_rate) / original_sample_rate)
    resampled_audio = resample(audio_data, number_of_samples)
    return resampled_audio.astype(np.int16)

# 函数：音频格式转换pcm->wav
def pcm_to_wav(pcm_data, wav_file, sample_rate=16000, num_channels=1, sample_width=2):
    print(f"saved to file {wav_file}")
    with wave.open(wav_file, 'wb') as wav:
        wav.setnchannels(num_channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_data)

# 函数：发送音频
async def send_audio(client, audio_file_path: str):
    sample_rate = 16000
    duration_ms = 100
    samples_per_chunk = sample_rate * (duration_ms / 1000)
    bytes_per_sample = 2
    bytes_per_chunk = int(samples_per_chunk * bytes_per_sample)
    audio_data, original_sample_rate = sf.read(
        audio_file_path, dtype="int16")
    if original_sample_rate != sample_rate:
        audio_data = resample_audio(
            audio_data, original_sample_rate, sample_rate)
    audio_bytes = audio_data.tobytes()
    for i in range(0, len(audio_bytes), bytes_per_chunk):
        await asyncio.sleep((duration_ms - 10)/1000)
        chunk = audio_bytes[i: i + bytes_per_chunk]
        base64_audio = base64.b64encode(chunk).decode("utf-8")
        append_event = {
            "type": "input_audio_buffer.append",
            "audio": base64_audio
        }
        await client.send(json.dumps(append_event))
    commit_event = {
        "type": "input_audio_buffer.commit"
    }
    await client.send(json.dumps(commit_event))
    event = {
        "type": "response.create",
        "response": {
                "modalities": ["text", "audio"]
        }
    }
    await client.send(json.dumps(event))

# 函数：接收音频
async def receive_messages(client, save_file_name):
    global text_story
    audio_list = bytearray()
    while not client.closed:
        message = await client.recv()
        if message is None:
            continue
        event = json.loads(message)
        message_type = event.get("type")
        text_t = event.get("transcript")
        if message_type == "response.audio.delta":
            audio_bytes = base64.b64decode(event["delta"])
            audio_list.extend(audio_bytes)
            continue
        if message_type == 'response.done':
            pcm_to_wav(audio_list, save_file_name)
            break
        if message_type == 'response.audio_transcript.done':
            text_story = text_t
        continue

async def with_realtime(audio_file_path: str, save_file_name: str):
    ws_url = "wss://ai-gateway.vei.volces.com/v1/realtime?model=AG-voice-chat-agent"
    key = "sk-e5be6d02fcce48c29df7bb19e9c704f7qg326iho1ylbo639" # 修改为你的 key
    headers = {
        "Authorization": f"Bearer {key}",
    }
    async with websockets.connect(ws_url, extra_headers=headers) as client:
        session_msg = get_session_update_msg()
        await client.send(session_msg)
        # 语音录入
        print("麦克风中···")
        record_audio(audio_file_path)
        print("麦克风关闭！")
        await asyncio.gather(send_audio(client, audio_file_path),
                            receive_messages(client, save_file_name))
        await asyncio.sleep(0.5)

def get_session_update_msg():
    config = {
        "modalities": ["text", "audio"],
        "instructions": "你的名字叫豆包，你是一个一次只能讲520字以内的故事助手",
        "voice": "zh_female_tianmeixiaoyuan_moon_bigtts",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "tool_choice": "auto",
        "turn_detection": None,
        "temperature": 0.8,
    }
    event = {
        "type": "session.update",
        "session": config
    }
    return json.dumps(event)

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
            elif  button0_key == -1 and button2_key == -1:
                button0_key = 0
                button2_key = 0
                color_0     = green
                color_2     = green    
        elif  button1_drag and button0_key !=0 :
            if  button1_key == 0 :
                button1_key = 1
                color_1     = red
        elif  button2_drag and button0_key !=0 :
            if  button2_key == 0 :
                button2_key = 1
                color_2     = red
    if button0_key != 0 :    
        text_state = "运行中···"
    if button1_key == 1 :    
        text_state = "阅读中···"
    # 绘制背景
    screen.fill(black)  
    pygame.draw.rect(screen, white, (120,0,2,60))
    pygame.draw.rect(screen, white, (0,60,width,2))
    pygame.draw.rect(screen, white, (490,60,2,540))
    pygame.draw.rect(screen, white, (360,0,2,60))
    # 显示状态文本  
    blit_text1( 36 , text_state,( 135 , 12 ) )
    # 显示故事内容
    font1 = pygame.font.SysFont('SimHei', 20)
    blit_text2(screen, text_story, (5, 60), font1, 490)
    # 显示标题文本
    # blit_text1(20, text_title, (370, 5))
    # 绘制按钮
    pygame.draw.circle(screen, color_0, button0_pos, button_radius)
    pygame.draw.circle(screen, color_1, button1_pos, button_radius)
    pygame.draw.circle(screen, color_2, button2_pos, button_radius)
    # 图片显示
    if button2_key == -1 :
        picture_desplay(IMAGE_OUTPUT1,(500,70))
        picture_desplay(IMAGE_OUTPUT2,(500+250,70))
        picture_desplay(IMAGE_OUTPUT3,(500,70+250))
        picture_desplay(IMAGE_OUTPUT4,(500+250,70+250))
    # 更新屏幕显示
    pygame.display.flip()

    if button0_key == 1 :    #生成故事
        text_state = "运行中~"
        #生成故事
        start_time1 = time.time()
        asyncio.run(with_realtime(WAVE_INPUT, WAVE_OUTPUT))
        end_time1 = time.time()
        run_time1 = end_time1 - start_time1
        print(f"故事生成时长: {run_time1} 秒")
        print(text_story)
        button0_key = -1
    if button1_key == 1 :    #语音朗读
        start_time2 = time.time()
        pygame.mixer.music.load(WAVE_OUTPUT)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.5)
        end_time2 = time.time()
        run_time2 = end_time2 - start_time2
        print(f"阅读时长: {run_time2} 秒")
        button1_key = 0
        color_1     = green
    if button2_key == 1 :    #图片生成
        picture_produce(text_story)
        button2_key = -1
        color_2     = green

    # 控制帧率
    pygame.time.Clock().tick(60)



            
