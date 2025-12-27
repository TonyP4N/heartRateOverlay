import tkinter as tk
from tkinter import colorchooser
import configparser
import sys
import os
import random
from PIL import Image, ImageDraw, ImageTk

from config import COLOR, ART_FONT, CONFIG_FILE


# 配置文件名
CONFIG_FILE = "color_config.ini"

# 从 new_heart_rate.py 中获取默认的颜色和字体
try:
    from heart_rate_app import COLOR as DEFAULT_COLOR, ART_FONT as DEFAULT_FONT
except ImportError:
    DEFAULT_COLOR = COLOR
    DEFAULT_FONT = ART_FONT

# 预设艺术字体列表
FONT_LIST = [
    "Helvetica",
    "Roboto",
    "Times New Roman",
    "Georgia",
    "Comic Sans MS",
    "Verdana",
    "Arial",
    "Garamond",
    "Baskerville",
    "Futura",
    "Bodoni",
    "Rockwell"
]

class ColorFontSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("选择文本颜色和字体")
        self.root.geometry("800x400+400+200")  # 较大窗口
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")
        self.set_palette_icon()
    
        if os.path.exists(CONFIG_FILE):
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            self.chosen_color = config["Settings"].get("font_color", DEFAULT_COLOR)
            self.chosen_font = config["Settings"].get("font", DEFAULT_FONT)
        else:
            self.chosen_color = DEFAULT_COLOR
            self.chosen_font = DEFAULT_FONT

        # 创建页面布局：左侧颜色选择，右侧字体选择，下方预览区域和操作按钮
        self.create_widgets()
        self.update_preview()

    def set_palette_icon(self):
        size = (64, 64)
        image = Image.new("RGBA", size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([5, 5, 59, 59], fill="lightyellow", outline="goldenrod")
        colors = ["red", "blue", "green", "purple", "orange"]
        positions = [(15, 15), (40, 15), (15, 40), (40, 40), (27, 27)]
        for pos, color in zip(positions, colors):
            x, y = pos
            r = 7
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline="black")
        self.icon_image = ImageTk.PhotoImage(image)
        self.root.iconphoto(False, self.icon_image)

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # 使用 grid 布局分为两列
        left_frame = tk.Frame(main_frame, bg="#f0f0f0")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10)
        right_frame = tk.Frame(main_frame, bg="#f0f0f0")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # 左侧：颜色选择区域
        color_label = tk.Label(left_frame, text="颜色选择：", bg="#f0f0f0", fg="#333333", font=("微软雅黑", 16))
        color_label.pack(pady=(10,20))
        # 显示当前颜色的区域，点击后调出颜色选择对话框
        self.color_display = tk.Label(left_frame, text="点击选择颜色", bg=self.chosen_color, fg="#ffffff",
                                      font=("微软雅黑", 14), width=20, height=2)
        self.color_display.pack(pady=(0,10))
        self.color_display.bind("<Button-1>", lambda e: self.choose_color())

        # 右侧：字体选择区域
        font_label = tk.Label(right_frame, text="字体选择：", bg="#f0f0f0", fg="#333333", font=("微软雅黑", 16))
        font_label.pack(pady=(10,20))
        self.font_var = tk.StringVar(value=self.chosen_font)
        self.font_optionmenu = tk.OptionMenu(right_frame, self.font_var, *FONT_LIST, command=self.on_font_change)
        self.font_optionmenu.config(bg="#ffffff", fg="#333333", font=("微软雅黑", 14), width=15, relief=tk.FLAT)
        self.font_optionmenu["menu"].config(bg="#ffffff", fg="#333333", font=("微软雅黑", 12))
        self.font_optionmenu.pack(pady=(0,10))

        # 底部：预览区域（跨两列），显示随机心率效果
        self.preview_label = tk.Label(main_frame, text="", bg="#f0f0f0", fg=self.chosen_color,
                                      font=(self.chosen_font, 24))
        self.preview_label.grid(row=1, column=0, columnspan=2, pady=(20,10))

        # 底部按钮区域：保存和取消
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10,0))
        save_button = tk.Button(button_frame, text="保存", command=self.save_config,
                                bg="#ffffff", fg="#333333", font=("微软雅黑", 14), relief=tk.FLAT, width=10)
        save_button.pack(side="left", padx=10)
        cancel_button = tk.Button(button_frame, text="取消", command=self.root.destroy,
                                  bg="#ffffff", fg="#333333", font=("微软雅黑", 14), relief=tk.FLAT, width=10)
        cancel_button.pack(side="left", padx=10)

    def choose_color(self):
        color_code = colorchooser.askcolor(title="选择颜色", parent=self.root)
        if color_code[1] is not None:
            self.chosen_color = color_code[1]
            self.color_display.config(bg=self.chosen_color)
            self.update_preview()

    def on_font_change(self, value):
        self.chosen_font = value
        self.update_preview()

    def update_preview(self):
        random_hr = random.randint(60, 120)
        preview_text = f"{random_hr} bpm"
        self.preview_label.config(text=preview_text, fg=self.chosen_color, font=(self.chosen_font, 24))

    def save_config(self):
        config = configparser.ConfigParser()
        config["Settings"] = {
            "font_color": self.chosen_color,
            "font": self.chosen_font
        }
        with open(CONFIG_FILE, "w") as f:
            config.write(f)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorFontSelector(root)
    root.mainloop()