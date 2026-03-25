import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from datetime import datetime, timedelta

# ==========================================
# ⚙️ 基础配置与日志
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

# ==========================================
# 🕒 第一部分：时间解析引擎 (Time Parser)
# ==========================================
def parse_publish_time(time_str):
    """
    健壮的时间解析辅助函数。
    支持标准格式和相对格式，解析失败默认返回当前系统时间。
    返回：datetime 对象
    """
    now = datetime.now()
    if not time_str:
        return now
        
    time_str = str(time_str).strip()
    
    try:
        # 1. 处理相对时间 (刚刚, x分钟前, x小时前)
        if "刚刚" in time_str:
            return now
            
        match_min = re.search(r'(\d+)\s*分钟前', time_str)
        if match_min:
            return now - timedelta(minutes=int(match_min.group(1)))
            
        match_hour = re.search(r'(\d+)\s*小时前', time_str)
        if match_hour:
            return now - timedelta(hours=int(match_hour.group(1)))
            
        if "昨天" in time_str:
            match_time = re.search(r'(\d{1,2}):(\d{2})', time_str)
            if match_time:
                hour, minute = int(match_time.group(1)), int(match_time.group(2))
                return now.replace(hour=hour, minute=minute, second=0) - timedelta(days=1)
            return now - timedelta(days=1)
            
        # 2. 处理标准格式 (YYYY-MM-DD HH:MM 或 MM-DD 等)
        # 匹配 2026-03-25 14:00 或 2026/03/25
        match_date = re.search(r'(\d{4})[-\./年](\d{1,2})[-\./月](\d{1,2})日?(?:\s+(\d{1,2}):(\d{2}))?', time_str)
        if match_date:
            year, month, day = map(int, match_date.groups()[:3])
            hour = int(match_date.group(4)) if match_date.group(4) else 0
            minute = int(match_date.group(5)) if match_date.group(5) else 0
            return datetime(year, month, day, hour, minute)
            
        # 若都不匹配，但包含了数字，尝试作为今年处理 (如 "03-25 14:00")
        match_short_date = re.search(r'(\d{1,2})[-\./月](\d{1,2})日?(?:\s+(\d{1,2}):(\d{2}))?', time_str)
        if match_short_date:
            month, day = int(match_short_date.group(1)), int(match_short_date.group(2))
            hour = int(match_short_date.group(3)) if match_short_date.group(3) else 0
            minute = int(match_short_date.group(4)) if match_short_date.group(4) else 0
            return datetime(now.year, month, day, hour, minute)
            
    except Exception as e:
        logging.warning(f"时间解析引擎无法识别格式 '{time_str}', 错误: {e}. 默认赋予当前时间.")
        
    return now

# ==========================================
# 🇨🇳 第二部分：国内权威站点抓取模板
# ==========================================
def fetch_cctv_news(limit=5):
    """模板1：央视网抓取 (示例)"""
    logging.info("开始抓取 [央视网] ...")
    news_list = []
    # 替换为真实的央视网 AI/科技 频道 URL
    url = "https://news.cctv.com/tech/" 
    
    try:
        response = requests.get(url, headers=get_random_headers(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 占位：使用真实的 CSS 选择器
        articles = soup.find_all('li', class_='news-item')[:limit] 
        for art in articles:
            # title = ...
            # link = ...
            # snippet = ...
            # raw_time_str = art.find('span', class_='time').get_text(strip=True)
            
            # --- 模拟数据 ---
            title = "央视网：中国大模型产业取得突破"
            link = "https://news.cctv.com/demo1"
            snippet = "今日科技部宣布..."
            raw_time_str = "2小时前" 
            # ----------------
            
            pub_time = parse_publish_time(raw_time_str)
            
            news_list.append({
                'source': '央视网',
                'title': title,
                'url': link,
                'snippet': snippet,
                'publish_time': pub_time # 存入 datetime 对象用于后续排序
            })
    except Exception as e:
        logging.error(f"抓取 央视网 失败: {e}")
    return news_list

def fetch_caixin_news(limit=5):
    """模板2：财新网抓取 (示例)"""
    logging.info("开始抓取 [财新网] ...")
    news_list = []
    # 填入具体逻辑
    return news_list

# ==========================================
# 🌍 核心功能：海外站点严格熔断机制
# ==========================================
def fetch_mit_tech_review(limit=3):
    """海外站：MIT Technology Review (严格超时熔断)"""
    logging.info("开始抓取海外源 [MIT Tech Review] ...")
    news_list = []
    url = "https://www.technologyreview.com/topic/artificial-intelligence/"
    
    try:
        # ⚠️ 核心要求：严格控制 8 秒超时
        response = requests.get(url, headers=get_random_headers(), timeout=8)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 模拟数据解析 ---
        # TODO: 填入真实的解析逻辑
        pub_time = parse_publish_time("2026-03-24 23:00") 
        news_list.append({
            'source': 'MIT Tech Review',
            'title': "The next leap in GenAI architectures",
            'url': "https://www.technologyreview.com/demo",
            'snippet': "Researchers propose a new alternative to Transformers...",
            'publish_time': pub_time
        })
        
    except requests.exceptions.Timeout:
        logging.error("❌ 触发熔断：[MIT Tech Review] 请求超时 (>8秒)，自动切断防止阻塞。")
        return []
    except requests.exceptions.ConnectionError:
        logging.error("❌ 触发熔断：[MIT Tech Review] 网络连接失败 (可能被墙)。")
        return []
    except Exception as e:
        logging.error(f"⚠️ [MIT Tech Review] 解析异常: {e}")
        return []
        
    return news_list

def fetch_venturebeat_news(limit=3):
    """海外站：VentureBeat (严格超时熔断)"""
    logging.info("开始抓取海外源 [VentureBeat] ...")
    news_list = []
    url = "https://venturebeat.com/category/ai/"
    
    try:
        # ⚠️ 核心要求：严格控制 8 秒超时
        response = requests.get(url, headers=get_random_headers(), timeout=8)
        response.raise_for_status()
        
        # --- 模拟数据解析 ---
        # TODO: 填入真实的解析逻辑
        
    except requests.exceptions.Timeout:
        logging.error("❌ 触发熔断：[VentureBeat] 请求超时 (>8秒)，放弃抓取。")
        return []
    except requests.exceptions.ConnectionError:
        logging.error("❌ 触发熔断：[VentureBeat] 网络连接被拒。")
        return []
    except Exception as e:
        logging.error(f"⚠️ [VentureBeat] 解析异常: {e}")
        return []
        
    return news_list


# ==========================================
# 🌟 第三部分：全局汇总与时间排序核心
# ==========================================
def aggregate_news():
    """
    调度所有抓取函数，并基于提取的 publish_time 进行全局倒序排序。
    """
    logging.info("================ 开始执行核心新闻聚合管道 ================")
    all_news = []
    
    # 1. 串行执行各站点的抓取任务 (遇到海外超时会自动跳过，不阻塞主线程)
    all_news.extend(fetch_cctv_news())
    all_news.extend(fetch_caixin_news())
    # ... 其他国内站点
    
    all_news.extend(fetch_mit_tech_review())
    all_news.extend(fetch_venturebeat_news())
    
    if not all_news:
        logging.warning("本次运行未能抓取到任何新闻！")
        return []
        
    logging.info(f"聚合完毕，初步获取 {len(all_news)} 条资讯，准备进行时间线排序...")

    # 2. 核心：利用 Python 强大的 sort 方法，根据 datetime 对象倒序排列 (最新 -> 最旧)
    all_news.sort(key=lambda x: x['publish_time'], reverse=True)
    
    # 3. 排序完成后，将 datetime 对象格式化为友好的字符串，以便 JSON 序列化和前端展示
    for news in all_news:
        if isinstance(news['publish_time'], datetime):
            news['publish_time'] = news['publish_time'].strftime('%Y-%m-%d %H:%M')

    logging.info(f"排序完成！最新一条新闻时间为: {all_news[0]['publish_time']}")
    logging.info("================ 聚合管道执行完毕 ================")
    
    return all_news

# ==========================================
# 启动入口
# ==========================================
if __name__ == "__main__":
    # 为了测试，这里直接打印结果。实际项目中请传入 ai_summarizer
    results = aggregate_news()
    for idx, item in enumerate(results):
        print(f"[{idx+1}] {item['publish_time']} | {item['source']} | {item['title']}")
