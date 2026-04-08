import streamlit as st
import json
import os
import requests
import hashlib
import html
from datetime import datetime, timedelta
from duckduckgo_search import DDGS

# ==========================================
# 🎨 页面配置与状态持久化 (解决刷新丢失问题)
# ==========================================
st.set_page_config(page_title="AI 聚合资讯台", page_icon="🐋", layout="wide")

# 核心状态管理：检查 URL 参数，确保刷新时不回首页
params = st.query_params
if 'page' not in st.session_state:
    st.session_state.page = params.get("p", "home")
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'is_latest_view' not in st.session_state:
    st.session_state.is_latest_view = False
if 'keyword_explanation' not in st.session_state:
    st.session_state.keyword_explanation = None

# ==========================================
# 🖼️ 全源专属封面图配置
# ==========================================
DEFAULT_COVER = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=800&auto=format&fit=crop"
WEBSITE_PLACEHOLDERS = {
    "arXiv": "https://images.unsplash.com/photo-1518133910546-b6c2fb7d79e3?q=80&w=800&auto=format&fit=crop",
    "Hacker News": "https://images.unsplash.com/photo-1516259762381-22954d7d3ad2?q=80&w=800&auto=format&fit=crop",
    "GitHub": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=800&auto=format&fit=crop",
    "The Decoder": "https://images.unsplash.com/photo-1507146456680-607246479f64?q=80&w=800&auto=format&fit=crop",
    "VentureBeat": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
    "机器之心": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?q=80&w=800&auto=format&fit=crop",
    "量子位": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=800&auto=format&fit=crop",
    "36Kr": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?q=80&w=800&auto=format&fit=crop",
    "钛媒体": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=800&auto=format&fit=crop",
    "MIT Tech Review": "https://images.unsplash.com/photo-1507146153580-69a1fe6d8aa1?q=80&w=800&auto=format&fit=crop",
    "财新网": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=800&auto=format&fit=crop",
    "央视网·数智": "https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?q=80&w=800&auto=format&fit=crop"
}

# ==========================================
# 💅 深度定制 CSS：药丸一体化搜索框 (物理锁定)
# ==========================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* 🌟 核心魔法：胶囊容器，将输入框和 ✨ 按钮横向绑定 */
    div[data-testid="stForm"] > div:first-child { 
        display: flex !important; 
        flex-direction: row !important; 
        align-items: center !important; 
        background-color: #ffffff !important; 
        border: 1px solid #e2e8f0 !important; 
        border-radius: 40px !important; 
        box-shadow: 0 4px 14px rgba(0,0,0,0.06) !important; 
        padding: 6px 14px 6px 28px !important; 
        gap: 0 !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stForm"] > div:first-child:focus-within { border-color: #3b82f6 !important; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important; }
    
    /* 输入框样式重塑 */
    div[data-testid="stForm"] div[data-testid="stTextInput"] { flex-grow: 1 !important; margin: 0 !important; border: none !important; }
    div[data-testid="stForm"] div[data-testid="stTextInput"] input { border: none !important; box-shadow: none !important; background: transparent !important; font-size: 1.2rem !important; height: 50px !important; color: #1e293b !important; }
    
    /* ✨ 按钮样式：无背景透明化 */
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] { margin: 0 !important; padding: 0 !important; }
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button { 
        border: none !important; background: transparent !important; box-shadow: none !important; 
        font-size: 1.8rem !important; color: #f59e0b !important; padding: 0 8px !important; 
        transition: transform 0.2s ease !important; line-height: 1 !important;
    }
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover { transform: scale(1.2) rotate(10deg); color: #d97706 !important; background-color: transparent !important; }

    /* 🧠 AI 词典合并卡片样式 */
    .dictionary-hero {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #bfdbfe;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 32px;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.08);
        position: relative;
        overflow: hidden;
    }
    .dictionary-hero::before {
        content: '🧠';
        position: absolute;
        right: -10px;
        bottom: -10px;
        font-size: 5rem;
        opacity: 0.1;
    }
    .dict-term { color: #1e40af; font-size: 1.4rem; font-weight: 800; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
    .dict-content { color: #1e3a8a; font-size: 1.05rem; line-height: 1.7; }

    /* 卡片基础样式 */
    .news-card { background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s ease; margin-bottom: 24px; overflow: hidden; border: 1px solid #f0f0f0; display: flex; flex-direction: column; height: 100%; }
    .news-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .card-thumbnail { width: 100%; aspect-ratio: 16 / 9; overflow: hidden; background-color: #f8f9fa; position: relative; }
    .card-thumbnail img { width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; }
    .card-content { padding: 16px; display: flex; flex-direction: column; flex-grow: 1; }
    .card-title { font-size: 1.1rem; font-weight: 700; color: #1a1a1a; margin-bottom: 10px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-decoration: none; }
    .source-badge { background-color: #eef2ff; color: #4f46e5; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; white-space: nowrap; }
    .card-snippet { font-size: 0.95rem; color: #4a4a4a; line-height: 1.6; background-color: #f8fafc; padding: 12px; border-radius: 8px; border-left: 3px solid #10b981; margin-top: auto; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 侧边栏：仅保留控制功能
# ==========================================
with st.sidebar:
    st.title("🚀 控制台")
    st.caption("刷新浏览器也不会丢失当前浏览进度。")
    if st.button("🏠 返回首页", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.keyword_explanation = None
        st.query_params.clear()
        st.rerun()

# ==========================================
# ⚙️ 核心逻辑：执行检索并同步 URL 状态 (集成 AI 释义)
# ==========================================
def run_search(search_type="custom", keyword=""):
    st.session_state.keyword_explanation = None # 重置
    
    if search_type == "latest":
        st.session_state.is_latest_view = True
        if os.path.exists("daily_news.json"):
            with open("daily_news.json", "r", encoding="utf-8") as f:
                st.session_state.search_results = json.load(f)
    elif search_type == "custom" and keyword:
        st.session_state.is_latest_view = False
        
        # 🌟 合并逻辑：先获取 AI 对词汇的解释
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if api_key:
            try:
                # 即使搜索报错也不影响后续资讯展示，所以包在 try 里
                resp = requests.post("https://api.deepseek.com/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, json={
                    "model": "deepseek-chat", 
                    "messages": [
                        {"role": "system", "content": "你是一个资深的 AI 领域科普专家。请在100字内通俗解释用户提供的 AI 术语。如果该词与 AI 无关，请简要说明其通用定义。"}, 
                        {"role": "user", "content": keyword}
                    ]
                }, timeout=10)
                st.session_state.keyword_explanation = {
                    "term": keyword,
                    "content": resp.json()['choices'][0]['message']['content'].strip()
                }
            except:
                pass

        # 获取资讯
        with st.spinner(f"正在全网搜索：{keyword}..."):
            try:
                raw = DDGS().text(keywords=f"{keyword} AI 最新资讯", max_results=9)
                st.session_state.search_results = [{'source': '全网检索', 'title': r['title'], 'url': r['href'], 'ai_summary': r['body'], 'publish_time': '实时', 'cover_image_url': None} for r in raw]
            except: st.error("检索请求暂时限流。")
    
    st.session_state.page = "results"
    st.query_params["p"] = "results" 

def go_home():
    st.session_state.page = "home"
    st.session_state.keyword_explanation = None
    st.query_params.clear()

# ==========================================
# 🖥️ 页面模式逻辑
# ==========================================
if st.session_state.page == 'home':
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #1f2937;'>🐋 今天有什么关于 AI 的问题可以帮到你？</h1>", unsafe_allow_html=True)
    
    _, col_main, _ = st.columns([1, 2.2, 1])
    with col_main:
        with st.form(key='search_form'):
            u_input = st.text_input("S", placeholder="搜索专属源最新 AI 资讯...", label_visibility="collapsed")
            if st.form_submit_button("✨"):
                if u_input: 
                    run_search("custom", u_input)
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        _, btn_col, _ = st.columns([1, 1.5, 1])
        with btn_col:
            if st.button("📰 看看最新动态", use_container_width=True):
                run_search("latest")
                st.rerun()

elif st.session_state.page == 'results':
    nav_c, title_c = st.columns([1.5, 10])
    with nav_c: st.button("← 返回首页", on_click=go_home)
    with title_c: 
        st.title("🔍 资讯情报站")
        if st.session_state.is_latest_view:
            mode = st.radio("频道：", ["🔥 热门榜单 (Top 14D)", "⚡ 最新前沿 (Top 3D)"], horizontal=True, label_visibility="collapsed")
            raw_data = st.session_state.search_results
            now = datetime.now()
            
            def get_days(t_str):
                try: return (now - datetime.strptime(t_str, '%Y-%m-%d %H:%M')).days
                except: return 1
            
            if "最新" in mode:
                display_data = sorted([item for item in raw_data if get_days(item.get('publish_time','')) <= 3], key=lambda x: x.get('heat_score',0), reverse=True)
            else:
                display_data = sorted(raw_data, key=lambda x: x.get('heat_score',0), reverse=True)
        else:
            display_data = st.session_state.search_results

    st.markdown("---")

    # 🌟 核心新功能：展示 AI 词典释义 (合并版)
    if st.session_state.keyword_explanation:
        dict_data = st.session_state.keyword_explanation
        st.markdown(f"""
        <div class="dictionary-hero">
            <div class="dict-term"><span>🧠</span> AI 术语解读: {dict_data['term']}</div>
            <div class="dict-content">{dict_data['content']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if not display_data:
        st.info("📭 暂无匹配内容，请尝试更换关键词。")
    else:
        # 瀑布流展示
        rows = st.columns(3)
        for idx, item in enumerate(display_data):
            article = item 
            t_safe = html.escape(article['title'])
            s_safe = html.escape(article.get('ai_summary', ''))
            source = article['source']
            
            if source == "全网检索":
                card_html = f"""
                <div class="news-card" style="padding: 20px; flex-direction: row; gap: 16px; border-left: 5px solid #cbd5e1;">
                    <div style="flex-shrink: 0;"><span class="source-badge" style="background: #f1f5f9; color: #475569;">🔍 全网</span></div>
                    <div style="flex-grow: 1;">
                        <div style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 5px;">⏱️ {article['publish_time']}</div>
                        <a href="{article['url']}" target="_blank" style="text-decoration: none; color: #334155; font-size: 0.95rem; line-height: 1.5;">{s_safe}</a>
                    </div>
                </div>"""
            else:
                cover = article.get('cover_image_url') or WEBSITE_PLACEHOLDERS.get(source, DEFAULT_COVER)
                card_html = f"""
                <div class="news-card">
                    <a href="{article['url']}" target="_blank" class="card-thumbnail"><img src="{cover}"></a>
                    <div class="card-content">
                        <a href="{article['url']}" target="_blank" class="card-title" title="{t_safe}">{t_safe}</a>
                        <div class="card-meta"><span class="source-badge">{source}</span> <div>🔥 {article.get('heat_score',95)} ⏱️ {article['publish_time']}</div></div>
                        <div class="card-snippet"><strong>AI 深度精析：</strong>{s_safe}</div>
                    </div>
                </div>"""
            rows[idx % 3].markdown(card_html, unsafe_allow_html=True)
