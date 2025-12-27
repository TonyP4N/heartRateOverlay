import tkinter as tk
import time
import threading
import win32gui
import win32con
import logging
import os
import json
import pystray
from PIL import Image, ImageDraw
from dotenv import load_dotenv

from get_wss import get_wss_links, start_websocket_client

# 加载环境变量（STROMNO_URL、COLOR）
load_dotenv()
STROMNO_URL = os.getenv("STROMNO_URL")
COLOR = os.getenv("COLOR")

# 设置日志级别为 WARNING
logging.getLogger().setLevel(logging.WARNING)

class HeartRateWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Heart Rate Monitor")
        self.root.geometry("200x100")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=COLOR)
        # 隐藏窗口边框（如果需要显示关闭按钮，可以去掉此行）
        self.root.overrideredirect(True)
        self.root.attributes("-transparentcolor", COLOR)

        # 显示心率的标签
        self.label = tk.Label(root, text="Loading...", font=("Arial", 28, "bold"), fg="white", bg=COLOR)
        self.label.pack(expand=True, fill="both")

        # 绑定鼠标拖动事件
        self.label.bind("<ButtonPress-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        self.set_position()
        self.start_websocket_client()

        # 在后台线程中强制窗口始终置顶
        threading.Thread(target=self.force_always_on_top, daemon=True).start()

        # 启动系统托盘图标
        self.create_tray_icon()

    def set_position(self):
        """动态设置窗口位置，确保不超出屏幕"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = min(1690, screen_width - 200)
        y = min(619, screen_height - 100)
        self.root.geometry(f"200x100+{x}+{y}")

    def start_move(self, event):
        """记录鼠标按下时的位置"""
        self.start_x = event.x
        self.start_y = event.y

    def do_move(self, event):
        """拖动窗口"""
        x_offset = event.x - self.start_x
        y_offset = event.y - self.start_y
        window_x = self.root.winfo_x() + x_offset
        window_y = self.root.winfo_y() + y_offset
        self.root.geometry(f"+{window_x}+{window_y}")

    def on_message(self, ws, message):
        """
        WebSocket 收到消息时的回调。
        假设消息内容形如:
            {"timestamp":1742694828170,"data":{"heartRate":73}}
        """
        try:
            data = json.loads(message)
            heart_rate = data["data"]["heartRate"]
        except Exception as e:
            print(f"解析数据出错: {e}, 原始消息: {message}")
            heart_rate = "N/A"
        self.root.after(0, lambda: self.label.config(text=f"{heart_rate} bpm"))

    def on_error(self, ws, error):
        print(f"WebSocket 错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket 关闭: {close_status_code}, {close_msg}")

    def on_open(self, ws):
        print("WebSocket 连接已建立")

    def start_websocket_client(self):
        """
        1. 使用 get_wss_links 捕获页面中的 WebSocket 链接
        2. 使用 start_websocket_client 建立连接
        """
        wss_links = get_wss_links(STROMNO_URL, wait_time=5)
        if not wss_links:
            self.label.config(text="N/A")
            return
        self.wss_url = wss_links[0]
        self.ws = start_websocket_client(
            self.wss_url,
            on_message_callback=self.on_message,
            on_error_callback=self.on_error,
            on_close_callback=self.on_close,
            on_open_callback=self.on_open
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def force_always_on_top(self):
        """确保窗口始终保持置顶状态"""
        while True:
            hwnd = win32gui.FindWindow(None, "Heart Rate Monitor")
            if hwnd:
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                )
            time.sleep(1)

    def close_websocket(self):
        """关闭 WebSocket 连接"""
        if hasattr(self, 'ws'):
            self.ws.close()

    # ===== 以下为系统托盘集成 =====
    def create_tray_icon(self):
        """创建系统托盘图标，并添加退出菜单"""
        image = self.create_image()
        menu = pystray.Menu(pystray.MenuItem("退出", self.on_quit))
        self.tray_icon = pystray.Icon("heart_rate", image, "心率监控", menu)
        # 以线程方式运行托盘图标，避免阻塞主线程
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def create_image(self):
        """创建一个简单的托盘图标 (需要 Pillow 库)"""
        width, height = 64, 64
        image = Image.new("RGB", (width, height), "black")
        dc = ImageDraw.Draw(image)
        dc.rectangle((width//4, height//4, width*3//4, height*3//4), fill="white")
        return image

    def on_quit(self, icon, item):
        """托盘菜单退出时的回调"""
        # 关闭 WebSocket 连接和托盘图标，并退出应用
        self.close_websocket()
        icon.stop()
        self.root.quit()

def main():
    root = tk.Tk()
    app = HeartRateWidget(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [app.close_websocket(), root.destroy()])
    root.mainloop()

if __name__ == "__main__":
    main()
