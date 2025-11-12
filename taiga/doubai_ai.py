from openai import OpenAI
from dotenv import dotenv_values  # pip install python-dotenv
from pathlib import Path

def load_env(env_path: str = ".env") -> dict:
    # 只解析 .env，返回字典，不改动系统环境变量
    p = Path(env_path)
    if not p.exists():
        raise FileNotFoundError(f"未找到 {env_path}，请在项目根目录创建该文件。")
    cfg = dotenv_values(env_path)
    return cfg

# 读取 .env
cfg = load_env()

# 允许两种 key 名称，任选其一
API_KEY = cfg.get("ARK_API_KEY") or cfg.get("OPENAI_API_KEY")
BASE_URL = cfg.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3/bots")

if not API_KEY:
    raise RuntimeError("请在 .env 中设置 ARK_API_KEY（或 OPENAI_API_KEY）。")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)
def ask_once(question: str, prompt: str) -> str:
    """
       入参: question, prompt
       出参: return_message (纯文本)
    """
    resp = client.chat.completions.create(
        model="bot-20251029054843-d8tv6",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )
    try:
        return_message = resp.choices[0].message.content or ""
    except Exception:
        print("warn: API 返回结构异常")
        return_message = ""

    if not return_message:
        print("warn: 模型返回空内容")

    return return_message
