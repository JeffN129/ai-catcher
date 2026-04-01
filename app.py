import streamlit as st
import json
import os
import requests
import hashlib
import html
from datetime import datetime, timedelta
from duckduckgo_search import DDGS

# ==========================================
# 🎨 页面基础配置
# ==========================================
st.set_page_config(page_title="AI 聚合资讯台", page_icon="🐋", layout="wide")

# ==========================================
# 🧠 Session State 状态管理 (页面路由)
# ==========================================
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'query_display' not in st.session_state:
    st.session_state.query_display = ""
if 'show_update_toast' not in st.session_state:
    st.session_state.show_update_toast = False

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
# 💅 深度定制的 CSS 样式 (终极修复版)
# ==========================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* === 🌟 终极搜索框魔法：强制绑定容器 === */
    /* 1. 让 Form 整体透明，去掉默认边框 */
    div[data-testid="stForm"] { 
        border: none !important; 
        padding: 0 !important; 
        background-color: transparent !important; 
    }
    
    /* 2. 【核心修复】将 Form 内部的容器设为 Relative，作为星星的“牢笼” */
    div[data-testid="stForm"] > div:first-child {
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* 3. 输入框本体：加大圆角，右侧留白 65px 防止文字被星星遮挡 */
    div[data-testid="stForm"] [data-testid="stTextInput"] input { 
        border-radius: 40px !important; 
        padding: 0 65px 0 25px !important; 
        height: 60px !important; 
        font-size: 1.15rem !important; 
        border: 1px solid #e2e8f0 !important; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important; 
        background-color: #ffffff !important; 
        width: 100% !important; 
    }
    div[data-testid="stForm"] [data-testid="stTextInput"] input:focus { 
        border-color: #3b82f6 !important; 
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important; 
    }
    
    /* 4. 星星按钮定位：绝对吸附在容器的右侧偏上 */
    div[data-testid="stForm"] [data-testid="stFormSubmitButton"] { 
        position: absolute !important; 
        right: 8px !important; 
        top: 6px !important; 
        margin: 0 !important; 
        padding: 0 !important;
        z-index: 10 !important; 
    }
    
    /* 5. 星星外观：完美的圆形和微发光感 */
    div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button { 
        border-radius: 50% !important; 
        font-size: 1.5rem !important; 
        background-color: transparent !important; 
        border: none !important; 
        color: #f59e0b !important; 
        width: 48px !important;
        height: 48px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        transition: all 0.2s ease !important; 
        box-shadow: none !important;
    }
    div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover { 
        color: #d97706 !important; 
        background-color: #fef3c7 !important; 
        transform: scale(1.05) !important; 
    }

    /* === 卡片瀑布流基础样式 === */
    .news-card { background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s ease; margin-bottom: 24px; overflow: hidden; border: 1px solid #f0f0f0; display: flex; flex-direction: column; height: 100%; }
    .news-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
    .card-thumbnail { width: 100%; aspect-ratio: 16 / 9; overflow: hidden; background-color: #f8f9fa; position: relative; }
    .card-thumbnail img { width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; }
    .card-content { padding: 16px; display: flex; flex-direction: column; flex-grow: 1; }
    .card-title { font-size: 1.1rem; font-weight: 700; color: #1a1a1a; margin-bottom: 8px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-decoration: none; }
    .card-title:hover { color: #2e6bc6; }
    .card-meta { font-size: 0.85rem; color: #666; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    .source-badge { background-color: #eef2ff; color: #4f46e5; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; white-space: nowrap; }
    .card-snippet { font-size: 0.9rem; color: #4a4a4a; line-height: 1.6; background-color: #f8fafc; padding: 12px; border-radius: 8px; border-left: 3px solid #10b981; margin-top: auto; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 全局侧边栏 (坚定守护你的 AI 词典)
# ==========================================
st.sidebar.title("🚀 工具箱")
st.sidebar.markdown("### 📖 随身 AI 词典")
st.sidebar.caption("遇到生僻的 AI 术语？随时在此查阅。")

search_term = st.sidebar.text_input("输入专业术语 (如：MoE, 算力)：", key="dictionary_input")
if st.sidebar.button("🧠 帮我解释", use_container_width=True):
    if not search_term: 
        st.sidebar.warning("请输入需要查询的词汇哦。")
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key: 
            st.sidebar.error("缺少 DEEPSEEK_API_KEY，无法调用大模型。")
        else:
            with st.sidebar.spinner(f"正在查阅 {search_term} ..."):
                try:
                    api_url = "https://api.deepseek.com/chat/completions"
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "你是一个资深的 AI 领域科普专家。请在100字内通俗解释AI术语。"}, {"role": "user", "content": f"请解释：{search_term}"}]}
                    resp = requests.post(api_url, headers=headers, json=payload, timeout=15)
                    resp.raise_for_status()
                    st.sidebar.success(resp.json()['choices'][0]['message']['content'])
                except Exception as e: 
                    st.sidebar.error(f"查询失败：{e}")

# ==========================================
# ⚙️ 核心逻辑：后台更新唤醒器
# ==========================================
def trigger_github_update():
    url = "https://api.github.com/repos/JeffN129/ai-catcher/actions/workflows/update_news.yml/dispatches"
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        try: requests.post(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {github_token}"}, json={"ref": "main"})
        except: pass 

# ==========================================
# ⚙️ 核心逻辑：执行检索与状态切换
# ==========================================
def execute_search(search_type="custom", keyword=""):
    if search_type == "latest":
        DATA_FILE = "daily_news.json"
        filtered_results = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    all_news = json.load(f)
                
                now = datetime.now()
                for item in all_news:
                    time_str = item.get('publish_time', '')
                    try:
                        pub_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                        days_old = (now - pub_time).days
                    except:
                        days_old = 3
                    
                    if days_old <= 14:
                        heat = 60 + max(0, (14 - days_old) * 2) 
                        title_upper = item.get('title', '').upper()
                        hot_words = ['SORA', 'GPT', '大模型', 'OPENAI', '芯片', 'NVIDIA', '英伟达', 'AGI']
                        if any(w in title_upper for w in hot_words):
                            heat += 15
                        
                        url_hash = int(hashlib.md5(item.get('url', '').encode()).hexdigest()[:4], 16)
                        heat += (url_hash % 16)
                        item['heat_score'] = min(99, heat)
                        filtered_results.append(item)
                        
                filtered_results.sort(key=lambda x: x.get('heat_score', 0), reverse=True)
                st.session_state.search_results = filtered_results
            except Exception as e:
                st.error(f"读取数据失败: {e}")
        else:
            st.session_state.search_results = []
            
        st.session_state.query_display = "🔥 近两周 AI 热门风向标"
        st.session_state.page = "results"
        
    elif search_type == "custom" and keyword.strip():
        with st.spinner(f"正在全网深潜检索：{keyword} ..."):
            DOMAIN_TO_NAME = {
                "arxiv.org": "arXiv", "jiqizhixin.com": "机器之心", "qbitai.com": "量子位",
                "36kr.com": "36Kr", "pubscholar.cn": "科讯头条", "cctv.com": "央视网·数智",
                "ccidgroup.com": "赛迪研究院", "caixin.com": "财新网", "tmtpost.com": "钛媒体",
                "technologyreview.com": "MIT Tech Review", "venturebeat.com": "VentureBeat"
            }
            sites_query = " OR ".join([f"site:{domain}" for domain in DOMAIN_TO_NAME.keys()])
            formatted_query = f"{keyword} ({sites_query})"
            
            raw_results = None
            try:
                raw_results = DDGS().text(keywords=formatted_query, max_results=9)
                if not raw_results: raise ValueError("Empty")
            except Exception:
                try:
                    fallback_query = f"{keyword} AI 资讯"
                    raw_results = DDGS().text(keywords=fallback_query, max_results=9)
                    if raw_results:
                        st.toast("专属信息源暂无匹配，已为您智能扩展至全网检索", icon="🔍")
                except Exception as e:
                    st.error(f"网络检索接口受限，请稍后再试。报错详情: {e}")
            
            adapted_results = []
            if raw_results:
                for item in raw_results:
                    href = item.get('href', '')
                    source_name = "全网检索"
                    for domain, name in DOMAIN_TO_NAME.items():
                        if domain in href:
                            source_name = name
                            break
                            
                    adapted_results.append({
                        'source': source_name, 
                        'title': item.get('title', '无标题'), 
                        'url': href,
                        'snippet': item.get('body', '暂无内容'), 
                        'publish_time': '归档', 
                        'cover_image_url': None
                    })
            st.session_state.search_results = adapted_results
            st.session_state.query_display = f"🔍 智能检索结果：{keyword}"
            st.session_state.page = "results"

def return_home():
    st.session_state.page = "home"

# ==========================================
# 🖥️ 页面一：极简 AI 搜索主页
# ==========================================
if st.session_state.page == 'home':
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3rem; color: #1f2937; margin-bottom: 20px;'>🐋 今天有什么关于 AI 的问题可以帮到你？</h1>", unsafe_allow_html=True)
    
    col_left, col_main, col_right = st.columns([1, 2, 1])
    with col_main:
        with st.form(key='search_form'):
            user_input = st.text_input("搜索", placeholder="搜索专属信息源的最新资讯...", label_visibility="collapsed")
            submit_search = st.form_submit_button("✨")
            
            if submit_search:
                if user_input:
                    execute_search("custom", user_input)
                    st.rerun()
                else:
                    st.warning("请先输入你想检索的关键词哦！")
        
        st.markdown("<br>", unsafe_allow_html=True)
        _, center_btn_col, _ = st.columns([1.2, 1.5, 1.2]) 
        with center_btn_col:
            if st.button("📰 看看最新动态", use_container_width=True):
                trigger_github_update()
                execute_search("latest")
                st.session_state.show_update_toast = True 
                st.rerun()
                
    st.markdown("<br><br><br><br><p style='text-align:center; color:#9ca3af; font-size:0.9rem;'>Powered by DuckDuckGo & DeepSeek · 数据抓取自 11 个全球顶尖源流</p>", unsafe_allow_html=True)

# ==========================================
# 🖥️ 页面二：瀑布流结果展示页
# ==========================================
elif st.session_state.page == 'results':
    
    if st.session_state.show_update_toast:
        st.toast("✅ 后台云端爬虫已唤醒！最新资讯将在 1~2 分钟后静默就绪。", icon="🚀")
        st.session_state.show_update_toast = False
        
    nav_col1, nav_col2 = st.columns([1, 10])
    with nav_col1:
        st.button("← 返回首页", on_click=return_home)
    with nav_col2:
        st.markdown(f"<h3 style='margin-top:0;'>{st.session_state.query_display}</h3>", unsafe_allow_html=True)
        
    st.markdown("---")
    news_data = st.session_state.search_results
    
    if not news_data:
        st.info("📭 抱歉，没有找到匹配的近期数据。换个词试试？")
    else:
        cols_per_row = 3
        for i in range(0, len(news_data), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(news_data):
                    article = news_data[i + j]
                    
                    # 🌟 关键防御：使用 html.escape() 防止 DuckDuckGo 携带的杂乱标签破坏结构！
                    title_safe = html.escape(article.get('title', '无标题'))
                    link_safe = html.escape(article.get('url', '#'))
                    source_safe = html.escape(article.get('source', '未知'))
                    time_str_safe = html.escape(article.get('publish_time', '最近'))
                    snippet_safe = html.escape(article.get('ai_summary') or article.get('snippet', '无摘要内容'))
                    
                    # 🌟 核心定制：当数据来源是"全网检索"时，采用专用的【极简左右排版】
                    if source_safe == "全网检索":
                        card_html = f"""
                        <div class="news-card" style="padding: 20px; flex-direction: row; align-items: flex-start; gap: 16px;">
                            <div style="flex-shrink: 0;">
                                <span class="source-badge" style="background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;">🔍 全网检索</span>
                            </div>
                            <div style="flex-grow: 1; display: flex; flex-direction: column; gap: 8px;">
                                <span style="color: #64748b; font-size: 0.85rem; font-weight: 500;">⏱️ {time_str_safe}</span>
                                <a href="{link_safe}" target="_blank" style="text-decoration: none; color: #334155; font-size: 0.95rem; line-height: 1.6; background-color: #f8fafc; padding: 12px; border-radius: 8px; border-left: 3px solid #cbd5e1;">
                                    {snippet_safe}
                                </a>
                            </div>
                        </div>
                        """
                    else:
                        # 普通站点的标准 YouTube 卡片样式
                        final_cover_url = article.get('cover_image_url')
                        if not final_cover_url:
                            final_cover_url = WEBSITE_PLACEHOLDERS.get(source_safe, DEFAULT_COVER)
                            
                        heat_badge = f'<span style="color: #ef4444; font-weight: 700; margin-right: 12px;">🔥 热度 {article.get("heat_score", 85)}</span>' if 'heat_score' in article else ''
                        
                        card_html = f"""
                        <div class="news-card">
                            <a href="{link_safe}" target="_blank" class="card-thumbnail">
                                <img src="{final_cover_url}" alt="封面图" loading="lazy">
                            </a>
                            <div class="card-content">
                                <a href="{link_safe}" target="_blank" class="card-title" title="{title_safe}">{title_safe}</a>
                                <div class="card-meta">
                                    <span class="source-badge">{source_safe}</span>
                                    <div>
                                        {heat_badge}
                                        <span>⏱️ {time_str_safe}</span>
                                    </div>
                                </div>
                                <div class="card-snippet">
                                    <strong>核心摘要：</strong> {snippet_safe}
                                </div>
                            </div>
                        </div>
                        """
                    
                    cols[j].markdown(card_html, unsafe_allow_html=True)
