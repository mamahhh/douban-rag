"""
Frontend authentication module using Firebase.

Provides login/register UI components for Streamlit.
"""

import streamlit as st
import re
import os
import json
import requests
from typing import Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Firebase config from environment
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
FIREBASE_AUTH_DOMAIN = os.environ.get("FIREBASE_AUTH_DOMAIN", "")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")

# Firebase Auth REST API base URL
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1"


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password meets requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter  
    - At least 1 number
    
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "密码至少需要8个字符"
    
    if not re.search(r"[A-Z]", password):
        return False, "密码需要包含至少1个大写字母"
    
    if not re.search(r"[a-z]", password):
        return False, "密码需要包含至少1个小写字母"
    
    if not re.search(r"\d", password):
        return False, "密码需要包含至少1个数字"
    
    return True, ""


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def firebase_sign_up(email: str, password: str) -> dict:
    """Create a new user with email and password."""
    url = f"{FIREBASE_AUTH_URL}/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    return response.json()


def firebase_sign_in(email: str, password: str) -> dict:
    """Sign in with email and password."""
    url = f"{FIREBASE_AUTH_URL}/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    return response.json()


def firebase_refresh_token(refresh_token: str) -> dict:
    """Refresh the ID token using a refresh token."""
    url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post(url, data=payload)
    return response.json()


def get_google_oauth_url() -> str:
    """Generate Google OAuth sign-in URL."""
    redirect_uri = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8501")
    scope = "email profile openid"
    
    return (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={os.environ.get('GOOGLE_CLIENT_ID', '')}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
    )


def init_session_state():
    """Initialize authentication session state."""
    if "auth" not in st.session_state:
        st.session_state.auth = {
            "logged_in": False,
            "id_token": None,
            "refresh_token": None,
            "user": None,
            "remember_me": False,
        }


def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    init_session_state()
    return st.session_state.auth.get("logged_in", False)


def get_auth_token() -> Optional[str]:
    """Get the current ID token for API requests."""
    init_session_state()
    return st.session_state.auth.get("id_token")


def get_current_user_info() -> Optional[dict]:
    """Get current user information."""
    init_session_state()
    return st.session_state.auth.get("user")


def logout():
    """Clear authentication state."""
    st.session_state.auth = {
        "logged_in": False,
        "id_token": None,
        "refresh_token": None,
        "user": None,
        "remember_me": False,
    }


def login_success(response: dict, remember_me: bool = False):
    """Handle successful login/registration."""
    st.session_state.auth = {
        "logged_in": True,
        "id_token": response.get("idToken"),
        "refresh_token": response.get("refreshToken"),
        "user": {
            "uid": response.get("localId"),
            "email": response.get("email"),
            "display_name": response.get("displayName", response.get("email", "").split("@")[0]),
            "email_verified": response.get("emailVerified", False),
        },
        "remember_me": remember_me,
    }


def show_auth_page():
    """
    Display the authentication page with login/register tabs.
    
    Returns True if user is authenticated, False otherwise.
    """
    init_session_state()
    
    if is_authenticated():
        return True
    
    st.title("🔐 欢迎使用 Douban RAG System")
    st.markdown("请登录或注册以继续使用")
    
    # Check for API key configuration
    if not FIREBASE_API_KEY:
        st.error("⚠️ Firebase 未配置。请在 .env 文件中设置 FIREBASE_API_KEY。")
        st.info("详细配置说明请参考 docs/firebase_setup.md")
        return False
    
    tab1, tab2 = st.tabs(["🔑 登录", "📝 注册"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()
    
    # Divider and Google sign-in (if configured)
    google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if google_client_id:
        st.divider()
        st.markdown("**或使用其他方式登录**")
        
        if st.button("🔵 使用 Google 账户登录", use_container_width=True):
            st.info("🔄 正在跳转到 Google 登录...")
            # Note: Full Google OAuth requires proper redirect handling
            # This is typically done with a custom component or external redirect
            st.markdown(f"[点击这里手动登录 Google]({get_google_oauth_url()})")
    
    return False


def show_login_form():
    """Display login form."""
    with st.form("login_form"):
        email = st.text_input("📧 邮箱", placeholder="your@email.com")
        password = st.text_input("🔒 密码", type="password")
        remember_me = st.checkbox("记住我")
        
        submitted = st.form_submit_button("登录", use_container_width=True, type="primary")
        
        if submitted:
            if not email or not password:
                st.error("请输入邮箱和密码")
                return
            
            if not validate_email(email):
                st.error("请输入有效的邮箱地址")
                return
            
            with st.spinner("正在登录..."):
                response = firebase_sign_in(email, password)
            
            if "error" in response:
                error_msg = response["error"].get("message", "登录失败")
                if "INVALID_LOGIN_CREDENTIALS" in error_msg or "EMAIL_NOT_FOUND" in error_msg:
                    st.error("邮箱或密码错误")
                elif "INVALID_EMAIL" in error_msg:
                    st.error("邮箱格式无效")
                else:
                    st.error(f"登录失败: {error_msg}")
            else:
                login_success(response, remember_me)
                st.success("登录成功! ✅")
                st.rerun()


def show_register_form():
    """Display registration form."""
    with st.form("register_form"):
        email = st.text_input("📧 邮箱", placeholder="your@email.com", key="reg_email")
        password = st.text_input("🔒 密码", type="password", key="reg_password")
        password_confirm = st.text_input("🔒 确认密码", type="password", key="reg_password_confirm")
        
        st.caption("""
        **密码要求:**
        - 至少 8 个字符
        - 至少 1 个大写字母
        - 至少 1 个小写字母
        - 至少 1 个数字
        """)
        
        remember_me = st.checkbox("记住我", key="reg_remember")
        
        submitted = st.form_submit_button("注册", use_container_width=True, type="primary")
        
        if submitted:
            if not email or not password or not password_confirm:
                st.error("请填写所有字段")
                return
            
            if not validate_email(email):
                st.error("请输入有效的邮箱地址")
                return
            
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                st.error(error_msg)
                return
            
            if password != password_confirm:
                st.error("两次输入的密码不一致")
                return
            
            with st.spinner("正在注册..."):
                response = firebase_sign_up(email, password)
            
            if "error" in response:
                error_msg = response["error"].get("message", "注册失败")
                if "EMAIL_EXISTS" in error_msg:
                    st.error("该邮箱已被注册,请直接登录")
                elif "WEAK_PASSWORD" in error_msg:
                    st.error("密码强度不够,请使用更复杂的密码")
                elif "INVALID_EMAIL" in error_msg:
                    st.error("邮箱格式无效")
                else:
                    st.error(f"注册失败: {error_msg}")
            else:
                login_success(response, remember_me)
                st.success("注册成功! 🎉")
                st.rerun()


def show_user_sidebar():
    """Display user info and logout button in sidebar."""
    user = get_current_user_info()
    if not user:
        return
    
    st.sidebar.divider()
    st.sidebar.markdown("### 👤 用户信息")
    
    display_name = user.get("display_name", "用户")
    email = user.get("email", "")
    
    st.sidebar.write(f"**{display_name}**")
    st.sidebar.caption(email)
    
    if st.sidebar.button("🚪 退出登录", use_container_width=True):
        logout()
        st.rerun()
