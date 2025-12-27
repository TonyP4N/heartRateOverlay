from dotenv import load_dotenv
import os

load_dotenv()  # 加载 .env 文件

CONFIG_FILE = "color_config.ini"
STROMNO_URL = os.getenv("STROMNO_URL")
COLOR = os.getenv("COLOR")
ART_FONT = os.getenv("FONT")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 500))
