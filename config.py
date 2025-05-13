import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 微信客服配置
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID")  # 企业ID
WECHAT_SECRET = os.getenv("WECHAT_SECRET")  # Secret
WECHAT_TOKEN = os.getenv("WECHAT_TOKEN")  # Token
WECHAT_ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY")  # EncodingAESKey

# 服务器配置
HOST = "0.0.0.0"
PORT = 8080

# 飞书
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET')


# openai
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
