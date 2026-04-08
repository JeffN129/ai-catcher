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

def get_full_article_content(url):
    """进入详情页提取核心正文（约1500字），增加 AI 素材量"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=12)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for s in soup(["script", "style", "nav", "footer", "header", "aside"]):
            s.decompose()

        for selector in ['article', 'main', '.post-content', '.article-content', '#content', '.entry-content', '.content']:
            target = soup.select_one(selector)
            if target:
                text = "\n".join([p.get_text().strip() for p in target.find_all('p') if len(p.get_text()) > 20])
                if len(text) > 100: return text[:1500]
        
        paragraphs = soup.find_all('p')
        content = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 25])
        return content[:1500]
    except:
        return ""

def ai_editor_workflow(raw_news):
    """主编筛选 Top 10 + 深度总结"""
    if not raw_news: return []
    print(f"[{datetime.now()}] AI 正在从 {len(raw_news)} 条资讯中挑选重磅内容...")
    
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    
    # 1. 筛选
    titles = [f"{i}. [{n['source']}] {n['title']}" for i, n in enumerate(raw_news)]
    select_prompt = f"你是一位资深科技主编。请从以下列表中挑选出最具有技术突破性或行业震荡性的 10 条。仅输出选中项的索引数字，用逗号分隔。\n\n{chr(10).join(titles)}"
    
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

    # 2. 深度精读（增加 Token 消耗，提高质量）
    final_processed = []
    for item in selected_items:
        print(f"-> 精读解析: {item['title']}")
        full_text = get_full_article_content(item['url'])
        
        summary_prompt = f"根据正文，提供一段深度解析（180字左右）。包含：1.背景 2.核心技术/事件逻辑 3.行业深层影响。\n\n标题：{item['title']}\n正文：{full_text if len(full_text) > 100 else '（正文获取受限，请根据标题进行专家级解析）'}"
        
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

    # 4. 垂直源与权威源
    sites = [
        {"name": "The Decoder", "url": "https://the-decoder.com/news/", "selector": "h2.entry-title a"},
        {"name": "VentureBeat", "url": "https://venturebeat.com/category/ai/", "selector": "h2.article-title a"},
        {"name": "机器之心", "url": "https://www.jiqizhixin.com/", "selector": "a.article-item__title"},
        {"name": "量子位", "url": "https://www.qbitai.com/", "selector": "h3 a"},
        {"name": "36Kr", "url": "https://36kr.com/information/technology/", "selector": "a.article-item-title"},
        {"name": "财新网", "url": "https://search.caixin.com/search/search.jsp?keyword=AI", "selector": "dt a"}
    ]
    for site in sites:
        try:
            r = requests.get(site['url'], headers=headers, timeout=10)
            s = BeautifulSoup(r.text, 'html.parser')
            links = s.select(site['selector'])[:5]
            for link in links:
                href = urljoin(site['url'], link.get('href'))
                all_news.append({'source': site['name'], 'title': link.get_text().strip(), 'url': href})
        except: pass

    return all_news

if __name__ == "__main__":
    raw = scrape_all_sources()
    refined = ai_editor_workflow(raw)
    with open("daily_news.json", "w", encoding="utf-8") as f:
        json.dump(refined, f, ensure_ascii=False, indent=4)
    print("✨ 后端全源抓取任务圆满完成！")
