import time
import logging
from seleniumwire import webdriver as sw_webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import websocket

# 设置较高的日志级别以减少输出
logging.getLogger().setLevel(logging.WARNING)

def get_wss_links(url, wait_time=5):
    """
    使用 Selenium Wire 打开指定页面，并等待一段时间后捕获所有发起的 WebSocket 请求链接
    :param url: 目标页面 URL
    :param wait_time: 等待时间（秒）
    :return: list, 包含捕获到的所有 wss 链接
    """
    seleniumwire_options = {
        'verify_ssl': False,  # 不验证 SSL 证书
    }
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # 禁用图片加载
    chrome_options.add_argument("--window-size=400,300")  # 小窗口，降低资源消耗

    driver = sw_webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        seleniumwire_options=seleniumwire_options,
        options=chrome_options
    )
    try:
        driver.get(url)
        time.sleep(wait_time)
        # 遍历所有请求，捕获以 "wss://" 开头的链接
        wss_links = [req.url for req in driver.requests if req.response and req.url.startswith("wss://")]
        return wss_links
    finally:
        driver.quit()

def start_websocket_client(wss_url, on_message_callback, on_error_callback=None, on_close_callback=None, on_open_callback=None):
    """
    启动 WebSocket 客户端连接
    :param wss_url: WebSocket 链接
    :param on_message_callback: 消息回调函数
    :param on_error_callback: 错误回调函数
    :param on_close_callback: 关闭回调函数
    :param on_open_callback: 打开连接回调函数
    :return: websocket.WebSocketApp 对象
    """
    ws_app = websocket.WebSocketApp(
        wss_url,
        on_message=on_message_callback,
        on_error=on_error_callback,
        on_close=on_close_callback,
        on_open=on_open_callback
    )
    return ws_app
