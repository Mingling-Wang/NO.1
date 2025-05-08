# ********coding      :   utf-8
# ********create at   :   2025/04
# ********create by   :   wml
# ********Description :   ai-dialogue and interupt-dialogue
import pyaudio
import webrtcvad
import asyncio
import base64
import json
import numpy as np
import websockets
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VoiceProcessor:
    def __init__(self, api_key, format=pyaudio.paInt16, channels=1, rate=16000, play_rate=15000, chunk=320,
                 vad_mode=2, silence_frames_threshold=30):
        self.FORMAT = format
        self.CHANNELS = channels
        self.RATE = rate
        self.PLAY_RATE = play_rate
        self.CHUNK = chunk
        self.VAD_MODE = vad_mode
        self.SILENCE_FRAMES_THRESHOLD = silence_frames_threshold
        self.key = api_key
        self.p = pyaudio.PyAudio()
        self.vad = webrtcvad.Vad(self.VAD_MODE)
        self.input_stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
        self.output_stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.PLAY_RATE, output=True)
        self.is_speaking = False
        self.is_speaking_detect = False
        self.silence_frame_count = 0
        self.rounds_dialogue = 0
        self.audio_packet_queue = asyncio.Queue()
        self.conversation_head_KEY = 0
        self.send_state = 0
        self.detection_thread = None
        self.send_end_time = 0.0
        self.receive_start_time = 0.0
        self.is_playing = False

    async def play_audio_packets(self):
        self.is_playing = True
        while not self.audio_packet_queue.empty():
            try:
                if self.is_speaking:  # 检测到新的语音输入，停止播放
                    self.audio_packet_queue = asyncio.Queue()  # 清空队列
                    self.is_playing = False
                    break
                audio_packet = await self.audio_packet_queue.get()
                self.output_stream.write(audio_packet)
            except Exception as e:
                logging.error(f"播放音频包时出错: {e}")
        self.is_playing = False

    async def send_audio_stream(self, client):
        try:
            self.send_state = 0
            duration_ms = 150
            samples_per_chunk = self.RATE * (duration_ms / 1000)
            bytes_per_sample = 2
            bytes_per_chunk = int(samples_per_chunk * bytes_per_sample)
            while True:
                try:
                    data = self.input_stream.read(self.CHUNK)
                except Exception as e:
                    logging.error(f"读取音频输入流时出错: {e}")
                    break
                is_speech = self.vad.is_speech(data, self.RATE)
                if is_speech:
                    if not self.is_speaking:
                        if self.is_playing:  # 如果正在播放音频，停止播放
                            self.audio_packet_queue = asyncio.Queue()  # 清空队列
                            self.is_playing = False
                        self.is_speaking = True
                        logging.info("开始说话")
                        start_time0 = time.time()
                    audio_bytes = np.frombuffer(data, dtype=np.int16)
                    for i in range(0, len(audio_bytes), bytes_per_chunk):
                        chunk = audio_bytes[i: i + bytes_per_chunk]
                        base64_audio = base64.b64encode(chunk).decode("utf-8")
                        append_event = {
                            "type": "input_audio_buffer.append",
                            "audio": base64_audio
                        }
                        try:
                            await client.send(json.dumps(append_event))
                        except Exception as e:
                            logging.error(f"发送音频数据时出错: {e}")
                            break
                        await asyncio.sleep(0.01)
                else:
                    if self.is_speaking:
                        self.silence_frame_count += 1
                        if self.silence_frame_count >= self.SILENCE_FRAMES_THRESHOLD:
                            logging.info("结束说话")
                            start_time1 = time.time()
                            logging.info(f"！！记录人声的时长: {round(start_time1 - start_time0, 3)} 秒！！")
                            self.is_speaking = False
                            self.silence_frame_count = 0
                            commit_event = {
                                "type": "input_audio_buffer.commit"
                            }
                            try:
                                await client.send(json.dumps(commit_event))
                            except Exception as e:
                                logging.error(f"发送提交事件时出错: {e}")
                                break
                            self.send_state = 1
                            event = {
                                "type": "response.create",
                                "response": {
                                    "modalities": ["audio"]
                                }
                            }
                            self.send_end_time = time.time()
                            try:
                                await client.send(json.dumps(event))
                            except Exception as e:
                                logging.error(f"发送响应创建事件时出错: {e}")
                                break
                            end_time1 = time.time()
                            logging.info(f"！！发送音频的时长: {round(end_time1 - start_time1, 4)} 秒！！")
                            break
        except Exception as e:
            logging.error(f"发送音频时出错: {e}")

    async def receive_read_messages(self, client):
        num_frames = 2
        frame_count = 0
        time_KEY = 1
        frame_start_time = 0.0
        try:
            while not client.closed :
                try:
                    message = await client.recv()
                except Exception as e:
                    logging.error(f"接收消息时网络出错: {e}")
                    break
                if message is None:
                    continue
                event = json.loads(message)
                message_type = event.get("type")
                if message_type == "response.audio.delta":
                    if frame_count == 0:
                        frame_start_time = time.time()
                    try:
                        audio_bytes = base64.b64decode(event["delta"])
                    except Exception as e:
                        logging.error(f"解码音频数据时出错: {e}")
                        continue
                    await self.audio_packet_queue.put(audio_bytes)
                    if time_KEY:
                        frame_count += 1
                        if frame_count == num_frames:
                            time_KEY = 0
                            end_time = time.time()
                            self.receive_start_time = time.time()
                            frame_run_time = round(end_time - frame_start_time, 3)
                            logging.info(f"接收{num_frames}帧音频的时长: {frame_run_time} 秒")
                            logging.info(f"大模型处理时间: {round(self.receive_start_time - self.send_end_time - frame_run_time, 3)} 秒\n")
                            await self.play_audio_packets()
                    else:
                        await self.play_audio_packets()
                elif message_type == 'response.done':
                    self.send_state = 0
                    break
        except Exception as e:
            logging.error(f"接收消息时出错: {e}")

    def get_session_update_msg(self):
        config = {
            "modalities": ["text", "audio"],
            "instructions": "你的名字叫豆包，你是一个智能语音对话助手，回答尽量简洁",
            "voice": "zh_female_tianmeixiaoyuan_moon_bigtts",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "tool_choice": "auto",
            "turn_detection": None,
            "temperature": 0.8
        }
        event = {
            "type": "session.update",
            "session": config
        }
        return json.dumps(event)

    async def with_realtime(self):
        try:
            t1 = time.time()
            ws_url = "wss://ai-gateway.vei.volces.com/v1/realtime?model=AG-voice-chat-agent"
            headers = {
                "Authorization": f"Bearer {self.key}"
            }
            async with websockets.connect(ws_url, extra_headers=headers) as client:
                if self.conversation_head_KEY == 0:
                    session_msg = self.get_session_update_msg()
                    await client.send(session_msg)
                    self.conversation_head_KEY = 1
                t2 = time.time()
                logging.info(f"与大模型建立连接的时长: {round(t2 - t1, 3)} 秒")
                tasks = [
                    self.send_audio_stream(client),
                    self.receive_read_messages(client)
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
        except websockets.exceptions.ConnectionClosedError as e:
            logging.error(f"WebSocket连接意外关闭: {e}")
        except websockets.exceptions.InvalidStatusCode as e:
            logging.error(f"收到来自服务器的无效状态码: {e}")
        except Exception as e:
            logging.error(f"实时处理音频时出错: {e}")


    async def start_detection(self):
        await self.with_realtime()

    def __del__(self):
        try:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.p.terminate()
        except Exception as e:
            logging.error(f"关闭音频流和PyAudio实例时出错: {e}")


async def main():
    api_key = "sk-e5be6d02fcce48c29df7bb19e9c704f7qg326iho1ylbo639"
    processor = VoiceProcessor(api_key)
    while True:
        await processor.start_detection()


if __name__ == "__main__":
    asyncio.run(main())