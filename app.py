import streamlit as st
import json
import os
import requests

# ==========================================
# ⚙️ AI 词典 API 配置区域 (DeepSeek 示例)
# ==========================================
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-xxxxxxxxxxxxxxxxxxxx")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL_NAME = "deepseek-chat"

# 1. 页面基本配置：开启宽屏模式
st.set_page_config(
    page_title="AI 前沿资讯站",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 注入自定义 CSS，实现仿 YouTube 的网格排版
st.markdown("""
    <style>
    /* 隐藏顶部留白，让内容更紧凑 */
    .block-container { padding-top: 2rem; max-width: 95%; }

    /* 消除 Streamlit 原生卡片的边距干扰 */
    div[data-testid="stVerticalBlock"] > div { margin-bottom: 0 !important; }

    /* YouTube 单个视频卡片容器 */
    .yt-card {
        margin-bottom: 30px;
        transition: transform 0.2s;
        cursor: pointer;
    }
    .yt-card:hover { transform: scale(1.02); }

    /* 16:9 圆角缩略图 */
    .yt-thumbnail {
        width: 100%;
        aspect-ratio: 16 / 9;
        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%); 
        border-radius: 12px; 
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 50px;
        margin-bottom: 12px;
        color: #fff;
    }

    /* 头像与文字信息的包裹层 */
    .yt-info-wrapper {
        display: flex;
        gap: 12px; 
    }

    /* 频道圆形头像 */
    .yt-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #cc0000; 
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        flex-shrink: 0;
        margin-top: 2px;
    }

    /* 右侧文字区 */
    .yt-text-content {
        display: flex;
        flex-direction: column;
    }

    /* 视频标题 */
    .yt-title {
        font-size: 16px;
        font-weight: 600;
        color: #0f0f0f; 
        line-height: 1.4;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2; 
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* 频道名与播放量（这里用来展示来源和摘要） */
    .yt-metadata {
        font-size: 14px;
        color: #606060; 
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 3; 
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* 超链接去下划线，包裹整个卡片 */
    a.yt-link {
        text-decoration: none;
        color: inherit;
        display: block;
    }

    /* 优化侧边栏解释框的样式 */
    .ai-explanation {
        background-color: #f0f8ff;
        border-left: 4px solid #0056b3;
        padding: 15px;
        border-radius: 4px;
        font-size: 14px;
        line-height: 1.6;
        color: #333;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# 3. 核心功能函数

@st.cache_data
def load_data(file_path="daily_news.json"):
    """加载本地新闻数据"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def explain_ai_term(term):
    """调用大模型 API 解释 AI 名词"""
    if not API_KEY or API_KEY.startswith("sk-xxx"):
        return "⚠️ 请先在代码中配置正确的 API Key！"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "你是一个资深的 AI 工程师。请用通俗易懂的中文，向非专业人士解释用户输入的 AI 名词。语言要生动，最好能举个生活中的例子。字数控制在 150 字左右。"
            },
            {"role": "user", "content": f"请帮我解释这个概念：{term}"}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"查询失败，请检查网络或配置。错误详情：{str(e)}"

# ==========================================
# 🚀 新增功能：一键强制云端更新
# ==========================================
st.sidebar.markdown("### ⚡ 实时抓取")
if st.sidebar.button("🔄 立即获取最新资讯"):
    with st.sidebar.status("正在唤醒云端爬虫...", expanded=True) as status:
        st.write("发送指令到 GitHub...")
        
        # ⚠️ 注意：请把下面的 '你的用户名' 和 '你的仓库名' 替换成你真实的！
        # 比如：'zhangsan' 和 'NewsAggregator'
        url = "https://api.github.com/repos/你的用户名/你的仓库名/actions/workflows/update_news.yml/dispatches"
        
        # 尝试获取 GitHub Token
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token:
            status.update(label="缺少 GITHUB_TOKEN 配置！", state="error")
            st.sidebar.error("请先在 Streamlit Secrets 中配置 GITHUB_TOKEN")
        else:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"Bearer {github_token}"
            }
            data = {"ref": "main"}
            
            try:
                # 触发 GitHub Actions
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 204:
                    status.update(label="指令发送成功！", state="complete")
                    st.sidebar.success("✅ 后台爬虫已启动！\n\n爬取和 AI 总结大约需要 1~2 分钟，请稍后手动刷新本网页。")
                else:
                    status.update(label="触发失败", state="error")
                    st.sidebar.error(f"错误码: {response.status_code}\n信息: {response.text}")
            except Exception as e:
                status.update(label="网络请求失败", state="error")
                st.sidebar.error(f"报错: {str(e)}")
# ==========================================
# 📺 侧边栏：AI 词典与频道过滤
# ==========================================

# --- 新增功能：AI 词典搜索框 ---
st.sidebar.markdown("### 🤖 随身 AI 词典")
# 使用 text_input 接收用户输入
search_term = st.sidebar.text_input(
    label="名词搜索",
    placeholder="遇到陌生的 AI 名词？在这里搜索...",
    label_visibility="collapsed"  # 隐藏顶部的小标题，看起来更简洁
)

# 当用户输入内容并按回车后触发
if search_term:
    with st.sidebar.spinner(f"正在请教资深 AI 工程师关于「{search_term}」的知识..."):
        explanation = explain_ai_term(search_term)

    # 用自定义的 HTML 样式漂亮地展示结果
    st.sidebar.markdown(f"""
        <div class="ai-explanation">
            <b>💡 【{search_term}】</b><br><br>
            {explanation}
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")

# --- 原有功能：频道订阅 ---
st.sidebar.markdown("### ☰ 订阅频道")

data = load_data()
filtered_data = []

if not data:
    st.sidebar.warning("⚠️ 未检测到数据源。")
    st.info("💡 请先运行 Python 抓取脚本生成 `daily_news.json` 文件。")
else:
    all_sources = list(set([item.get('source', '未知') for item in data]))
    selected_sources = st.sidebar.multiselect("内容筛选", options=all_sources, default=all_sources)
    filtered_data = [item for item in data if item.get('source') in selected_sources]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**内容库：** 发现 {len(filtered_data)} 个视频")

# ==========================================
# 📺 主体区域：YouTube 风格信息流
# ==========================================

if filtered_data:
    st.markdown("### ▶️ 最新资讯推荐")
    st.markdown("<br>", unsafe_allow_html=True)

    # 采用 4 列网格（桌面端标准展示）
    cols_per_row = 4

    for i in range(0, len(filtered_data), cols_per_row):
        cols = st.columns(cols_per_row)
        row_data = filtered_data[i: i + cols_per_row]

        for j, item in enumerate(row_data):
            with cols[j]:
                title = item.get('title', '无标题')
                source = item.get('source', '未知来源')
                url = item.get('url', '#')
                summary = item.get('ai_summary', item.get('snippet', '暂无内容'))

                # 提取来源的第一个字作为头像文字
                avatar_char = source[0] if source else "A"

                # 缩略图中心图标
                thumb_icon = "📰"
                if source == "量子位":
                    thumb_icon = "🪐"
                elif source == "arXiv":
                    thumb_icon = "📑"
                elif source == "36Kr":
                    thumb_icon = "🚀"

                # 拼接 HTML
                youtube_card = f"""
                <a href="{url}" target="_blank" class="yt-link">
                    <div class="yt-card">
                        <!-- 上半部分：缩略图 -->
                        <div class="yt-thumbnail">
                            {thumb_icon}
                        </div>
                        <!-- 下半部分：头像 + 文字 -->
                        <div class="yt-info-wrapper">
                            <div class="yt-avatar">{avatar_char}</div>
                            <div class="yt-text-content">
                                <div class="yt-title" title="{title}">{title}</div>
                                <div class="yt-metadata" title="{summary}">
                                    {source} · 刚刚更新<br>
                                    {summary}
                                </div>
                            </div>
                        </div>
                    </div>
                </a>
                """
                st.markdown(youtube_card, unsafe_allow_html=True)
