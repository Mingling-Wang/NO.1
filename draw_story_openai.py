import asyncio
import base64
import json
import wave
import numpy as np
import soundfile as sf
from scipy.signal import resample
import websockets
import pygame
import time
import pyaudio
import os
import openai
import requests

# 设置 OpenAI API 密钥
openai.api_key = "YOUR_OPENAI_API_KEY"

WAVE_INPUT = "C:\\Users\\L\\Desktop\\表情\\audio\\what_you_sad_story.wav"
WAVE_OUTPUT = "C:\\Users\\L\\Desktop\\表情\\audio\\what_you_receive_story.wav"
IMAGE_OUTPUT = "C:\\Users\\L\\Desktop\\表情\\image\\generated_image.png"

# 定义文件路径
file_path = 'test_file.txt'

# 使用 os.chmod() 函数修改文件权限
new_permissions = 0o777
if os.path.exists(WAVE_INPUT):
    os.chmod(WAVE_INPUT, new_permissions)
if os.path.exists(WAVE_OUTPUT):
    os.chmod(WAVE_OUTPUT, new_permissions)

# 录音参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5

# 初始化 pygame 混音器
pygame.mixer.init()
# 初始化 PyAudio
p = pyaudio.PyAudio()

# 创建录音函数
def record_audio(filename):
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        print("麦克风中~")
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        print("麦克风关闭！")
        stream.stop_stream()
        stream.close()
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
    except Exception as e:
        print(f"录音时发生错误: {e}")

def resample_audio(audio_data, original_sample_rate, target_sample_rate):
    number_of_samples = round(
        len(audio_data) * float(target_sample_rate) / original_sample_rate)
    resampled_audio = resample(audio_data, number_of_samples)
    return resampled_audio.astype(np.int16)

def pcm_to_wav(pcm_data, wav_file, sample_rate=16000, num_channels=1, sample_width=2):
    print(f"saved to file {wav_file}")
    try:
        with wave.open(wav_file, 'wb') as wav:
            wav.setnchannels(num_channels)
            wav.setsampwidth(sample_width)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm_data)
    except Exception as e:
        print(f"保存音频文件时发生错误: {e}")

async def send_audio(client, audio_file_path: str):
    try:
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
            await asyncio.sleep((duration_ms - 10) / 1000)
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
    except Exception as e:
        print(f"发送音频时发生错误: {e}")

async def receive_messages(client, save_file_name):
    audio_list = bytearray()
    text_response = ""
    try:
        while not client.closed:
            message = await client.recv()
            if message is None:
                continue
            event = json.loads(message)
            message_type = event.get("type")
            if message_type == "response.audio.delta":
                audio_bytes = base64.b64decode(event["delta"])
                audio_list.extend(audio_bytes)
            elif message_type == "response.text.delta":
                text_response += event["delta"]
            elif message_type == 'response.done':
                pcm_to_wav(audio_list, save_file_name)
                # 根据文本响应生成图片
                generate_image(text_response)
                break
    except Exception as e:
        print(f"接收消息时发生错误: {e}")

def generate_image(prompt):
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        img_data = requests.get(image_url).content
        with open(IMAGE_OUTPUT, 'wb') as handler:
            handler.write(img_data)
        print(f"图片已保存到 {IMAGE_OUTPUT}")
    except Exception as e:
        print(f"生成图片时发生错误: {e}")

def get_session_update_msg():
    config = {
        "modalities": ["text", "audio"],
        "instructions": "你的名字叫小爱同学，你是一个智能助手",
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
        record_audio(audio_file_path)
        await asyncio.gather(send_audio(client, audio_file_path),
                                receive_messages(client, save_file_name))
        await asyncio.sleep(0.5)
        # 收听响应
        print("回应中~")
        pygame.mixer.music.load(save_file_name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.5)
        print("回应结束！")


if __name__ == "__main__":
    try:
        asyncio.run(with_realtime(WAVE_INPUT, WAVE_OUTPUT))
    finally:
        p.terminate()
        pygame.mixer.quit()