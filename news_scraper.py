import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime

# ==========================================
# 🛠️ 配置与环境变量
# ==========================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"

# ==========================================
# 📰 核心：深度正文抓取函数
# ==========================================
def get_article_content(url):
    """进入详情页，抓取核心正文（避开导航和广告）"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 自动寻找常见的正文容器
        article_body = ""
        # 尝试常见的正文标签
        potential_containers = soup.find_all(['article', 'div', 'main'])
        for container in potential_containers:
            # 过滤掉杂质，只找段落比较集中的地方
            paragraphs = container.find_all('p')
            if len(paragraphs) > 3:
                article_body = "\n".join([p.get_text().strip() for p in paragraphs[:8]]) # 取前8段
                break
        
        return article_body[:1500] # 最多取1500字，给AI提供充足素材
    except Exception as e:
        return ""

# ==========================================
# 🤖 核心：AI 首席编辑逻辑 (分两步)
# ==========================================

def ai_editor_selection(news_list):
    """第一步：从海量标题中筛选出真正有价值的重磅新闻"""
    if not news_list: return []
    
    titles = [f"{i}. {n['title']}" for i, n in enumerate(news_list)]
    prompt = f"""你是一位全球顶尖的科技编辑。请从以下新闻标题中，挑选出最具有“技术突破性”、“行业震荡性”或“高度讨论价值”的 8-10 条。
    请只输出选中新闻的索引数字，用逗号隔开，不要任何废话。
    
    新闻列表：
    {chr(10).join(titles)}
    """
    
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "system", "content": "你是一个严苛的新闻主编。"}, {"role": "user", "content": prompt}]
        }
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        indices = resp.json()['choices'][0]['message']['content'].strip().split(',')
        selected_indices = [int(i.strip()) for i in indices if i.strip().isdigit()]
        return [news_list[i] for i in selected_indices if i < len(news_list)]
    except:
        return news_list[:10] # 如果AI筛选失败，退而求其次取前10条

def ai_deep_summary(title, content):
    """第二步：根据深度正文进行高质量总结"""
    if not content or len(content) < 50:
        return "（素材不足，仅根据标题记录）"
        
    prompt = f"""请根据以下文章正文，提供一个高质量的深度摘要。
    要求：
    1. 包含核心技术点或事件背景。
    2. 说明该事件对AI行业的具体影响。
    3. 语言专业、精炼。
    4. 字数在 150-200 字之间。
    
    标题：{title}
    正文：{content}
    """
    
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        return resp.json()['choices'][0]['message']['content'].strip()
    except:
        return "AI 深度解析失败。"

# ==========================================
# 🕵️ 抓取源：新增 Hacker News
# ==========================================
def scrape_hacker_news():
    news = []
    try:
        # 获取 TopStories ID
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:15]
        for item_id in top_ids:
            detail = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
            if 'title' in detail and 'url' in detail:
                news.append({
                    'source': 'Hacker News',
                    'title': f"[极客热议] {detail['title']}",
                    'url': detail['url'],
                    'snippet': '点击查看详情'
                })
    except: pass
    return news

# ==========================================
# 🚀 主运行函数
# ==========================================
def main():
    print(f"[{datetime.now()}] 启动深度抓取任务...")
    
    # 1. 采集全网原始资讯 (这里仅展示核心逻辑，你可以把之前的11个源都放进来)
    raw_news = []
    raw_news.extend(scrape_hacker_news())
    # ... 此处省略你之前的 36Kr, 机器之心等抓取函数 ...
    
    # 2. AI 首席编辑筛选（海选 -> 精选）
    print(f"海选抓取到 {len(raw_news)} 条，正在进行 AI 精选...")
    top_news = ai_editor_selection(raw_news)
    
    # 3. 深度内容提取与总结
    final_data = []
    for item in top_news:
        print(f"正在深入解析: {item['title']}")
        # 重点：不再使用列表页的 snippet，而是去抓正文！
        full_content = get_article_content(item['url'])
        
        # 喂给 AI 进行深度总结
        summary = ai_deep_summary(item['title'], full_content)
        
        item['ai_summary'] = summary
        item['publish_time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        # 给深度解析的文章手动赋予极高初始热度
        item['heat_score'] = 95 
        final_data.append(item)
        
        time.sleep(1) # 礼貌抓取
    
    # 4. 保存结果
    with open("daily_news.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    print("任务完成！")

if __name__ == "__main__":
    main()
