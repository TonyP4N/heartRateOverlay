import tkinter as tk
import time
import threading
import win32gui
import win32con
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options  # Correct import
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os

# 添加 pystray 和 PIL 依赖
import pystray
from PIL import Image, ImageDraw

# Load environment variables from .env file
load_dotenv()

# Stromno 心率数据 URL
STROMNO_URL = os.getenv("STROMNO_URL")
COLOR = os.getenv("COLOR")

class HeartRateWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Heart Rate Monitor")
        self.root.geometry("200x100")  # 先设置默认大小
        self.root.attributes("-topmost", True)  # 窗口置顶
        self.root.configure(bg=COLOR)  # 透明背景
        self.root.overrideredirect(True)  # 隐藏窗口边框
        self.root.attributes("-transparentcolor", COLOR)  # 让背景透明

        # 创建心率显示标签
        self.label = tk.Label(root, text="Loading...", font=("Arial", 28, "bold"), fg="white", bg=COLOR)  # 白色字体
        self.label.pack(expand=True, fill="both")

        # 绑定鼠标拖动事件
        self.label.bind("<ButtonPress-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        self.set_position()

        # 启动浏览器
        self.start_browser()

        self.update_heart_rate()

        threading.Thread(target=self.force_always_on_top, daemon=True).start()

        # 添加系统托盘图标（不改变原有逻辑）
        self.setup_tray_icon()

    def set_position(self):
        """动态设置窗口位置，确保不超出屏幕"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = min(1690, screen_width - 200)
        y = min(619, screen_height - 100)

        self.root.geometry(f"200x100+{x}+{y}")

    def start_move(self, event):
        """当鼠标按下时，记录窗口起始位置"""
        self.start_x = event.x
        self.start_y = event.y

    def do_move(self, event):
        """拖动窗口"""
        x_offset = event.x - self.start_x
        y_offset = event.y - self.start_y

        # 获取当前窗口位置
        window_x = self.root.winfo_x() + x_offset
        window_y = self.root.winfo_y() + y_offset

        # 更新窗口位置
        self.root.geometry(f"+{window_x}+{window_y}")

    def start_browser(self):
        """启动 Selenium 并打开 Stromno 页面"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--window-size=800x600")  

        # 启动浏览器
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.get(STROMNO_URL)

    def fetch_heart_rate(self):
        """从 Stromno 页面获取心率数据"""
        try:
            # 等待心率数据出现
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "widget-bpm"))
            )
            heart_rate_element = self.driver.find_element(By.ID, "widget-bpm")
            return heart_rate_element.text.strip()
        except Exception as e:
            print(f"Error fetching heart rate: {e}")
            return "N/A"

    def update_heart_rate(self):
        """定期更新心率数据，每 0.5 秒更新一次"""
        heart_rate = self.fetch_heart_rate()
        self.label.config(text=f"{heart_rate} bpm")
        self.root.after(500, self.update_heart_rate)  # 0.5 秒更新一次

    def force_always_on_top(self):
        """确保窗口即使在全屏模式下也能置顶"""
        while True:
            hwnd = win32gui.FindWindow(None, "Heart Rate Monitor")  # 获取窗口句柄
            if hwnd:
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            time.sleep(0.5)  # 每 0.5 秒刷新一次

    def close_browser(self):
        """关闭浏览器"""
        self.driver.quit()

    # =================== 系统托盘相关代码 ===================

    def create_image(self):
        """创建托盘图标的图片"""
        width, height = 64, 64
        image = Image.new('RGB', (width, height), "black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((width//4, height//4, width*3//4, height*3//4), fill="white")
        return image

    def setup_tray_icon(self):
        """创建并启动系统托盘图标"""
        image = self.create_image()
        menu = pystray.Menu(pystray.MenuItem("退出", self.on_quit))
        self.tray_icon = pystray.Icon("heart_rate_monitor", image, "Heart Rate Monitor", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_quit(self, icon, item):
        """托盘图标退出回调"""
        self.close_browser()
        icon.stop()
        self.root.quit()

def main():
    root = tk.Tk()
    app = HeartRateWidget(root)
    # 关闭窗口时退出 Selenium
    root.protocol("WM_DELETE_WINDOW", lambda: [app.close_browser(), root.destroy()])
    root.mainloop()

if __name__ == "__main__":
    main()
