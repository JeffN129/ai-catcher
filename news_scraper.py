import requests
from bs4 import BeautifulSoup
import feedparser
import logging
from ai_summarizer import process_and_save_news
import time
import time
import random  # 用于随机延时
import re      # 用于正则表达式，智能匹配链接

# 配置日志输出格式，方便调试和监控运行状态
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 统一请求头，模拟真实浏览器访问，降低被反爬虫拦截的概率
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def get_article_snippet(url):
    """
    通用辅助函数：访问文章详情页，提取正文的前几段作为摘要内容。
    注意：为了防止请求过快被封 IP，可以适当在此处加入 time.sleep()。
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        # 根据网页编码自动解码
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        # 尝试寻找常见的正文容器，提取所有的 <p> 标签
        # 多数新闻网站的正文都包含在 <p> 标签中
        paragraphs = soup.find_all('p')

        snippet_text = ""
        count = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            # 过滤掉太短的无意义段落（如：版权声明、编辑名字等）
            if len(text) > 20:
                snippet_text += text + " "
                count += 1
            # 只取前两到三个有效段落即可，避免数据过大
            if count >= 2:
                break

        return snippet_text if snippet_text else "未能提取到有效正文内容"
    except Exception as e:
        logging.warning(f"  [辅助] 抓取正文片段失败 ({url}): {e}")
        return "正文抓取失败或超时"


def fetch_arxiv_news(limit=5):
    """
    1. 抓取 arXiv (优化版：先用 requests 伪装浏览器获取数据，再解析)
    """
    logging.info("开始抓取 arXiv (CS.AI) ...")
    news_list = []
    rss_url = "http://export.arxiv.org/rss/cs.AI"

    try:
        # 第一步：用 requests 带着伪装的 HEADERS 去请求 RSS 数据
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        # 第二步：将拿到的文本数据交给 feedparser 解析
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
    """
    2. 抓取 机器之心 (优化版：放弃CSS类名，直接正则匹配文章链接)
    """
    logging.info("开始抓取 机器之心 ...")
    news_list = []
    base_url = "https://www.jiqizhixin.com"

    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 智能匹配：寻找所有 href 属性包含 '/article/' 的 <a> 标签
        articles = soup.find_all('a', href=re.compile(r'/article/'))

        seen_urls = set()
        count = 0

        for a_tag in articles:
            if count >= limit:
                break

            link = a_tag.get('href', '')
            title = a_tag.get_text(strip=True)

            # 过滤掉没有标题，或者标题太短的无关链接（比如图片上的空链接）
            if not title or len(title) < 5:
                continue

            if link.startswith('/'):
                link = base_url + link

            if link in seen_urls:
                continue
            seen_urls.add(link)

            # 直接进入详情页抓取摘要
            snippet = get_article_snippet(link)

            news_list.append({
                'source': '机器之心',
                'title': title,
                'url': link,
                'snippet': snippet
            })
            count += 1
            time.sleep(random.uniform(2, 4))  # 随机停顿 2-4 秒

    except Exception as e:
        logging.error(f"抓取 机器之心 失败: {e}")

    return news_list


def fetch_qbitai_news(limit=5):
    """
    3. 抓取 量子位 (QbitAI)
    替换了原有的 AI Base。使用正则匹配典型的文章链接结构。
    """
    logging.info("开始抓取 量子位 (QbitAI) ...")
    news_list = []
    base_url = "https://www.qbitai.com/"

    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 智能匹配：量子位的文章链接通常包含年份格式，如 qbitai.com/2026/03/
        # 或者寻找 class 包含 article-title 的链接
        links = soup.find_all('a', href=re.compile(r'qbitai\.com/\d{4}/'))

        seen_urls = set()
        count = 0

        for link_tag in links:
            if count >= limit:
                break

            link = link_tag.get('href', '')
            title = link_tag.get_text(strip=True)

            # 过滤掉可能抓到的短文本（如“阅读更多”等）
            if not title or len(title) < 6:
                continue

            if link in seen_urls:
                continue
            seen_urls.add(link)

            # 进入详情页抓取摘要
            snippet = get_article_snippet(link)

            news_list.append({
                'source': '量子位',
                'title': title,
                'url': link,
                'snippet': snippet
            })
            count += 1
            time.sleep(random.uniform(2, 4))  # 随机停顿防封

    except Exception as e:
        logging.error(f"抓取 量子位 失败: {e}")

    return news_list


def fetch_36kr_news(limit=5):
    """
    4. 抓取 36Kr
    注意：36Kr 反爬策略较严（如使用验证码、动态JS渲染等），普通的 requests 可能会被拦截或只能拿到部分数据。
    这里使用静态解析方案，重点寻找包含 '/p/' 的文章链接。
    """
    logging.info("开始抓取 36Kr ...")
    news_list = []
    base_url = "https://36kr.com"
    # 也可以指定抓取特定的 AI 频道，例如 https://36kr.com/information/ai/
    target_url = "https://36kr.com/information/technology/"

    try:
        response = requests.get(target_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 36Kr 的文章链接通常都是 /p/xxxxx 的格式
        article_links = soup.find_all('a', href=lambda href: href and '/p/' in href)

        seen_urls = set()
        count = 0

        for a_tag in article_links:
            if count >= limit:
                break

            link = a_tag.get('href')
            title = a_tag.get_text(strip=True)

            if not title or len(title) < 6:
                continue

            # 补全绝对路径
            if link.startswith('/'):
                link = base_url + link

            if link in seen_urls:
                continue
            seen_urls.add(link)

            # 详情页抓取
            snippet = get_article_snippet(link)

            news_list.append({
                'source': '36Kr',
                'title': title,
                'url': link,
                'snippet': snippet
            })
            count += 1
            time.sleep(random.uniform(2, 5))

    except Exception as e:
        logging.error(f"抓取 36Kr 失败: {e}")

    return news_list


def aggregate_news():
    """
    核心调度函数：汇总四个网站的新闻数据，并返回统一的列表字典格式。
    采用单独的 try-except 和独立函数，确保一个网站宕机/改版不会影响其他网站的数据抓取。
    """
    logging.info("================ 开始执行聚合新闻任务 ================")

    all_news = []

    # 1. arXiv (RSS 方式)
    arxiv_data = fetch_arxiv_news(limit=3)
    all_news.extend(arxiv_data)

    # 2. 机器之心 (Requests + BS4)
    jiqizhixin_data = fetch_jiqizhixin_news(limit=3)
    all_news.extend(jiqizhixin_data)

    # 3. 量子位 (Requests + BS4)
    qbitai_data = fetch_qbitai_news(limit=3)
    all_news.extend(qbitai_data)

    # 4. 36Kr (Requests + BS4)
    kr36_data = fetch_36kr_news(limit=3)
    all_news.extend(kr36_data)

    logging.info(f"================ 聚合完毕，共获取 {len(all_news)} 条资讯 ================")
    return all_news


if __name__ == "__main__":
    # 1. 执行聚合任务，抓取原始新闻数据
    aggregated_results = aggregate_news()

    # 2. 将抓取到的数据列表直接传给 AI 处理函数，并保存为 JSON 文件
    # 如果数据较多，这一步可能会运行一段时间，请耐心等待
    if aggregated_results:
        process_and_save_news(aggregated_results, "daily_news.json")
    else:
        print("今天没有抓取到任何新闻，跳过 AI 总结步骤。")