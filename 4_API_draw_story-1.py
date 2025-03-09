import requests
import json
import uuid
import re

YOUR_BOT_ID = "7478702234465779749"
YOUR_COZE_TOKEN = "pat_FQ6Oh7ruUwOM7c0FH8emVhusI9Un0KJ6djDvQC7AJSU1q6kd9uuekoLCRx5lljfA"
text_all   = []
text_story = []
text_title = "小兔子的勇敢冒险"
image_url  = []
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
            'stream': True,  # 启用流式返回
            'auto_save_history': True, # 自动保存历史记录
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

if __name__ == '__main__':
    chat_bot = ChatBot()
    chat_bot.input_value = text_title
    chat_bot.send_message()
    image_url = filter_pic(text_all)
    text_story = filter_text(text_all)
    print(text_all)
    for index, url in enumerate(image_url):
        save_path = f"C:\\Users\\L\\Desktop\\表情\\picture\\image{index + 1}.png"
        download_image(url, save_path)
    print(f"故事内容:{text_story}")
    print(f"图片网址:{image_url}")
    pass