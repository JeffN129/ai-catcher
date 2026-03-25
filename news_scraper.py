import requests
from bs4 import BeautifulSoup
import feedparser
import logging
import time
import random
import re
from ai_summarizer import process_and_save_news

# 配置日志输出格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# 🛡️ 反爬策略配置区：动态 Headers 生成器
# ==========================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def get_random_headers():
    """每次请求时动态生成 Headers，随机抽取 User-Agent 伪装不同浏览器"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.baidu.com/s?wd=AI%E8%B5%84%E8%AE%AF'
    }

# ==========================================
# 🕸️ 通用与各个站点的抓取函数
# ==========================================
def get_article_snippet(url):
    """通用辅助函数：访问文章详情页提取正文"""
    try:
        # 注意：这里改用了 get_random_headers()
        response = requests.get(url, headers=get_random_headers(), timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        paragraphs = soup.find_all('p')
        snippet_text = ""
        count = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20:
                snippet_text += text + " "
                count += 1
            if count >= 2:
                break
        return snippet_text if snippet_text else "未能提取到有效正文内容"
    except Exception as e:
        logging.warning(f"  [辅助] 抓取正文片段失败 ({url}): {e}")
        return "正文抓取失败或超时"

def fetch_arxiv_news(limit=5):
    """1. 抓取 arXiv (AI/CS)"""
    logging.info("开始抓取 arXiv (CS.AI) ...")
    news_list = []
    rss_url = "http://export.arxiv.org/rss/cs.AI"
    
    try:
        response = requests.get(rss_url, headers=get_random_headers(), timeout=15)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            raise Exception("未能解析到任何文章记录。")
            
        for entry in feed.entries[:limit]: 
            title = entry.get('title', '无标题')
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            clean_summary = BeautifulSoup(summary, "html.parser").get_text(strip=True)
            
            news_list.append({
                'source': 'arXiv',
                'title': title,
                'url': link,
                'snippet': clean_summary
            })
    except Exception as e:
        logging.error(f"抓取 arXiv 失败: {e}")
    return news_list

def fetch_jiqizhixin_news(limit=5):
    """2. 抓取 机器之心"""
    logging.info("开始抓取 机器之心 ...")
    news_list = []
    base_url = "https://www.jiqizhixin.com"
    
    try:
        response = requests.get(base_url, headers=get_random_headers(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.find_all('a', href=re.compile(r'/article/'))
        seen_urls = set()
        count = 0
        
        for a_tag in articles:
            if count >= limit: break
            link = a_tag.get('href', '')
            title = a_tag.get_text(strip=True)
            
            if not title or len(title) < 5: continue
            if link.startswith('/'): link = base_url + link
            if link in seen_urls: continue
            seen_urls.add(link)
            
            snippet = get_article_snippet(link)
            news_list.append({
                'source': '机器之心',
                'title': title, 'url': link, 'snippet': snippet
            })
            count += 1
            time.sleep(random.uniform(2, 4))
    except Exception as e:
        logging.error(f"抓取 机器之心 失败: {e}")
    return news_list

def fetch_qbitai_news(limit=5):
    """3. 抓取 量子位 (QbitAI)"""
    logging.info("开始抓取 量子位 (QbitAI) ...")
    news_list = []
    base_url = "https://www.qbitai.com/"
    
    try:
        response = requests.get(base_url, headers=get_random_headers(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=re.compile(r'qbitai\.com/\d{4}/'))
        seen_urls = set()
        count = 0
        
        for link_tag in links:
            if count >= limit: break
            link = link_tag.get('href', '')
            title = link_tag.get_text(strip=True)
            
            if not title or len(title) < 6: continue
            if link in seen_urls: continue
            seen_urls.add(link)
            
            snippet = get_article_snippet(link)
            news_list.append({
                'source': '量子位',
                'title': title, 'url': link, 'snippet': snippet
            })
            count += 1
            time.sleep(random.uniform(2, 4))
    except Exception as e:
        logging.error(f"抓取 量子位 失败: {e}")
    return news_list

def fetch_36kr_news(limit=5):
    """
    4. 抓取 36Kr (带有强化容错和AI关键词过滤机制)
    """
    logging.info("开始抓取 36Kr ...")
    news_list = []
    
    # 🌟 方案一：更换更精准的源头 URL
    target_url = "https://36kr.com/information/ai/" # 改为 36Kr AI 专属频道
    base_url = "https://36kr.com"
    
    # 🛡️ 方案二：关键词白名单拦截
    ai_keywords = ["AI", "大模型", "人工智能", "芯片", "算力", "GPT", "DeepMind", "机器人", "算法", "自动驾驶"]
    
    try:
        response = requests.get(target_url, headers=get_random_headers(), timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_links = soup.find_all('a', href=lambda href: href and '/p/' in href)
        seen_urls = set()
        count = 0
        
        for a_tag in article_links:
            if count >= limit: break
            link = a_tag.get('href')
            
            # 🌟 就是这一行提取了标题！
            title = a_tag.get_text(strip=True)
            
            # ==========================================
            # 🛡️ 【新增拦截逻辑】：关键词过滤
            # ==========================================
            # 检查标题（忽略大小写）是否包含白名单中的任意一个词
            is_ai_related = any(keyword.lower() in title.lower() for keyword in ai_keywords)

            if not is_ai_related:
                # 如果标题里没有这些词，直接跳过这篇文章，去抓下一篇
                # 我们打印一条日志，方便在 Actions 里查看过滤效果
                logging.info(f"  -> [过滤] 标题未匹配到AI关键词，跳过: {title}")
                continue
            # ==========================================

            if not title or len(title) < 6: continue
            if link.startswith('/'): link = base_url + link
            if link in seen_urls: continue
            seen_urls.add(link)
            
            snippet = get_article_snippet(link)
            news_list.append({
                'source': '36Kr',
                'title': title, 'url': link, 'snippet': snippet
            })
            count += 1
            time.sleep(random.uniform(2, 5))
            
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 403:
            logging.error(f"❌ 抓取 36Kr 失败: 遭遇 403 Forbidden 拦截。机房 IP 已被 WAF 封锁。")
        elif status_code >= 500:
            logging.error(f"❌ 抓取 36Kr 失败: 遭遇 {status_code} 服务器内部错误。")
        else:
            logging.error(f"❌ 抓取 36Kr 失败: HTTP 状态码 {status_code}")
        return [] 
    except requests.exceptions.RequestException as e:
        logging.error(f"⚠️ 抓取 36Kr 网络异常: {e}")
        return []
    except Exception as e:
        logging.error(f"⚠️ 抓取 36Kr 发生解析异常: {e}")
        return []
        
    return news_list
# ==========================================
# 🚀 主调度函数
# ==========================================
def aggregate_news():
    """汇总所有新闻数据"""
    logging.info("================ 开始执行聚合新闻任务 ================")
    all_news = []
    
    all_news.extend(fetch_arxiv_news(limit=3))
    all_news.extend(fetch_jiqizhixin_news(limit=3))
    all_news.extend(fetch_qbitai_news(limit=3))
    all_news.extend(fetch_36kr_news(limit=3))
    
    logging.info(f"================ 聚合完毕，共获取 {len(all_news)} 条资讯 ================")
    return all_news

if __name__ == "__main__":
    aggregated_results = aggregate_news()
    if aggregated_results:
        process_and_save_news(aggregated_results, "daily_news.json")
    else:
        print("今天没有抓取到任何新闻，跳过 AI 总结步骤。")
