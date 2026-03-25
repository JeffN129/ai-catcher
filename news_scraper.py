import os
import requests
from bs4 import BeautifulSoup
import feedparser
import logging
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin
# 确保导入你的 AI 总结模块
from ai_summarizer import process_and_save_news  

# ==========================================
# ⚙️ 基础配置与日志
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
# 🕒 时间解析引擎 (Time Parser)
# ==========================================
def parse_publish_time(time_str):
    """健壮的时间解析，支持相对时间和绝对时间"""
    now = datetime.now()
    if not time_str: return now
    time_str = str(time_str).strip()
    
    try:
        if "刚刚" in time_str: return now
        
        match_min = re.search(r'(\d+)\s*分钟前', time_str)
        if match_min: return now - timedelta(minutes=int(match_min.group(1)))
            
        match_hour = re.search(r'(\d+)\s*小时前', time_str)
        if match_hour: return now - timedelta(hours=int(match_hour.group(1)))
            
        if "昨天" in time_str:
            match_time = re.search(r'(\d{1,2}):(\d{2})', time_str)
            if match_time:
                hour, minute = int(match_time.group(1)), int(match_time.group(2))
                return now.replace(hour=hour, minute=minute, second=0) - timedelta(days=1)
            return now - timedelta(days=1)
            
        # 匹配 YYYY-MM-DD HH:MM
        match_date = re.search(r'(\d{4})[-\./年](\d{1,2})[-\./月](\d{1,2})日?(?:\s+(\d{1,2}):(\d{2}))?', time_str)
        if match_date:
            year, month, day = map(int, match_date.groups()[:3])
            hour = int(match_date.group(4)) if match_date.group(4) else 0
            minute = int(match_date.group(5)) if match_date.group(5) else 0
            return datetime(year, month, day, hour, minute)
            
    except Exception as e:
        logging.warning(f"时间解析失败 '{time_str}', 错误: {e}")
        
    return now

def get_article_detail(url, timeout=10):
    """访问文章详情页，智能提取正文摘要和发布时间"""
    snippet, pub_time_str = "未能提取到有效正文", ""
    try:
        response = requests.get(url, headers=get_random_headers(), timeout=timeout)
        
        response.raise_for_status()
        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, 'html.parser')

        #优先寻找 Open Graph 协议的封面图
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            cover_image_url = og_image['content']
        
        # 1. 提取正文片段
        paragraphs = soup.find_all('p')
        text_content = ""
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20: text_content += text + " "
            if len(text_content) > 150: break
        if text_content: snippet = text_content
            
        # 2. 尝试从网页文本中用正则抓取日期格式
        html_text = soup.get_text()
        time_match = re.search(r'(202\d[-\./年]\d{1,2}[-\./月]\d{1,2}日?(?:\s+\d{1,2}:\d{2})?)', html_text)
        if time_match: pub_time_str = time_match.group(1)
        
    except Exception as e:
        pass
    return snippet, parse_publish_time(pub_time_str), cover_image_url

# ==========================================
# 🤖 通用网站抓取器 (自动寻路逻辑)
# ==========================================
def generic_news_fetcher(source_name, target_url, limit=3, timeout=10, must_contain_ai=False):
    """通用的智能抓取函数，适用未知 HTML 结构的站点"""
    logging.info(f"开始抓取 [{source_name}] ...")
    news_list = []
    ai_keywords = ["AI", "大模型", "人工智能", "算法", "GPT", "算力"]
    
    try:
        response = requests.get(target_url, headers=get_random_headers(), timeout=timeout)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        seen_urls = set()
        count = 0
        
        # 寻找所有 a 标签
        for a_tag in soup.find_all('a'):
            if count >= limit: break
            link = a_tag.get('href')
            title = a_tag.get_text(strip=True)
            
            # 基础过滤：标题太短、无链接、或者属于无关的导航链接
            if not title or len(title) < 8 or not link or 'javascript' in link: continue
            
            # 如果要求必须包含 AI 关键词（比如针对财新网首页）
            if must_contain_ai and not any(kw.lower() in title.lower() for kw in ai_keywords):
                continue
                
            full_link = urljoin(target_url, link)
            if full_link in seen_urls: continue
            seen_urls.add(full_link)
            
            # 深入详情页抓取摘要和时间
            snippet, pub_time = get_article_detail(full_link, timeout=timeout)
            
            news_list.append({
                'source': source_name,
                'title': title,
                'url': full_link,
                'snippet': snippet,
                'publish_time': pub_time
                'cover_image_url': cover_img
            })
            count += 1
            time.sleep(random.uniform(1.5, 3)) # 礼貌延时
            
    except Exception as e:
        logging.error(f"❌ 抓取 {source_name} 失败: {e}")
        
    return news_list

# ==========================================
# 🇨🇳 新增的 5 个国内权威站点
# ==========================================
def fetch_pubscholar():
    return generic_news_fetcher("科讯头条", "https://pubscholar.cn/headlines", limit=2)

def fetch_cctv_ai():
    return generic_news_fetcher("央视网·数智", "http://5gai.cctv.cn/h5/index.shtml", limit=2)

def fetch_ccid():
    return generic_news_fetcher("赛迪研究院", "https://www.ccidgroup.com/info/1155/43077.htm", limit=2)

def fetch_caixin():
    # 财新网内容庞杂，开启 must_contain_ai=True 进行过滤
    return generic_news_fetcher("财新网", "https://www.caixin.com", limit=2, must_contain_ai=True)

def fetch_tmtpost():
    return generic_news_fetcher("钛媒体", "https://www.tmtpost.com/tag/topic/299106", limit=2)

# ==========================================
# 🌍 新增的 2 个海外站点 (严格熔断)
# ==========================================
def fetch_mit_tech_review():
    """海外站：MIT Technology Review (严格超时熔断)"""
    try:
        return generic_news_fetcher("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/", limit=2, timeout=8)
    except requests.exceptions.Timeout:
        logging.error("❌ 触发熔断：[MIT Tech Review] 请求超时 (>8秒)")
        return []
    except Exception:
        return []

def fetch_venturebeat():
    """海外站：VentureBeat (严格超时熔断)"""
    try:
        return generic_news_fetcher("VentureBeat", "https://venturebeat.com/category/ai/", limit=2, timeout=8)
    except requests.exceptions.Timeout:
        logging.error("❌ 触发熔断：[VentureBeat] 请求超时 (>8秒)")
        return []
    except Exception:
        return []

# ==========================================
# 🏛️ 原有的 4 个经典站点 (简写调用)
# ==========================================
def fetch_arxiv_news(limit=2):
    logging.info("开始抓取 [arXiv] ...")
    news_list = []
    try:
        feed = feedparser.parse("http://export.arxiv.org/rss/cs.AI")
        for entry in feed.entries[:limit]: 
            pub_time = parse_publish_time(entry.get('published', ''))
            news_list.append({
                'source': 'arXiv', 'title': entry.get('title', ''), 'url': entry.get('link', ''),
                'snippet': BeautifulSoup(entry.get('summary', ''), "html.parser").get_text(strip=True),
                'publish_time': pub_time
            })
    except Exception as e: pass
    return news_list

def fetch_jiqizhixin(): return generic_news_fetcher("机器之心", "https://www.jiqizhixin.com", limit=2)
def fetch_qbitai(): return generic_news_fetcher("量子位", "https://www.qbitai.com/", limit=2)
def fetch_36kr(): return generic_news_fetcher("36Kr", "https://36kr.com/information/ai/", limit=2)

# ==========================================
# 🌟 全局汇总与时间排序核心
# ==========================================
def aggregate_news():
    logging.info("================ 开始执行 11 站全量聚合 ==================")
    all_news = []
    
    # 1. 执行原有的 4 个站点
    all_news.extend(fetch_arxiv_news())
    all_news.extend(fetch_jiqizhixin())
    all_news.extend(fetch_qbitai())
    all_news.extend(fetch_36kr())
    
    # 2. 执行新增的国内 5 个权威站点
    all_news.extend(fetch_pubscholar())
    all_news.extend(fetch_cctv_ai())
    all_news.extend(fetch_ccid())
    all_news.extend(fetch_caixin())
    all_news.extend(fetch_tmtpost())
    
    # 3. 执行海外站点 (带有熔断机制，若超时会静默失败不影响大局)
    all_news.extend(fetch_mit_tech_review())
    all_news.extend(fetch_venturebeat())
    
    if not all_news:
        logging.warning("本次运行未能抓取到任何新闻！")
        return []
        
    logging.info(f"全站聚合完毕，初步获取 {len(all_news)} 条资讯，准备进行时间排序...")

    # 核心：根据 datetime 对象倒序排列 (最新 -> 最旧)
    all_news.sort(key=lambda x: x['publish_time'], reverse=True)
    
    # 将 datetime 对象格式化为字符串，方便保存 JSON
    for news in all_news:
        if isinstance(news['publish_time'], datetime):
            news['publish_time'] = news['publish_time'].strftime('%Y-%m-%d %H:%M')

    logging.info(f"排序完成！最新新闻时间为: {all_news[0]['publish_time']}")
    return all_news

# ==========================================
# 🚀 真实的生产启动入口
# ==========================================
if __name__ == "__main__":
    aggregated_results = aggregate_news()
    
    if aggregated_results:
        logging.info(f"准备将 {len(aggregated_results)} 条已排序资讯交由 AI 总结...")
        # 调用大模型总结并保存
        process_and_save_news(aggregated_results, "daily_news.json")
    else:
        logging.warning("今天没有抓取到任何新闻，跳过 AI 总结步骤。")
