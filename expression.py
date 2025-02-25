import pygame
import sys
import time

# 初始化pygame
pygame.init()
# 设置窗口大小
width, height = 1000, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("表情显示")

# 定义颜色
white = (255, 255, 255)
blue  = (0,191,255)
black = (0, 0, 0)
red   = (255, 0, 0)
green   = (0, 255, 0)

# 表情参数
face_length  = 3*140
face_width   = 2*140
mouth_radius = 16
# 定义嘴的参数
circle_x = 320
circle_y = 240
circle_radius = 5
# 眨眼参数
blink_duration = 0.2  # 眨眼持续时间（秒）
blink_interval = 1    # 两次眨眼间隔时间（秒）
last_blink_time = time.time()
is_blinking = False
eye_x = 320
eye_y = 240
eye_type = 1

# 定义按钮
button_radius = 16  # 按钮的大小
# 定义按钮0的参数,控制嘴的大小
button_x = 40
button_pos = (button_x, circle_y)
button_range = 100  # 按钮的活动范围
# 定义按钮1的参数,控制嘴的大小
button1_x = 100
button1_pos = (button1_x, eye_y)
button1_range = 100  # 按钮的活动范围
# 定义按钮2的参数,控制嘴的大小
button2_x = 160
button2_y = 270
button2_key = 0
button2_pos = (button2_x, button2_y)

# 加载图片
mouth = pygame.image.load(r"C:\Users\L\Desktop\表情\picture\1.jpeg")
eye_open1 = pygame.image.load(r"C:\Users\L\Desktop\表情\picture\4.jpeg")
eye_open2_part = pygame.image.load(r"C:\Users\L\Desktop\表情\picture\5.jpeg")
eye_open0 = pygame.image.load(r"C:\Users\L\Desktop\表情\picture\6.jpeg")
eye_open2 = pygame.image.load(r"C:\Users\L\Desktop\表情\picture\7.jpeg")
eye_closed = pygame.image.load(r"C:\Users\L\Desktop\表情\picture\2.jpeg")

# 眨眼参数
blink_duration = 0.2  # 眨眼持续时间（秒）
blink_interval = 1.0  # 两次眨眼间隔时间（秒）
last_blink_time = time.time()

running = True
button_drag  = False
button1_drag = False
button2_drag = False
is_blinking = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if (button_pos[0] - button_radius < pygame.mouse.get_pos()[0] < button_pos[0] + button_radius and
                button_pos[1] - button_radius < pygame.mouse.get_pos()[1] < button_pos[1] + button_radius):
                button_drag = True
            elif (button1_pos[0] - button_radius < pygame.mouse.get_pos()[0] < button1_pos[0] + button_radius and
                button1_pos[1] - button_radius < pygame.mouse.get_pos()[1] < button1_pos[1] + button_radius):
                button1_drag = True
            elif (((mouse_x - button2_pos[0]) ** 2 + (mouse_y - button2_pos[1]) ** 2) ** 0.5<= button_radius):
                button2_drag = True
        elif event.type == pygame.MOUSEBUTTONUP:
            button_drag = False
            button1_drag = False
            button2_drag = False
        if  button_drag:
            # 鼠标移动时更新按钮0位置，并限制活动范围
            new_x = 40
            new_y = max(circle_y - button_range, min(circle_y + button_range, pygame.mouse.get_pos()[1]))
            button_pos = (new_x, new_y)
            circle_radius = abs(new_y - circle_y - button_range)//20
            if(circle_radius == 0):
                circle_radius = 0.9
        elif  button1_drag:
            # 鼠标移动时更新按钮1位置，并限制活动范围
            new1_x = 100
            new1_y = max(eye_y - button_range, min(eye_y + button1_range, pygame.mouse.get_pos()[1]))
            button1_pos = (new1_x, new1_y)
            eye_type = abs(new1_y - eye_y - button_range//2*3)//100
        elif  button2_drag:
            # 鼠标移动时更新按钮2位置
            if button2_y == 270 and button2_key ==0 :
                button2_y = 210
            elif button2_y == 210 and button2_key ==1:
                button2_y = 270
            button2_key = not button2_key
            button2_x = 160
            button2_pos = (button2_x, button2_y)
            
    # 获取当前时间
    current_time = time.time()

    # 检查是否需要眨眼
    if button2_key == 1 :
        if current_time - last_blink_time > blink_interval:
            is_blinking = True
            last_blink_time = current_time
    elif button2_key == 0 :
        is_blinking = False
    # 绘制背景
    screen.fill(black)  # 用黑色填充背景

    # # 设置字体和大小
    # font = pygame.font.Font(None, 72)  # 使用默认字体，大小为72
    # # 渲染数字为图像
    # number_text = font.render(str(button2_key), True, (255, 255, 255))  # 白色文字
    # number_rect = number_text.get_rect(center=(100,100))  # 居中显示
    # # 将数字绘制到屏幕上
    # screen.blit(number_text, number_rect)

    # 绘制表情
    # 画脸
    pygame.draw.rect(screen, white, (width//2-face_length//2, height//2-face_width//2, face_length, face_width),5)
    if is_blinking:
        # 显示闭眼图片
        screen.blit(eye_closed, (width // 2 + 50, height // 2 - 50))
        screen.blit(eye_closed, (width // 2 - 150, height // 2 - 50))
        if current_time - last_blink_time > blink_duration:
            is_blinking = False
    else:
        # 显示睁眼图片
        if eye_type == 0:
            screen.blit(eye_open0, (width // 2 + 50, height // 2 - 50))
            screen.blit(eye_open0, (width // 2 - 150,  height // 2 - 50))
        elif eye_type == 1:
            screen.blit(eye_open1, (width // 2 + 50, height // 2 - 100))
            screen.blit(eye_open1, (width // 2 - 150,  height // 2 - 100))
        elif eye_type == 2:
            screen.blit(eye_open2, (width // 2 + 50, height // 2 - 100))
            screen.blit(eye_open2, (width // 2 - 150,  height // 2 - 100))
            screen.blit(eye_open2_part, (width // 2 + 70, height // 2 - 20))
            screen.blit(eye_open2_part, (width // 2 - 130,  height // 2 - 20))

    # 比例缩放嘴的图片
    original_width, original_height = mouth.get_size()
    mouth_image = pygame.transform.scale(mouth, (original_width // circle_radius, original_height // circle_radius))
    # 显示嘴的图片
    screen.blit(mouth_image, (width // 2 - mouth_image.get_width() // 2, 370 - mouth_image.get_height() // 2))

    # 绘制按钮
    pygame.draw.circle(screen, white, button_pos, button_radius)
    pygame.draw.rect(screen, white, ( button_x-16,circle_y-button_range, button_radius*2, button_range*2),2)
    pygame.draw.circle(screen, blue, button1_pos, button_radius)
    pygame.draw.rect(screen, white, ( button1_x-16,circle_y-button_range, button_radius*2, button_range*2),2)
    pygame.draw.circle(screen, green, button2_pos, button_radius)
    pygame.draw.rect(screen, white, ( button2_x-16,circle_y-button_range+50, button_radius*2, button_range),2)
    # 更新屏幕显示
    pygame.display.flip()

    # 控制帧率
    pygame.time.Clock().tick(60)

