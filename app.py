import streamlit as st
import json
import os
import requests
from duckduckgo_search import DDGS

# ==========================================
# 🎨 页面基础配置
# ==========================================
st.set_page_config(page_title="AI 聚合资讯台", page_icon="🐋", layout="wide")

# ==========================================
# 🧠 Session State 状态管理 (页面路由)
# ==========================================
if 'page' not in st.session_state:
    st.session_state.page = 'home'  # 默认首页
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'query_display' not in st.session_state:
    st.session_state.query_display = ""

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
    "VentureBeat": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
    "实时检索": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop"
}

# ==========================================
# 💅 深度定制的 CSS 样式
# ==========================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stTextInput"] input { border-radius: 30px !important; padding: 20px 24px !important; font-size: 1.25rem !important; border: 1px solid #e0e0e0 !important; box-shadow: 0 8px 24px rgba(0,0,0,0.06) !important; transition: all 0.3s ease; background-color: #ffffff; }
    div[data-testid="stTextInput"] input:focus { border-color: #3b82f6 !important; box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2) !important; }
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
st.sidebar.markdown("### ⚡ 实时抓取")
if st.sidebar.button("🔄 立即获取最新资讯", use_container_width=True):
    with st.sidebar.status("正在唤醒云端爬虫...", expanded=True) as status:
        url = "https://api.github.com/repos/JeffN129/ai-catcher/actions/workflows/update_news.yml/dispatches"
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token: status.update(label="缺少 GITHUB_TOKEN 配置！", state="error")
        else:
            headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"Bearer {github_token}"}
            try:
                response = requests.post(url, headers=headers, json={"ref": "main"})
                if response.status_code == 204:
                    status.update(label="指令发送成功！", state="complete")
                    st.sidebar.success("✅ 后台已启动！大概需 1~2 分钟，稍后请点击【看看最新动态】。")
                else: status.update(label="触发失败", state="error")
            except Exception as e: status.update(label="请求报错", state="error")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 随身 AI 词典")
search_term = st.sidebar.text_input("输入专业术语 (例如：MoE架构, 算力)：")
if st.sidebar.button("🧠 帮我解释", use_container_width=True):
    if not search_term: st.sidebar.warning("请输入需要查询的词汇哦。")
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key: st.sidebar.error("缺少 DEEPSEEK_API_KEY，无法调用大模型。")
        else:
            with st.sidebar.spinner(f"正在查阅 {search_term} ..."):
                try:
                    api_url = "https://api.deepseek.com/chat/completions"
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "你是一个资深的 AI 领域科普专家。请在100字内解释AI术语。"}, {"role": "user", "content": f"请解释：{search_term}"}]}
                    resp = requests.post(api_url, headers=headers, json=payload, timeout=15)
                    resp.raise_for_status()
                    st.sidebar.success(resp.json()['choices'][0]['message']['content'])
                except Exception as e: st.sidebar.error(f"查询失败：{e}")

# ==========================================
# ⚙️ 核心逻辑：执行检索与状态切换
# ==========================================
def execute_search(search_type="custom", keyword=""):
    if search_type == "latest":
        DATA_FILE = "daily_news.json"
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                st.session_state.search_results = json.load(f)
        else:
            st.session_state.search_results = []
        st.session_state.query_display = "📰 今日 AI 全网聚合动态"
        st.session_state.page = "results"
        
    elif search_type == "custom" and keyword.strip():
        with st.spinner(f"正在全网深潜检索：{keyword} ..."):
            formatted_query = f"{keyword} AI 人工智能 最新"
            try:
                raw_results = DDGS().text(keywords=formatted_query, timelimit='d', max_results=9)
                adapted_results = []
                if raw_results:
                    for item in raw_results:
                        adapted_results.append({
                            'source': '实时检索', 'title': item.get('title', '无标题'), 'url': item.get('href', '#'),
                            'snippet': item.get('body', '暂无内容'), 'publish_time': '过去 24 小时内', 'cover_image_url': None
                        })
                st.session_state.search_results = adapted_results
                st.session_state.query_display = f"🔍 深度检索结果：{keyword}"
                st.session_state.page = "results"
            except Exception as e:
                st.error(f"网络检索接口受限，请稍后再试。报错详情: {e}")

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
        user_input = st.text_input("搜索", placeholder="搜索全网最新 AI 资讯...", label_visibility="collapsed", key="search_input")
        
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1.5, 1.5, 1])
        with btn_col2:
            if st.button("🚀 深度检索", use_container_width=True):
                if user_input:
                    execute_search("custom", user_input)
                    st.rerun() # 🌟 关键修复：强制刷新，瞬间切换页面！
                else:
                    st.warning("请先输入你想检索的关键词哦！")
        with btn_col3:
            if st.button("📰 看看最新动态", use_container_width=True):
                execute_search("latest")
                st.rerun() # 🌟 关键修复：强制刷新，瞬间切换页面！
                
    st.markdown("<br><br><br><br><p style='text-align:center; color:#9ca3af; font-size:0.9rem;'>Powered by DuckDuckGo & DeepSeek · 数据抓取自 11 个全球顶尖源流</p>", unsafe_allow_html=True)

# ==========================================
# 🖥️ 页面二：瀑布流结果展示页
# ==========================================
elif st.session_state.page == 'results':
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
                                <strong>核心摘要：</strong> {snippet}
                            </div>
                        </div>
                    </div>
                    """
                    cols[j].markdown(card_html, unsafe_allow_html=True)
