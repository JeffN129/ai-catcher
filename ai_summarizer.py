import json
import time
import requests
import logging
import os

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# ⚙️ API 配置区域 (请在此处填入你的配置)
# ==========================================
# 改为 DeepSeek 的接口配置
os.environ.get("DEEPSEEK_API_KEY")
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
    接收新闻列表，过滤掉历史已存在的数据，逐条调用 API 生成总结，
    并将新数据与历史数据合并后写回本地 JSON 文件。
    """
    logging.info(f"开始处理 AI 总结任务，本次抓取共 {len(news_list)} 条源数据...")
    
    # 1. 尝试读取历史数据
    historical_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                historical_data = json.load(f)
            logging.info(f"成功读取历史记录，当前本地已有 {len(historical_data)} 条资讯。")
        except Exception as e:
            logging.error(f"读取历史文件失败: {e}，将作为全新文件处理。")
            historical_data = []

    # 2. 提取历史数据中所有的 URL，构建集合（Set），用于极速去重校验
    existing_urls = {item.get('url') for item in historical_data if item.get('url')}
    
    processed_news = []
    
    # 3. 遍历本次抓取的新闻
    for i, news in enumerate(news_list):
        news_url = news.get('url')
        
        # 【核心逻辑】：基于 URL 去重
        if news_url in existing_urls:
            logging.info(f"  -> [跳过] 该资讯已存在于历史记录中: {news.get('title')}")
            continue
            
        logging.info(f"正在处理新增资讯 [{len(processed_news)+1}]: {news.get('title')}")
        
        # 调用大模型生成总结 (假设 generate_ai_summary 已在上方定义)
        summary = generate_ai_summary(news['snippet'])
        
        # 将生成的总结塞回原有的字典中
        news['ai_summary'] = summary
        processed_news.append(news)
        
        # 成功处理一条后，强制延时，防止请求过快触发 API 限制
        time.sleep(1.5) 
        
    # 4. 合并数据：将最新处理的新闻放在列表最前面，历史数据放在后面
    final_data = processed_news + historical_data
    
    # 5. 将全量合并后的数据写回 JSON 文件
    if processed_news:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            logging.info(f"🎉 处理完成！本次新增 {len(processed_news)} 条，总数据量累计达到: {len(final_data)} 条。")
        except Exception as e:
            logging.error(f"保存 JSON 文件失败: {e}")
    else:
        logging.info("🎉 本次运行没有发现新资讯，历史文件保持不变。")
