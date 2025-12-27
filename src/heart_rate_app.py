import tkinter as tk
import time
import threading
import subprocess
import configparser
import sys
import os
from dotenv import load_dotenv

import win32gui
import win32con

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

import pystray
from PIL import Image, ImageDraw

from config import STROMNO_URL, COLOR, ART_FONT, CHECK_INTERVAL, CONFIG_FILE
from color_config import ColorFontSelector


# ============ 全局配置 ============
# load_dotenv()

# CONFIG_FILE = "color_config.ini"
# STROMNO_URL = os.getenv("STROMNO_URL")
# COLOR = os.getenv("COLOR")
# ART_FONT = os.getenv("FONT")  # 艺术字体，可自行修改
# CHECK_INTERVAL = 500 # UI刷新间隔（毫秒），同时也是检测配置文件的间隔


class HeartRateWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Heart Rate Monitor")
        self.root.geometry("200x100")
        self.root.attributes("-topmost", True)  # 窗口置顶
        self.root.overrideredirect(True)        # 隐藏窗口边框

        self.root.configure(bg="black")
        self.root.attributes("-transparentcolor", "black")

        self.font_color = self.load_font_color(default=COLOR)
        self.art_font = ART_FONT

        # 创建显示标签
        self.label = tk.Label(
            root,
            text="Loading...",
            font=(ART_FONT, 28, "bold"),
            fg=self.font_color,
            bg="black"
        )
        self.label.pack(expand=True, fill="both")

        self.label.bind("<ButtonPress-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        self.set_position()

        self.start_browser()

        # 启动后台线程获取心率数据
        threading.Thread(target=self.update_heart_rate_thread, daemon=True).start()

        # 后台线程保证窗口置顶
        threading.Thread(target=self.force_always_on_top, daemon=True).start()

        self.setup_tray_icon()

        # 启动定时器：每隔一段时间检查配置文件是否更新
        self.last_mtime = None
        self.check_config_file()

    def load_font_color(self, default=COLOR):
        """读取配置文件中的字体颜色，如无则返回默认颜色"""
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            return config["Settings"].get("font_color", default)
        else:
            return default
        
    def load_art_font(self, default=ART_FONT):
        """读取配置文件中的字体，如无则返回默认字体"""
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            return config["Settings"].get("font", default)
        else:
            return default

    def check_config_file(self):
        """周期性检测配置文件是否修改，若有新颜色则更新"""
        if os.path.exists(CONFIG_FILE):
            current_mtime = os.path.getmtime(CONFIG_FILE)
            if self.last_mtime is None or current_mtime > self.last_mtime:
                self.last_mtime = current_mtime
                # 重新读取颜色
                new_color = self.load_font_color(default=self.font_color)
                if new_color != self.font_color:
                    self.font_color = new_color
                    self.label.config(fg=self.font_color)
                # 重新读取字体
                new_font = self.load_art_font(default=self.art_font)
                if new_font != self.art_font:
                    self.art_font = new_font
                    self.label.config(font=(self.art_font, 28, "bold"))
        # 通过 Tk 的定时器机制循环调用
        self.root.after(CHECK_INTERVAL, self.check_config_file)

    def set_position(self):
        """动态设置窗口位置，确保不超出屏幕"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = min(1690, screen_width - 200)
        y = min(619, screen_height - 100)
        self.root.geometry(f"200x100+{x}+{y}")

    def start_move(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def do_move(self, event):
        x_offset = event.x - self.start_x
        y_offset = event.y - self.start_y
        window_x = self.root.winfo_x() + x_offset
        window_y = self.root.winfo_y() + y_offset
        self.root.geometry(f"+{window_x}+{window_y}")

    def start_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--window-size=800x600")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.get(STROMNO_URL)

    def fetch_heart_rate(self):
        """从 Stromno 页面获取心率数据"""
        try:
            if hasattr(self, 'heart_rate_element'):
                heart_rate = self.heart_rate_element.text.strip()
            else:
                self.heart_rate_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "widget-bpm"))
                )
                heart_rate = self.heart_rate_element.text.strip()
            return heart_rate
        except StaleElementReferenceException:
            try:
                self.heart_rate_element = self.driver.find_element(By.ID, "widget-bpm")
                return self.heart_rate_element.text.strip()
            except Exception as e:
                print(f"Error fetching heart rate (stale recovery): {e}")
                return "N/A"
        except TimeoutException as e:
            print(f"Timeout fetching heart rate: {e}")
            return "N/A"
        except Exception as e:
            print(f"Error fetching heart rate: {e}")
            return "N/A"

    def update_heart_rate_thread(self):
        """在后台线程中定时更新心率数据"""
        while True:
            heart_rate = self.fetch_heart_rate()
            self.root.after(0, lambda hr=heart_rate: self.label.config(text=f"{hr} bpm"))
            time.sleep(0.5)

    def force_always_on_top(self):
        while True:
            hwnd = win32gui.FindWindow(None, "Heart Rate Monitor")
            if hwnd:
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            time.sleep(0.5)

    def close_browser(self):
        try:
            self.driver.quit()
        except Exception as e:
            print(f"Error closing browser: {e}")

    # ============== 系统托盘相关代码 ==============
    def create_image(self):
        width, height = 64, 64
        image = Image.new('RGB', (width, height), "black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((width//4, height//4, width*3//4, height*3//4), fill=self.font_color)
        return image

    def setup_tray_icon(self):
        image = self.create_image()
        # 菜单包含“更改颜色/字体”和“退出”
        menu = pystray.Menu(
            pystray.MenuItem("更改颜色/字体", self.on_change_color),
            pystray.MenuItem("退出", self.on_quit)
        )
        self.tray_icon = pystray.Icon("heart_rate_monitor", image, "Heart Rate Monitor", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def open_color_config(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("更改颜色/字体")
        ColorFontSelector(config_window)

    def on_change_color(self, icon, item):
        # subprocess.Popen(["python", "color_config.py"])
        self.root.after(0, self.open_color_config)

    def on_quit(self, icon, item):
        self.close_browser()
        icon.stop()
        self.root.quit()

def main():
    root = tk.Tk()
    app = HeartRateWidget(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [app.close_browser(), root.destroy()])
    root.mainloop()

if __name__ == "__main__":
    main()
