import streamlit as st
import requests
import json
import os

# Import authentication module
from auth import (
    show_auth_page, 
    is_authenticated, 
    get_auth_token, 
    show_user_sidebar,
    init_session_state,
    get_current_user_info
)

# Initialize auth session state
init_session_state()

def login_as_demo():
    """Login as a demo user without Firebase."""
    st.session_state.auth = {
        "logged_in": True,
        "id_token": "demo-token",
        "refresh_token": None,
        "user": {
            "uid": "demo-user",
            "email": "demo@example.com",
            "display_name": "Demo User",
            "email_verified": True,
        },
        "remember_me": False,
    }
    st.success("已进入演示模式!")
    st.rerun()

# Constants - Use environment variable for Cloud Run, default to localhost for local dev
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api"

st.set_page_config(
    page_title="Douban RAG System",
    page_icon="📚",
    layout="wide"
)

# Check authentication first - show login page if not authenticated
if not is_authenticated():
    # Check for demo login request from auth page
    if st.session_state.get("request_demo_login", False):
        st.session_state["request_demo_login"] = False # Reset flag
        login_as_demo()
    
    show_auth_page()
    st.stop()

# User is authenticated - show main app
st.title("Douban RAG System 📚")


def get_auth_headers():
    """Get authorization headers for API requests."""
    token = get_auth_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def process_upload_with_progress(uploaded_file):
    """Upload file with streaming progress updates."""
    # Determine content type
    if uploaded_file.name.endswith('.xlsx'):
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content_type = "text/csv"
    
    # Create progress containers
    progress_bar = st.progress(0)
    status_text = st.empty()
    eta_text = st.empty()
    
    try:
        # Use the streaming endpoint with authentication
        files = {"file": (uploaded_file.name, uploaded_file, content_type)}
        response = requests.post(
            f"{API_URL}/upload/stream",
            files=files,
            headers=get_auth_headers(),
            stream=True
        )
        
        if response.status_code != 200:
            st.error(f"错误: {response.text}")
            return None
        
        result = None
        
        # Process SSE events
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        stage = data.get('stage', '')
                        progress = data.get('progress', 0)
                        message = data.get('message', '')
                        eta = data.get('eta', '')
                        
                        # Update progress bar
                        progress_bar.progress(progress / 100)
                        
                        # Update status text with icon based on stage
                        if stage == 'parsing':
                            status_text.markdown(f"📄 **解析中**: {message}")
                        elif stage == 'indexing':
                            status_text.markdown(f"🔍 **索引中**: {message}")
                        elif stage == 'complete':
                            status_text.markdown(f"✅ **{message}**")
                            result = data
                        elif stage == 'error':
                            status_text.markdown(f"❌ **错误**: {message}")
                            return None
                        
                        # Update ETA
                        if eta:
                            eta_text.markdown(f"⏱️ 预计剩余时间: **{eta}**")
                        
                        if stage == 'complete':
                            eta_text.markdown(f"⏱️ 总用时: **{data.get('total_time', '')}**")
                            
                    except json.JSONDecodeError:
                        continue
        
        # Clear progress indicators after completion
        progress_bar.empty()
        
        return result
        
    except Exception as e:
        st.error(f"连接错误: {e}")
        return None


# Sidebar for configuration & Upload

def display_upload_result(result, success_msg_template="✅ 成功导入 {count} 条记录!"):
    """Helper to display upload results and media type breakdown."""
    if not result:
        return

    count = result.get('documents_processed', 0)
    st.success(success_msg_template.format(count=count))
    
    # Show media type breakdown
    media_types = result.get('media_types', {})
    if media_types:
        st.write("**导入内容:**")
        type_names = {
            "movie": "电影",
            "book": "书籍", 
            "music": "音乐",
            "game": "游戏",
            "drama": "舞台剧",
            "unknown": "其他"
        }
        for mt, count in media_types.items():
            name = type_names.get(mt, mt)
            st.write(f"  - {name}: {count} 条")


# Sidebar for configuration & Upload
with st.sidebar:
    # Show user info and logout button
    show_user_sidebar()
    
    st.header("数据管理")
    
    # Check if this is a demo user
    user = get_current_user_info()
    is_demo = user and user.get("uid") == "demo-user"
    
    if is_demo:
        st.info("演示模式: 仅限使用默认数据。")
        if st.button("加载默认演示数据", type="primary", use_container_width=True):
            # Locate the demo file relative to frontend/app.py
            # Assuming we run from frontend/ or root, try to find it
            demo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/demo.xlsx"))
            
            if os.path.exists(demo_path):
                with open(demo_path, "rb") as f:
                    # Create a file-like object with a name attribute for requests
                    import io
                    file_content = f.read()
                    file_obj = io.BytesIO(file_content)
                    file_obj.name = "demo.xlsx"
                    
                    # Manually trigger upload
                    result = process_upload_with_progress(file_obj)
                    display_upload_result(result, "成功加载演示数据! ({count} 条记录)")
            else:
                st.error(f"无法找到演示数据文件: {demo_path}")
    else:
        # Standard upload button logic (Only show if NOT demo)
        uploaded_file = st.file_uploader(
            "上传豆瓣数据 (.csv 或 .xlsx)", 
            type=['csv', 'xlsx'],
            help="支持豆伴导出的 Excel 文件或单独的 CSV 文件",
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            if st.button("开始导入", type="primary", key="upload_btn"):
                result = process_upload_with_progress(uploaded_file)
                display_upload_result(result)

    st.divider()
    
    st.header("系统状态")
    if st.button("检查后端"):
        try:
            response = requests.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                st.success("后端在线 ✅")
            else:
                st.error(f"后端状态: {response.status_code}")
        except:
            st.error("后端离线 ❌")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("询问你的豆瓣记录..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat", 
                    json={"message": prompt},
                    headers=get_auth_headers()
                )
                if response.status_code == 200:
                    bot_reply = response.json().get("response")
                    st.markdown(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                else:
                    error_msg = f"错误: {response.text}"
                    st.error(error_msg)
            except Exception as e:
                st.error(f"连接后端失败: {e}")
