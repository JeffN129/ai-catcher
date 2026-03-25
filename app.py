import streamlit as st
import json
import os
import requests

# ==========================================
# 🎨 页面基础配置
# ==========================================
st.set_page_config(page_title="AI 聚合资讯台", page_icon="🚀", layout="wide")

# ==========================================
# 🖼️ 网站专属兜底封面图
# ==========================================
DEFAULT_COVER = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=800&auto=format&fit=crop"
WEBSITE_PLACEHOLDERS = {
    "arXiv": "https://images.unsplash.com/photo-1518133910546-b6c2fb7d79e3?q=80&w=800&auto=format&fit=crop",
    "机器之心": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?q=80&w=800&auto=format&fit=crop",
    "量子位": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=800&auto=format&fit=crop",
    "36Kr": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?q=80&w=800&auto=format&fit=crop",
    "科讯头条": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?q=80&w=800&auto=format&fit=crop",
    "央视网·数智": "https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?q=80&w=800&auto=format&fit=crop",
    "赛迪研究院": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop",
    "财新网": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=800&auto=format&fit=crop",
    "钛媒体": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=800&auto=format&fit=crop",
    "MIT Tech Review": "https://images.unsplash.com/photo-1507146153580-69a1fe6d8aa1?q=80&w=800&auto=format&fit=crop",
    "VentureBeat": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop"
}

# ==========================================
# 💅 现代化 CSS 样式
# ==========================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .news-card { background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s ease; margin-bottom: 24px; overflow: hidden; border: 1px solid #f0f0f0; display: flex; flex-direction: column; height: 100%; }
    .news-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .card-thumbnail { width: 100%; aspect-ratio: 16 / 9; overflow: hidden; background-color: #f8f9fa; position: relative; }
    .card-thumbnail img { width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; }
    .card-content { padding: 16px; display: flex; flex-direction: column; flex-grow: 1; }
    .card-title { font-size: 1.1rem; font-weight: 700; color: #1a1a1a; margin-bottom: 8px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-decoration: none; }
    .card-title:hover { color: #2e6bc6; }
    .card-meta { font-size: 0.85rem; color: #666; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    .source-badge { background-color: #eef2ff; color: #4f46e5; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .card-snippet { font-size: 0.9rem; color: #4a4a4a; line-height: 1.6; background-color: #f8fafc; padding: 12px; border-radius: 8px; border-left: 3px solid #10b981; margin-top: auto; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 侧边栏
# ==========================================
st.sidebar.title("🚀 控制台与工具")

# 1. 实时抓取模块 (调用 GitHub)
st.sidebar.markdown("### ⚡ 实时抓取")
if st.sidebar.button("🔄 立即获取最新资讯", use_container_width=True):
    with st.sidebar.status("正在唤醒云端爬虫...", expanded=True) as status:
        url = "https://api.github.com/repos/JeffN129/ai-catcher/actions/workflows/update_news.yml/dispatches"
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token:
            status.update(label="缺少 GITHUB_TOKEN 配置！", state="error")
        else:
            headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {github_token}"}
            try:
                response = requests.post(url, headers=headers, json={"ref": "main"})
                if response.status_code == 204:
                    status.update(label="指令发送成功！", state="complete")
                    st.sidebar.success("✅ 后台已启动！大概需 1~2 分钟，稍后请手动刷新。")
                else:
                    status.update(label="触发失败", state="error")
            except Exception as e:
                status.update(label="请求报错", state="error")

st.sidebar.markdown("---")

# 2. 随身 AI 词典模块 (调用 DeepSeek)
st.sidebar.markdown("### 📖 随身 AI 词典")
st.sidebar.caption("阅读资讯时遇到不懂的专业词汇？问问 AI 吧。")
search_term = st.sidebar.text_input("输入专业术语 (例如：MoE架构, 算力)：")

if st.sidebar.button("🧠 帮我解释", use_container_width=True):
    if not search_term:
        st.sidebar.warning("请输入需要查询的词汇哦。")
    else:
        # 这里前端必须直接读取 API KEY 来进行实时交互
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            st.sidebar.error("缺少 DEEPSEEK_API_KEY，无法调用大模型。")
        else:
            with st.sidebar.spinner(f"正在查阅 {search_term} ..."):
                try:
                    api_url = "https://api.deepseek.com/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一个资深的 AI 领域科普专家。请用简洁明了、通俗易懂的语言，在 100 字以内解释用户提出的 AI 术语或概念。"},
                            {"role": "user", "content": f"请解释：{search_term}"}
                        ]
                    }
                    resp = requests.post(api_url, headers=headers, json=payload, timeout=15)
                    resp.raise_for_status()
                    explanation = resp.json()['choices'][0]['message']['content']
                    st.sidebar.success(explanation)
                except Exception as e:
                    st.sidebar.error(f"查询失败，可能网络超时或余额不足：{e}")

# ==========================================
# 🖥️ 主页面渲染逻辑 (信息流卡片)
# ==========================================
st.title("⚡ AI 前沿资讯聚合台")
st.markdown("实时追踪全球 11 大顶尖科技源头，AI 智能萃取核心价值。")
st.markdown("---")

DATA_FILE = "daily_news.json"
news_data = []

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            news_data = json.load(f)
    except Exception:
        pass

if not news_data:
    st.info("📭 暂无资讯。如果是首次运行，请点击左侧按钮进行抓取。")
else:
    cols_per_row = 3
    for i in range(0, len(news_data), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(news_data):
                article = news_data[i + j]
                
                # 图片兜底逻辑
                final_cover_url = article.get('cover_image_url')
                if not final_cover_url:
                    final_cover_url = WEBSITE_PLACEHOLDERS.get(article.get('source', ''), DEFAULT_COVER)
                
                title = article.get('title', '无标题')
                link = article.get('url', '#')
                source = article.get('source', '未知')
                time_str = article.get('publish_time', '最近')
                snippet = article.get('ai_summary') or article.get('snippet', '无摘要内容')
                
                card_html = f"""
                <div class="news-card">
                    <a href="{link}" target="_blank" class="card-thumbnail">
                        <img src="{final_cover_url}" alt="封面图" loading="lazy">
                    </a>
                    <div class="card-content">
                        <a href="{link}" target="_blank" class="card-title" title="{title}">{title}</a>
                        <div class="card-meta">
                            <span class="source-badge">{source}</span>
                            <span>⏱️ {time_str}</span>
                        </div>
                        <div class="card-snippet">
                            <strong>AI 划重点：</strong> {snippet}
                        </div>
                    </div>
                </div>
                """
                cols[j].markdown(card_html, unsafe_allow_html=True)
