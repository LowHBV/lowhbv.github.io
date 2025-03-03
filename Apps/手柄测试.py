import ctypes
import pygame
import time
import threading
import math
import multiprocessing


# 锁定键盘布局为英文
def set_keyboard_layout():
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    # 0x0409 是英语（美国）的语言代码
    english_layout = 0x04090409  # 英语（美国）的键盘布局标识符
    user32.LoadKeyboardLayoutW('00000409', 1)
    user32.ActivateKeyboardLayout(english_layout, 1)


# 调用锁定键盘布局函数
set_keyboard_layout()

# 初始化pygame的所有模块
pygame.init()

# 初始化字体，使用支持汉字的字体文件
pygame.font.init()
font_path = r"C:\Windows\Fonts\msyh.ttc"  # 请确保路径和字体文件正确

# 初始化手柄
pygame.joystick.init()
joystick_count = pygame.joystick.get_count()

# 按键编号与按键名称的映射
button_names = {
    0: "A",
    1: "B",
    2: "X",
    3: "Y",
    4: "LB",
    5: "RB",
    6: "Back",
    7: "Start",
    8: "LThumb",
    9: "RThumb"
}


# 手柄震动线程函数
def vibrate(joystick, strength_var, stop_event):
    while not stop_event.is_set():
        strength = strength_var.value
        joystick.rumble(strength, strength, 1000)  # 持续震动1秒
        time.sleep(1)
    joystick.rumble(0, 0, 0)  # 停止震动


# 手柄窗口函数
def joystick_window(joystick_index, start_event):
    pygame.init()
    joystick = pygame.joystick.Joystick(joystick_index)
    joystick.init()
    joystick_name = joystick.get_name()

    # 创建一个窗口来捕获键盘事件
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption(joystick_name)
    font = pygame.font.Font(font_path, 20)

    vibration_strength = multiprocessing.Value('d', 0.5)  # 震动强度初始值
    is_vibrating = False  # 震动状态标志
    stop_event = threading.Event()  # 用于停止震动线程

    # 记录按键按下时间
    button_press_time = {}

    # 记录要显示的文本信息
    text_output = ""
    left_stick_text = ""
    right_stick_text = ""
    lt_value = 0
    rt_value = 0
    left_stick_pos = (0, 0)
    right_stick_pos = (0, 0)
    dpad_text = ""

    # 用于存储拖尾位置的列表
    left_trail = []
    right_trail = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and not is_vibrating:
                    text_output = "开始震动"
                    is_vibrating = True
                    stop_event.clear()
                    threading.Thread(target=vibrate, args=(joystick, vibration_strength, stop_event)).start()
                elif event.key == pygame.K_e and is_vibrating:
                    text_output = "停止震动"
                    is_vibrating = False
                    stop_event.set()  # 停止震动
                elif event.key == pygame.K_s and is_vibrating:
                    with vibration_strength.get_lock():
                        vibration_strength.value = max(0, vibration_strength.value - 0.1)  # 强度不能小于0
                    text_output = f"震动力度减少到: {vibration_strength.value:.1f}"
                elif event.key == pygame.K_w and is_vibrating:
                    with vibration_strength.get_lock():
                        vibration_strength.value = min(1, vibration_strength.value + 0.1)  # 强度不能大于1
                    text_output = f"震动力度增加到: {vibration_strength.value:.1f}"
                elif event.key == pygame.K_o:
                    running = False
                elif event.key == pygame.K_r:
                    start_event.set()  # 触发所有手柄震动
            elif event.type == pygame.JOYBUTTONDOWN:
                button_press_time[event.button] = time.time()
            elif event.type == pygame.JOYBUTTONUP:
                if event.button in button_press_time:
                    press_duration = time.time() - button_press_time[event.button]
                    cps = 1 / press_duration if press_duration > 0 else 0
                    button_name = button_names.get(event.button, f"Button {event.button}")
                    text_output = (f"按键名字 : {button_name} "
                                   f" 编号 : {event.button} "
                                   f" 按压时间 : {press_duration:.2f}秒 "
                                   f" 每秒点击速度 (CPS) : {cps:.2f}")
                    del button_press_time[event.button]
            elif event.type == pygame.JOYAXISMOTION:
                # 读取左摇杆的X轴和Y轴
                if event.axis == 0 or event.axis == 1:
                    lx = joystick.get_axis(0)
                    ly = joystick.get_axis(1)
                    left_stick_pos = (lx, ly)
                    angle = math.degrees(math.atan2(-ly, lx)) % 360
                    left_stick_text = f"左摇杆 : 角度 : {angle:.2f}"
                    # 更新拖尾位置
                    left_trail.append(left_stick_pos)
                    if len(left_trail) > 20:  # 限制拖尾长度
                        left_trail.pop(0)
                # 读取右摇杆的X轴和Y轴
                elif event.axis == 2 or event.axis == 3:
                    rx = joystick.get_axis(2)
                    ry = joystick.get_axis(3)
                    right_stick_pos = (rx, ry)
                    angle = math.degrees(math.atan2(-ry, rx)) % 360
                    right_stick_text = f"右摇杆 : 角度 : {angle:.2f}"
                    # 更新拖尾位置
                    right_trail.append(right_stick_pos)
                    if len(right_trail) > 20:  # 限制拖尾长度
                        right_trail.pop(0)
                # 读取LT RT的值
                elif event.axis == 4:  # 假设LT是轴4
                    lt_value = (joystick.get_axis(4) + 1) / 2  # 归一化到0到1之间
                elif event.axis == 5:  # 假设RT是轴5
                    rt_value = (joystick.get_axis(5) + 1) / 2  # 归一化到0到1之间

                # 读取十字键（D-pad）的值
                elif event.axis == 6 or event.axis == 7:
                    dpad_x = joystick.get_axis(6)
                    dpad_y = joystick.get_axis(7)
                    dpad_text = f"十字键: X轴: {dpad_x:.2f}, Y轴: {dpad_y:.2f}"

        # 清屏
        screen.fill((0, 0, 0))

        # 在窗口左上角显示手柄名字
        joystick_name_surface = font.render(f"手柄名字: {joystick_name}", True, (255, 255, 255))
        screen.blit(joystick_name_surface, (10, 10))

        # 在手柄名字下面显示连接方式
        connection_info_surface = font.render(f"连接方式: {joystick.get_guid()}", True, (255, 255, 255))
        screen.blit(connection_info_surface, (10, 40))

        # 在窗口右上角显示“震动中”标志
        if is_vibrating:
            vibrating_surface = font.render("震动中", True, (255, 0, 0))
            screen.blit(vibrating_surface, (screen.get_width() - vibrating_surface.get_width() - 10, 10))
            # 显示当前震动力度
            vibration_strength_surface = font.render(f"震动力度: {vibration_strength.value:.1f}", True, (255, 255, 255))
            screen.blit(vibration_strength_surface,
                        (screen.get_width() - vibration_strength_surface.get_width() - 10, 40))

        # 绘制左摇杆圆盘和位置点
        center_left = (200, 200)  # 更新圆盘位置
        radius = 100  # 设置较小的圆盘半径
        point_radius = 3  # 设置摇杆点和中心白点的半径
        pygame.draw.circle(screen, (255, 255, 255), center_left, radius, 2)  # 绘制较小的圆盘
        pygame.draw.circle(screen, (255, 255, 255), center_left, point_radius)  # 中心白点
        left_stick_point = (
        center_left[0] + int(left_stick_pos[0] * radius), center_left[1] + int(left_stick_pos[1] * radius))

        # 绘制左摇杆拖尾
        for pos in left_trail:
            trail_point = (center_left[0] + int(pos[0] * radius), center_left[1] + int(pos[1] * radius))
            pygame.draw.circle(screen, (0, 255, 255), trail_point, point_radius // 2)  # 青色拖尾

        # 绘制左摇杆白点和位置点之间的连接线
        pygame.draw.line(screen, (255, 255, 255), center_left, left_stick_point, 1)

        # 计算左摇杆点和中心白点之间的距离
        distance_left = math.sqrt(
            (left_stick_point[0] - center_left[0]) ** 2 + (left_stick_point[1] - center_left[1]) ** 2)
        if distance_left < point_radius * 2:
            pygame.draw.circle(screen, (255, 0, 0), left_stick_point, point_radius)
        else:
            pygame.draw.circle(screen, (0, 255, 0), left_stick_point, point_radius)

        # 绘制右摇杆圆盘和位置点
        center_right = (600, 200)  # 更新圆盘位置
        pygame.draw.circle(screen, (255, 255, 255), center_right, radius, 2)  # 绘制较小的圆盘
        pygame.draw.circle(screen, (255, 255, 255), center_right, point_radius)  # 中心白点
        right_stick_point = (
        center_right[0] + int(right_stick_pos[0] * radius), center_right[1] + int(right_stick_pos[1] * radius))

        # 绘制右摇杆拖尾
        for pos in right_trail:
            trail_point = (center_right[0] + int(pos[0] * radius), center_right[1] + int(pos[1] * radius))
            pygame.draw.circle(screen, (0, 255, 255), trail_point, point_radius // 2)  # 青色拖尾

        # 绘制右摇杆白点和位置点之间的连接线
        pygame.draw.line(screen, (255, 255, 255), center_right, right_stick_point, 1)

        # 计算右摇杆点和中心白点之间的距离
        distance_right = math.sqrt(
            (right_stick_point[0] - center_right[0]) ** 2 + (right_stick_point[1] - center_right[1]) ** 2)
        if distance_right < point_radius * 2:
            pygame.draw.circle(screen, (255, 0, 0), right_stick_point, point_radius)
        else:
            pygame.draw.circle(screen, (0, 255, 0), right_stick_point, point_radius)

        # 在圆盘底部标注X和Y轴
        x_axis_font = pygame.font.Font(font_path, 18)
        y_axis_font = pygame.font.Font(font_path, 18)
        left_x_axis_surface = x_axis_font.render(f"X轴: {left_stick_pos[0]:.2f}", True, (255, 255, 255))
        left_y_axis_surface = y_axis_font.render(f"Y轴: {left_stick_pos[1]:.2f}", True, (255, 255, 255))
        right_x_axis_surface = x_axis_font.render(f"X轴: {right_stick_pos[0]:.2f}", True, (255, 255, 255))
        right_y_axis_surface = y_axis_font.render(f"Y轴: {right_stick_pos[1]:.2f}", True, (255, 255, 255))
        screen.blit(left_x_axis_surface, (center_left[0] - 50, center_left[1] + radius + 10))
        screen.blit(left_y_axis_surface, (center_left[0] + radius + 10, center_left[1] - 10))
        screen.blit(right_x_axis_surface, (center_right[0] - 50, center_right[1] + radius + 10))
        screen.blit(right_y_axis_surface, (center_right[0] + radius + 10, center_right[1] - 10))

        # 渲染摇杆文本
        y_offset = 350
        left_stick_surface = font.render(left_stick_text, True, (255, 255, 255))
        screen.blit(left_stick_surface, (10, y_offset))
        y_offset += 30
        right_stick_surface = font.render(right_stick_text, True, (255, 255, 255))
        screen.blit(right_stick_surface, (10, y_offset))
        y_offset += 30

        # 渲染十字键文本
        dpad_surface = font.render(dpad_text, True, (255, 255, 255))
        screen.blit(dpad_surface, (10, y_offset))
        y_offset += 30

        # 渲染LT RT进度条
        pygame.draw.rect(screen, (255, 0, 0), (10, y_offset, 200, 20))  # LT背景条
        pygame.draw.rect(screen, (0, 255, 0), (10, y_offset, int(200 * lt_value), 20))  # LT进度条
        lt_text_surface = font.render(f"LT : {lt_value:.2f}", True, (255, 255, 255))
        screen.blit(lt_text_surface, (220, y_offset))
        y_offset += 30

        pygame.draw.rect(screen, (255, 0, 0), (10, y_offset, 200, 20))  # RT背景条
        pygame.draw.rect(screen, (0, 255, 0), (10, y_offset, int(200 * rt_value), 20))  # RT进度条
        rt_text_surface = font.render(f"RT : {rt_value:.2f}", True, (255, 255, 255))
        screen.blit(rt_text_surface, (220, y_offset))
        y_offset += 30

        # 渲染按键日志
        text_surface = font.render(text_output, True, (255, 255, 255))
        screen.blit(text_surface, (10, y_offset))

        pygame.display.flip()

    # 退出pygame
    pygame.quit()
    stop_event.set()  # 确保退出时停止震动


# 控制所有手柄震动的函数
def all_joysticks_vibrate(start_event):
    pygame.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(joystick_count)]
    for joystick in joysticks:
        joystick.init()

    def vibrate_all():
        for joystick in joysticks:
            joystick.rumble(0.5, 0.5, 1000)  # 所有手柄震动1秒

    while True:
        start_event.wait()  # 等待触发事件
        vibrate_all()
        time.sleep(1)
        start_event.clear()  # 重置事件


if __name__ == "__main__":
    start_event = multiprocessing.Event()
    processes = []

    try:
        # 创建每个手柄的窗口进程
        for i in range(joystick_count):
            p = multiprocessing.Process(target=joystick_window, args=(i, start_event))
            p.start()
            processes.append(p)

        # 创建控制所有手柄震动的进程
        p_vibrate = multiprocessing.Process(target=all_joysticks_vibrate, args=(start_event,))
        p_vibrate.start()
        processes.append(p_vibrate)

        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("收到中断信号，正在关闭所有进程...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        print("所有进程已关闭。")
