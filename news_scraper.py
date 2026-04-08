import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
from urllib.parse import urljoin

# ==========================================
# 🛠️ 配置与环境变量
# ==========================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"

# ==========================================
# 📰 核心：深度正文提取器
# ==========================================
def get_full_article_content(url):
    """进入详情页，智能提取核心正文内容"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=12)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除干扰标签
        for s in soup(["script", "style", "nav", "footer", "header", "aside"]):
            s.decompose()

        # 尝试常见正文容器
        for selector in ['article', 'main', '.post-content', '.article-content', '#content', '.entry-content', '.content']:
            target = soup.select_one(selector)
            if target:
                text = "\n".join([p.get_text().strip() for p in target.find_all('p') if len(p.get_text()) > 20])
                if len(text) > 100: return text[:1500]
        
        # 密度算法兜底
        paragraphs = soup.find_all('p')
        content = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 25])
        return content[:1500]
    except:
        return ""

# ==========================================
# 🤖 核心：AI 首席编辑部 (两步决策)
# ==========================================
def ai_editor_workflow(raw_news):
    """
    第一步：从海选名单挑选 Top 10
    第二步：深度精读并生成 AI 总结
    """
    if not raw_news: return []
    print(f"[{datetime.now()}] AI 正在从 {len(raw_news)} 条原始资讯中挑选重磅内容...")
    
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    
    # 1. 筛选
    titles = [f"{i}. [{n['source']}] {n['title']}" for i, n in enumerate(raw_news)]
    select_prompt = f"你是一位资深科技主编。请从以下 50 条资讯标题中，挑选出最具有技术突破性、行业震荡性或高度讨论价值的 10 条。仅输出选中项的索引数字，用逗号分隔。\n\n列表如下：\n{chr(10).join(titles)}"
    
    selected_items = []
    try:
        resp = requests.post(API_URL, headers=headers, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": select_prompt}]
        }, timeout=25)
        content = resp.json()['choices'][0]['message']['content'].strip()
        indices = [int(i.strip()) for i in content.split(',') if i.strip().isdigit()]
        selected_items = [raw_news[i] for i in indices if i < len(raw_news)]
    except:
        selected_items = raw_news[:10]

    # 2. 总结
    final_processed = []
    for item in selected_items:
        print(f"-> 深度精读解析: {item['title']}")
        full_text = get_full_article_content(item['url'])
        
        summary_prompt = f"请根据以下文章正文，提供一段深度解析（150-200字）。要求：指出核心技术逻辑或事件背景，并分析其对AI行业的深层影响。禁止废话。\n\n标题：{item['title']}\n正文：{full_text if len(full_text) > 100 else '（正文获取受限，请根据标题进行行业背景关联解析）'}"
        
        try:
            resp = requests.post(API_URL, headers=headers, json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": summary_prompt}]
            }, timeout=25)
            item['ai_summary'] = resp.json()['choices'][0]['message']['content'].strip()
        except:
            item['ai_summary'] = "AI 深度解析生成失败。"
        
        item['publish_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        item['heat_score'] = 98 
        final_processed.append(item)
        time.sleep(0.5)

    return final_processed

# ==========================================
# 🕵️ 全源抓取逻辑 (包含你要求的所有硬核源)
# ==========================================
def scrape_all_sources():
    all_news = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}
    
    # 1. arXiv (AI Section)
    try:
        resp = requests.get("https://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=10", timeout=10)
        soup = BeautifulSoup(resp.text, 'xml')
        for entry in soup.find_all('entry'):
            all_news.append({'source': 'arXiv', 'title': f"[论文] {entry.title.text.strip()}", 'url': entry.id.text.strip()})
    except: pass

    # 2. Hacker News
    try:
        ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:15]
        for idx in ids:
            d = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{idx}.json").json()
            if 'title' in d and 'url' in d:
                all_news.append({'source': 'Hacker News', 'title': f"[极客] {d['title']}", 'url': d['url']})
    except: pass

    # 3. GitHub Trending
    try:
        r = requests.get("https://github.com/trending/python?since=daily", headers=headers, timeout=10)
        s = BeautifulSoup(r.text, 'html.parser')
        repos = s.select('article.Box-row h2 a')[:5]
        for repo in repos:
            all_news.append({'source': 'GitHub', 'title': f"[趋势] {repo.get_text(strip=True)}", 'url': "https://github.com" + repo['href']})
    except: pass

    # 4. 其他垂直源与大报 (36Kr, 机器之心, Decoder, VentureBeat 等)
    sites = [
        {"name": "The Decoder", "url": "https://the-decoder.com/news/", "selector": "h2.entry-title a"},
        {"name": "VentureBeat", "url": "https://venturebeat.com/category/ai/", "selector": "h2.article-title a"},
        {"name": "机器之心", "url": "https://www.jiqizhixin.com/", "selector": "a.article-item__title"},
        {"name": "量子位", "url": "https://www.qbitai.com/", "selector": "h3 a"},
        {"name": "36Kr", "url": "https://36kr.com/information/technology/", "selector": "a.article-item-title"},
        {"name": "钛媒体", "url": "https://www.tmtpost.com/tag/2042173", "selector": "a.title"},
        {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/", "selector": "a[data-event-category='Article List Content']"},
        {"name": "财新网", "url": "https://search.caixin.com/search/search.jsp?keyword=AI", "selector": "dt a"},
        {"name": "央视网·数智", "url": "https://search.cctv.com/search.php?qtext=人工智能", "selector": "h3.tit a"}
    ]

    for site in sites:
        try:
            r = requests.get(site['url'], headers=headers, timeout=10)
            s = BeautifulSoup(r.text, 'html.parser')
            links = s.select(site['selector'])[:8]
            for link in links:
                title = link.get_text().strip()
                href = link.get('href')
                if href:
                    href = urljoin(site['url'], href)
                    all_news.append({'source': site['name'], 'title': title, 'url': href})
        except: pass

    return all_news

def main():
    raw_list = scrape_all_sources()
    print(f"总计抓取到 {len(raw_list)} 条原始标题，开始 AI 编辑部加工...")
    refined = ai_editor_workflow(raw_list)
    with open("daily_news.json", "w", encoding="utf-8") as f:
        json.dump(refined, f, ensure_ascii=False, indent=4)
    print("✨ 深度资讯精炼任务已圆满完成！")

if __name__ == "__main__":
    main()
