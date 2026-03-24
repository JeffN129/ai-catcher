import json
import time
import requests
import logging

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# ⚙️ API 配置区域 (请在此处填入你的配置)
# ==========================================
# 改为 DeepSeek 的接口配置
API_KEY = "sk-d9e083a9b6b0409e8d31229ac83255b3"  # ⚠️ 请在这里替换为你申请的 DeepSeek API Key
API_URL = "https://api.deepseek.com/chat/completions"
MODEL_NAME = "deepseek-chat" # DeepSeek 的默认对话模型


# 如果你想换成 DeepSeek，只需修改：
# API_URL = "https://api.deepseek.com/chat/completions"
# MODEL_NAME = "deepseek-chat"

def generate_ai_summary(text, max_retries=3):
    """
    调用大语言模型 API 为文本生成 50-100 字的精简总结。
    带有重试机制（Retrying）和指数退避延时。

    :param text: 需要总结的新闻正文片段
    :param max_retries: 最大重试次数，默认 3 次
    :return: AI 生成的总结文本
    """
    # 如果前面爬虫没有抓到正文，直接跳过 API 调用以节省 Token
    if not text or "抓取失败" in text or len(text) < 20:
        return "无有效原文，跳过 AI 总结。"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 构建 Prompt (提示词)
    prompt = f"请根据以下新闻正文片段，生成一段50到100字的精简中文总结。要求：客观、准确、提炼核心。\n\n新闻片段：{text}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是一个专业的人工智能新闻编辑，擅长从长文中提取核心信息并输出精炼的摘要。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3  # 较低的温度值让输出更加客观、严谨
    }

    # 重试机制循环
    for attempt in range(max_retries):
        try:
            # 发送 POST 请求，设置 15 秒超时防止卡死
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)

            # 检查 HTTP 状态码，如果不是 200 会抛出异常进入 except 块
            response.raise_for_status()

            # 解析 JSON 结果并提取文本
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            return summary

        except requests.exceptions.RequestException as e:
            logging.warning(f"API 网络调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
        except KeyError as e:
            logging.warning(f"API 返回格式异常，可能 Key 错误或欠费 (尝试 {attempt + 1}/{max_retries}): {response.text}")

        # 如果还没达到最大重试次数，则进行延时后重试
        if attempt < max_retries - 1:
            # 指数退避延时 (Exponential Backoff): 失败后分别等待 2秒, 4秒, 8秒...
            sleep_time = 2 ** (attempt + 1)
            logging.info(f"等待 {sleep_time} 秒后进行重试...")
            time.sleep(sleep_time)

    # 如果循环结束还没 return，说明全失败了
    return "AI总结失败：多次调用 API 未能成功获取结果。"


def process_and_save_news(news_list, output_file="daily_news.json"):
    """
    接收新闻列表，逐条调用 API 生成总结，并将最终结果保存为本地 JSON 文件。

    :param news_list: 包含字典的列表（前面爬虫的输出）
    :param output_file: 保存的文件名
    """
    logging.info(f"开始处理 AI 总结任务，共 {len(news_list)} 条数据...")

    processed_news = []

    for i, news in enumerate(news_list):
        logging.info(f"正在处理 [{i + 1}/{len(news_list)}]: {news['title']}")

        # 调用生成函数
        summary = generate_ai_summary(news['snippet'])

        # 将生成的总结塞回原有的字典中
        news['ai_summary'] = summary
        processed_news.append(news)

        # 成功处理一条后，强制延时 1-2 秒，防止请求过快触发 API 的 QPS 限制 (Rate Limit)
        time.sleep(1.5)

        # 将包含 AI 总结的新数据保存为 JSON 文件
    try:
        # ensure_ascii=False 保证中文正常显示，不变成 \uXXXX
        # indent=4 让 JSON 文件内容具有良好的缩进和可读性
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_news, f, ensure_ascii=False, indent=4)
        logging.info(f"🎉 处理完成！所有数据已成功保存至本地文件: {output_file}")
    except Exception as e:
        logging.error(f"保存 JSON 文件失败: {e}")


