import pyaudio
import webrtcvad
import wave
import asyncio
import base64
import json
import numpy as np
import soundfile as sf
from scipy.signal import resample
import websockets
import pygame
import time
import os
import threading
import logging
import queue
import sys

conversation_start_KET = 0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VoiceDetector:
    def __init__(self, save_path, format=pyaudio.paInt16, channels=1, rate=16000,
                 chunk=320, vad_mode=3, silence_frames_threshold=40):
        self.FORMAT = format
        self.CHANNELS = channels
        self.RATE = rate
        self.CHUNK = chunk
        self.VAD_MODE = vad_mode
        self.SILENCE_FRAMES_THRESHOLD = silence_frames_threshold
        self.p = pyaudio.PyAudio()
        self.vad = webrtcvad.Vad(self.VAD_MODE)
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        self.save_path = save_path
        self.is_speaking = False
        self.speech_frames = []
        self.silence_frame_count = 0
        self.file_queue = queue.Queue()
        self.file_index = 0
        self.lock = threading.Lock()
        pygame.mixer.init()
        self.mixer_lock = threading.Lock()

    def save_audio(self, frames, filename):
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))

    def start_detection(self, stop_event):
        logging.info("开始语音检测，按 Ctrl+C 停止...")
        try:
            while not stop_event.is_set():
                data = self.stream.read(self.CHUNK)
                is_speech = self.vad.is_speech(data, self.RATE)
                if is_speech:
                    with self.mixer_lock:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.stop()
                    if not self.is_speaking:
                        self.is_speaking = True
                        self.speech_frames = [data]
                        self.silence_frame_count = 0
                    else:
                        self.speech_frames.append(data)
                        self.silence_frame_count = 0
                else:
                    if self.is_speaking:
                        self.silence_frame_count += 1
                        self.speech_frames.append(data)
                        if self.silence_frame_count >= self.SILENCE_FRAMES_THRESHOLD:
                            with self.lock:
                                self.file_index += 1
                                filename = f"{self.save_path}5_audio_{self.file_index}.wav"
                                self.save_audio(self.speech_frames, filename)
                                logging.info(f"保存语音文件: {filename}")
                                self.file_queue.put(filename)
                            self.is_speaking = False
                            self.speech_frames = []
                            self.silence_frame_count = 0
        except KeyboardInterrupt:
            logging.info("停止语音检测")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

class VoiceConversation:
    def __init__(self, api_key):
        self.key = api_key
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.RECORD_SECONDS = 6
        pygame.mixer.init()
        self.p = pyaudio.PyAudio()
        self.text_story = ""

    def resample_audio(self, audio_data, original_sample_rate):
        try:
            number_of_samples = round(
                len(audio_data) * float(self.RATE) / original_sample_rate)
            resampled_audio = resample(audio_data, number_of_samples)
            return resampled_audio.astype(np.int16)
        except Exception as e:
            logging.error(f"重采样音频时出错: {e}")
            return audio_data

    def pcm_to_wav(self, pcm_data, wav_file):
        try:
            logging.info(f"saved to file {wav_file}")
            with wave.open(wav_file, 'wb') as wav:
                wav.setnchannels(self.CHANNELS)
                wav.setsampwidth(2)
                wav.setframerate(self.RATE)
                wav.writeframes(pcm_data)
        except Exception as e:
            logging.error(f"将PCM转换为WAV时出错: {e}")

    async def send_audio(self, client, audio_file_path):
        try:
            start_time2 = time.time()
            sample_rate = 16000
            duration_ms = 100
            samples_per_chunk = sample_rate * (duration_ms / 1000)
            bytes_per_sample = 2
            bytes_per_chunk = int(samples_per_chunk * bytes_per_sample)
            audio_data, original_sample_rate = sf.read(
                audio_file_path, dtype="int16")
            if original_sample_rate != sample_rate:
                audio_data = self.resample_audio(
                    audio_data, original_sample_rate)
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
            end_time2 = time.time()
            run_time2 = round(end_time2 - start_time2, 3)
            print(f"！！发送音频的时间: {run_time2} 秒！！")
        except Exception as e:
            logging.error(f"发送音频时出错: {e}")

    async def receive_messages(self, client, save_file_name):
        audio_list = bytearray()
        try:
            start_time3 = time.time()
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
                    self.pcm_to_wav(audio_list, save_file_name)
                    break
                if message_type == 'response.audio_transcript.done':
                    self.text_story = text_t
                    logging.info(f"text_story:::{self.text_story}")
            end_time3 = time.time()
            run_time3 = round(end_time3 - start_time3, 3)
            print(f"！！发送到接收回应的时间: {run_time3} 秒！！")
        except Exception as e:
            logging.error(f"接收消息时出错: {e}")

    def get_session_update_msg(self):
        config = {
            "modalities": ["text", "audio"],
            "instructions": "你的名字叫豆包，你是一个智能语音对话助手",
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

    async def interupt_message(self, client):
        event = {
            "type": "response.cancel"
        }
        try:
            await client.send(json.dumps(event))
            await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"发送取消响应时出错: {e}")

    async def with_realtime(self, audio_file_path, save_file_name):
        global conversation_start_KET
        try:
            # 修改文件权限
            new_permissions = 0o777
            os.chmod(audio_file_path, new_permissions)
            os.chmod(save_file_name, new_permissions)
            ws_url = "wss://ai-gateway.vei.volces.com/v1/realtime?model=AG-voice-chat-agent"
            headers = {
                "Authorization": f"Bearer {self.key}",
            }
            async with websockets.connect(ws_url, extra_headers=headers) as client:
                if conversation_start_KET == 0:
                    session_msg = self.get_session_update_msg()
                    await client.send(session_msg)
                    conversation_start_KET = 1
                else:
                    await self.interupt_message(client)
                await asyncio.gather(
                    self.send_audio(client, audio_file_path),
                    self.receive_messages(client, save_file_name)
                )
                await asyncio.sleep(0.1)
                logging.info("回应中~")
                await asyncio.sleep(0.1)
                print(f"save_file_name-save_file_name:{save_file_name}")
                with threading.Lock():
                    pygame.mixer.music.load(save_file_name)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                logging.info("回应结束！")
        except Exception as e:
            logging.error(f"实时处理音频时出错: {e}")

    def process_audio(self, path_in, path_out):
        asyncio.run(self.with_realtime(path_in, path_out))

def main():
    audio_recording_path = "C:\\Users\\L\\Desktop\\表情\\audio\\"
    wave_output = "C:\\Users\\L\\Desktop\\表情\\audio\\"
    api_key = "sk-e5be6d02fcce48c29df7bb19e9c704f7qg326iho1ylbo639"
    stop_event = threading.Event()
    detector = VoiceDetector(audio_recording_path)
    conversation = VoiceConversation(api_key)
    detection_thread = threading.Thread(target=detector.start_detection, args=(stop_event,))
    detection_thread.start()
    last_file_index = 0
    conversation_thread = None
    try:
        while True:
            with detector.lock:
                # if detector.file_index > 3:           # 用对话轮次打断程序
                #     stop_event.set()
                #     if conversation_thread:
                #         conversation_thread.join()
                #     detection_thread.join()
                #     break
                if detector.file_index > last_file_index:
                    print(last_file_index)
                    audio_file_path = f"{audio_recording_path}5_audio_{detector.file_index}.wav"
                    audio_out_path = f"{wave_output}what_you_receive{detector.file_index}.wav"
                    conversation_thread = threading.Thread(target=conversation.process_audio, args=(audio_file_path, audio_out_path))
                    conversation_thread.start()
                    last_file_index = detector.file_index
            time.sleep(0.6)
    except KeyboardInterrupt:
        stop_event.set()
        if conversation_thread:
            conversation_thread.join()
        detection_thread.join()
    finally:
        pygame.mixer.quit()

if __name__ == "__main__":
    main()