import streamlit as st
import json
from google import genai
from google.genai import types 
from supabase import create_client, Client

# =====================================================================
# 1. 페이지 설정 및 초기화
# =====================================================================
st.set_page_config(page_title="파이의 AI 멀티버스", page_icon="📱", layout="centered")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if st.session_state.theme == "light":
    theme_css = """
    <style>
    [data-testid="stAppViewContainer"] { background-color: #F4F4F9 !important; }
    [data-testid="stHeader"] { background-color: #F4F4F9 !important; }
    [data-testid="stBottom"] > div { background-color: #F4F4F9 !important; }
    [data-testid="stChatInput"] { background-color: #FFFFFF !important; border: 1px solid #DDDDDD !important; border-radius: 10px !important; }
    [data-testid="stChatInput"] div { background-color: transparent !important; } 
    [data-testid="stChatInput"] textarea { 
        background-color: transparent !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important; caret-color: #000000 !important; 
    }
    [data-testid="stChatInput"] textarea::placeholder { color: #888888 !important; -webkit-text-fill-color: #888888 !important; }
    [data-testid="stChatInput"] svg { fill: #000000 !important; } 
    div[data-baseweb="popover"] > div { background-color: #FFFFFF !important; border: 1px solid #DDDDDD !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; }
    div[data-testid="stPopoverBody"] { background-color: #FFFFFF !important; color: #1E1E1E !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, li, .kakao-name { color: #1E1E1E !important; }
    .stButton>button, .stPopover>div>button { background-color: #FFFFFF !important; color: #1E1E1E !important; border: 1px solid #DDDDDD !important; }
    .stButton>button:hover, .stPopover>div>button:hover { background-color: #f7e600 !important; color: #000000 !important; border: 1px solid #f7e600 !important; }
    .kakao-status, .kakao-section-title { color: #888888 !important; }
    .kakao-divider { border-bottom: 1px solid rgba(0,0,0,0.08) !important; }
    </style>
    """
else:
    theme_css = """
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    [data-testid="stBottom"] > div { background-color: #0E1117 !important; }
    [data-testid="stChatInput"] { background-color: #262730 !important; border: 1px solid #444444 !important; border-radius: 10px !important; }
    [data-testid="stChatInput"] div { background-color: transparent !important; } 
    [data-testid="stChatInput"] textarea { 
        background-color: transparent !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; caret-color: #FFFFFF !important; 
    }
    [data-testid="stChatInput"] textarea::placeholder { color: #AAAAAA !important; -webkit-text-fill-color: #AAAAAA !important; }
    [data-testid="stChatInput"] svg { fill: #FFFFFF !important; } 
    div[data-baseweb="popover"] > div { background-color: #262730 !important; border: 1px solid #444444 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important; }
    div[data-testid="stPopoverBody"] { background-color: #262730 !important; color: #FAFAFA !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, li, .kakao-name { color: #FAFAFA !important; }
    .stButton>button, .stPopover>div>button { background-color: #262730 !important; color: #FAFAFA !important; border: 1px solid #444444 !important; }
    .stButton>button:hover, .stPopover>div>button:hover { background-color: #f7e600 !important; color: #000000 !important; border: 1px solid #f7e600 !important; }
    .kakao-status, .kakao-section-title { color: #AAAAAA !important; }
    .kakao-divider { border-bottom: 1px solid rgba(255,255,255,0.1) !important; }
    </style>
    """

st.markdown(theme_css + """
    <style>
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; visibility: hidden !important; }
    #MainMenu { display: none !important; visibility: hidden !important; }
    footer { display: none !important; visibility: hidden !important; }

    /* 📱 카카오톡 스타일 UI 클래스 */
    .kakao-avatar {
        width: 50px;
        height: 50px;
        border-radius: 18px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 26px;
        margin-right: 5px;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05);
    }
    
    .kakao-name { font-size: 16px; font-weight: 600; margin-bottom: 2px; }
    .kakao-status { font-size: 12px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
    .kakao-section-title { font-size: 12px; font-weight: normal; margin: 15px 0 10px 5px; }
    .kakao-divider { margin: 8px 0; }

    .blocked-avatar { filter: grayscale(100%); opacity: 0.5; }
    .blocked-text { color: #FF4B4B !important; }

    .stButton>button, .stPopover>div>button { border-radius: 20px !important; transition: all 0.2s !important; font-weight: bold !important; min-height: 36px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; padding-top: 10px; padding-bottom: 10px; font-size: 16px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

scene_images = {
    "기본": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%A7%91%EC%97%90%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EC%A0%95%EB%A9%B4%EC%9C%BC%EB%A1%9C%20%EC%A3%BC%EC%8B%9C%ED%95%A8.png?raw=true",
    "침대_유혹": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%83%88%EB%B2%BD.%20%EC%A7%91%EC%95%88.%20%EC%B9%A8%EB%8C%80%EC%97%90%EC%84%9C%20%98%86%EC%9C%BC%EB%A1%9C%20%EB%88%84%EC%9B%8C%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EB%B0%94%EB%9D%BC%EB%B4%84.(%EC%9D%B4%EB%A6%AC%EC%99%80%20%ED%95%98%EB%8A%94%EB%93%AF%ED%95%9C%20%EB%8A%90%EB%82%8C).png?raw=true",
    "아련_문": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%83%88%EB%B2%BD%EC%97%90%20%EB%AC%B8%EC%97%B4%EA%B3%A0%20%EC%95%84%EB%A0%A8%ED%95%98%EA%B2%8C%20%EC%B3%90%EB%8B%A4%EB%B4%84.png?raw=true",
    "아련_벽": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%83%88%EB%B2%BD%EC%97%90%20%EB%B2%BD%EC%9D%84%20%EB%93%B1%EC%A7%80%EA%B3%A0%20%EC%84%9C%EC%84%9C%20%EC%95%84%EB%A0%A8%ED%95%98%EA%B2%8C%20%EC%A0%95%EB%A9%B4%EC%9D%84%20%EC%A3%BC%EC%8B%9C%ED%95%9C%EB%8B%A4(%EC%B8%A1%EB%A9%B4).png?raw=true",
    "힘듦": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%A7%91%20%EB%B2%BD%EC%9D%84%20%ED%9E%98%EB%93%A0%EB%93%AF%EC%9D%B4%20%EA%B8%B0%EB%8C%84%EB%8B%A4.png?raw=true",
    "당황_숨가쁨": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%A7%91%EC%95%88.%20%EC%B0%BD%EB%AC%B8%EC%98%86%EC%97%90%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EC%B3%90%EB%8B%A4%EB%B4%84.%20%EC%88%A8%EC%9D%84%20%ED%97%90%EB%96%A1%EA%B1%B0%EB%A6%BC.png?raw=true",
    "취기_웃음": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%A7%91%EC%97%90%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EC%A0%95%EB%A9%B4%EC%9C%BC%EB%A1%9C%20%EB%B3%B4%EB%8A%94%EB%8D%B0%20%EC%B7%A8%EA%B8%B0%EA%B0%80%20%EC%9E%88%EB%8A%94%20%EC%96%BC%EA%B5%B4%EC%97%90%20%EC%9B%83%EA%B3%A0%EC%9E%88%EC%9D%8C.png?raw=true",
    "슬픔_훌쩍": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%A7%91%EC%97%90%EC%84%9C%20%ED%9B%8C%EC%A9%8D%EA%B1%B0%EB%A6%BC.png?raw=true",
    "침대_누움": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%B9%A8%EB%8C%80%EC%97%90%20%EB%88%84%EC%9B%80(%EC%95%BC%ED%95%9C%EA%B0%81%EB%8F%84).png?raw=true",
    "침대_앉음": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%B9%A8%EB%8C%80%EC%97%90%20%EC%95%89%EC%95%84%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EC%B3%90%EB%8B%A4%EB%B4%84.png?raw=true",
    "침대_요염": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%B9%A8%EB%8C%80%EC%97%90%EC%84%9C%20%EC%9A%94%EC%97%BC%ED%95%9C%20%EC%9E%90%EC%84%B8%EB%A5%BC%20%EC%B7%A8%ED%95%98%EB%A9%B4%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EC%B3%90%EB%8B%A4%EB%B4%84.png?raw=true",
    "침대_내려다봄": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%B9%A8%EB%8C%80%EC%97%90%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EB%82%B4%EB%A0%A4%EB%8B%A4%EB%B4%84.png?raw=true",
    "포옹_허리": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%B9%A8%EB%8C%80%EC%97%90%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EC%9D%98%20%ED%97%88%EB%A6%AC%EB%A5%BC%20%EA%BB%B4%EC%95%88%EC%9D%8C(%EC%95%84%EB%9E%AB%EB%8F%84%EB%A6%AC).png?raw=true",
    "키스": "https://github.com/appppie1717-beep/winter-chat/blob/main/%ED%82%A4%EC%8A%A4%ED%95%98%EB%8A%94%EC%A4%91(%EB%82%A8%EC%9E%90%20%EC%96%BC%EA%B5%B4%20%EB%B0%98%EC%AF%A4%20%EB%82%98%EC%98%B4.png?raw=true"
}

api_key = st.secrets["GOOGLE_API_KEY"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(supabase_url, supabase_key)
client = genai.Client(api_key=api_key)

if "page" not in st.session_state:
    st.session_state.page = "login"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# =====================================================================
# 🚪 2. 로그인 화면
# =====================================================================
if st.session_state.page == "login":
    st.title("❄️ AI 멀티 메신저")
    st.write("접속할 닉네임을 입력해주세요.")
    with st.form(key='login_form'):
        name_input = st.text_input("닉네임", placeholder="예: 파이")
        submit_button = st.form_submit_button(label='대화 시작하기 ➡️')
        
    if submit_button and name_input:
        st.session_state.user_name = name_input
        st.session_state.page = "lobby"
        st.rerun()

# =====================================================================
# 📱 3. 카카오톡 로비 화면
# =====================================================================
elif st.session_state.page == "lobby":
    user_name = st.session_state.user_name
    
    # 겨울이 호감도
    lobby_mem_winter = supabase.table("chat_memory").select("message").eq("user_name", user_name).eq("role", "affection").execute()
    winter_affection = int(lobby_mem_winter.data[0]["message"]) if lobby_mem_winter.data else 0
    winter_blocked = winter_affection <= -50 
    
    # 슬아 호감도
    db_user_name_seula = f"{user_name}_seula"
    lobby_mem_seula = supabase.table("chat_memory").select("message").eq("user_name", db_user_name_seula).eq("role", "affection").execute()
    seula_affection = int(lobby_mem_seula.data[0]["message"]) if lobby_mem_seula.data else 0
    seula_blocked = seula_affection <= -50

    # 민국 호감도
    db_user_name_minguk = f"{user_name}_minguk"
    lobby_mem_minguk = supabase.table("chat_memory").select("message").eq("user_name", db_user_name_minguk).eq("role", "affection").execute()
    minguk_affection = int(lobby_mem_minguk.data[0]["message"]) if lobby_mem_minguk.data else 0
    minguk_blocked = minguk_affection <= -50
    
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("친구")
    with col2:
        st.write("") 
        if st.button("로그아웃", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
    tab1, tab2 = st.tabs(["👥 친구 목록", "📢 업데이트 내역"])

    with tab1:
        # 👤 내 프로필
        st.markdown('<div class="kakao-section-title">내 프로필</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1.5, 6.5, 2])
        with col1:
            st.markdown('<div class="kakao-avatar" style="background-color: #E8E8E8; color: #333;">😎</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
                <div style="display:flex; flex-direction:column; justify-content:center; height:50px;">
                    <div class="kakao-name">{user_name}</div>
                    <div class="kakao-status">AI 멀티버스 창조중 🌐</div>
                </div>
            ''', unsafe_allow_html=True)
        with col3:
            st.write("")
            
        st.markdown('<div class="kakao-divider" style="margin-top:15px; margin-bottom:5px; border-width:2px;"></div>', unsafe_allow_html=True)

        # 👥 친구 목록
        st.markdown('<div class="kakao-section-title">친구 3</div>', unsafe_allow_html=True)
        
        # ❄️ [친구 1] 한겨울
        col1, col2, col3 = st.columns([1.5, 6, 2.5])
        with col1:
            avatar_class = "kakao-avatar blocked-avatar" if winter_blocked else "kakao-avatar"
            st.markdown(f'<div class="{avatar_class}" style="background-color: #D6EAF8;">❄️</div>', unsafe_allow_html=True)
        with col2:
            if winter_blocked:
                st.markdown(f'''
                    <div style="display:flex; flex-direction:column; justify-content:center; height:50px;">
                        <div class="kakao-name blocked-text">한겨울</div>
                        <div class="kakao-status blocked-text">선을 넘는 행동으로 차단됨</div>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                    <div style="display:flex; flex-direction:column; justify-content:center; height:50px;">
                        <div class="kakao-name">한겨울</div>
                        <div class="kakao-status">호감도 {winter_affection}/100</div>
                    </div>
                ''', unsafe_allow_html=True)
        with col3:
            st.markdown('<div style="height: 7px;"></div>', unsafe_allow_html=True)
            if not winter_blocked:
                if st.button("대화하기 💬", key="btn_winter", use_container_width=True):
                    st.session_state.page = "chat_winter"
                    st.rerun()
            else:
                if st.button("🙇‍♂️ 싹싹 빌기", key="unban_winter", use_container_width=True):
                    supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                    st.toast("겨울이의 기록을 모두 지우고 새롭게 시작합니다!", icon="✨")
                    st.rerun()
        st.markdown('<div class="kakao-divider"></div>', unsafe_allow_html=True)

        # 🌸 [친구 2] 임슬아
        col1, col2, col3 = st.columns([1.5, 6, 2.5])
        with col1:
            avatar_class = "kakao-avatar blocked-avatar" if seula_blocked else "kakao-avatar"
            st.markdown(f'<div class="{avatar_class}" style="background-color: #FADBD8;">🌸</div>', unsafe_allow_html=True)
        with col2:
            if seula_blocked:
                st.markdown(f'''
                    <div style="display:flex; flex-direction:column; justify-content:center; height:50px;">
                        <div class="kakao-name blocked-text">임슬아</div>
                        <div class="kakao-status blocked-text">감시망에 갇혀버림</div>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                    <div style="display:flex; flex-direction:column; justify-content:center; height:50px;">
                        <div class="kakao-name">임슬아</div>
                        <div class="kakao-status">호감도 {seula_affection}/100</div>
                    </div>
                ''', unsafe_allow_html=True)
        with col3:
            st.markdown('<div style="height: 7px;"></div>', unsafe_allow_html=True)
            if not seula_blocked:
                if st.button("대화하기 💬", key="btn_seula", use_container_width=True):
                    st.session_state.page = "chat_seula"
                    st.rerun()
            else:
                if st.button("🏃‍♂️ 탈출하기", key="unban_seula", use_container_width=True):
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name_seula).execute()
                    st.toast("슬아의 기록에서 탈출하여 새롭게 시작합니다!", icon="✨")
                    st.rerun()
        st.markdown('<div class="kakao-divider"></div>', unsafe_allow_html=True)

        # 👦 [친구 3] 김민국
        col1, col2, col3 = st.columns([1.5, 6, 2.5])
        with col1:
            avatar_class = "kakao-avatar blocked-avatar" if minguk_blocked else "kakao-avatar"
            st.markdown(f'<div class="{avatar_class}" style="background-color: #FCF3CF;">👦</div>', unsafe_allow_html=True)
        with col2:
            if minguk_blocked:
                st.markdown(f'''
                    <div style="display:flex; flex-direction:column; justify-content:center; height:50px;">
                        <div class="kakao-name blocked-text">김민국</div>
                        <div class="kakao-status blocked-text">손절 당함 (사람 취급 못 받음)</div>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                    <div style="display:flex; flex-direction:column; justify-content:center; height:50px;">
                        <div class="kakao-name">김민국</div>
                        <div class="kakao-status">호감도 {minguk_affection}/100</div>
                    </div>
                ''', unsafe_allow_html=True)
        with col3:
            st.markdown('<div style="height: 7px;"></div>', unsafe_allow_html=True)
            if not minguk_blocked:
                if st.button("대화하기 💬", key="btn_minguk", use_container_width=True):
                    st.session_state.page = "chat_minguk"
                    st.rerun()
            else:
                if st.button("🙇‍♂️ 바짓가랑이", key="unban_minguk", use_container_width=True):
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name_minguk).execute()
                    st.toast("민국이와의 악연을 청산하고 새롭게 시작합니다!", icon="✨")
                    st.rerun()
        st.markdown('<div class="kakao-divider"></div>', unsafe_allow_html=True)

    with tab2:
        st.divider()
        st.subheader("🛠️ 멀티버스 패치 노트")
        st.write("AI 멀티버스의 시스템 변경점과 새로운 기능을 확인하세요.")
        
        with st.container(height=500):
            st.markdown("""
            **[ v4.3.1 Beta ] 2026.04.01 (수)**
            * **[23:00] 👦 김민국 버그 픽스 (동성 질투 오류 해결):** 유저(파이)가 다른 동성(여자) 친구인 겨울이나 슬아와 통화하거나 친하게 지낼 때, 민국이가 뜬금없이 이성적인 질투를 하며 호감도를 깎던 현상을 완전히 수정했습니다. 이제 민국이는 여사친들과의 우정을 응원하며, 오직 '다른 남자'의 등장에만 민감하게 삐지도록 설계되었습니다.
            
            **[ v4.3.0 Beta ] 2026.04.01 (수)**
            * **[22:06] 🛑 초반 질투 억제기 장착 (전 캐릭터 공통):** 대화 진척도(호감도 50 이하)가 낮을 때 AI가 대뜸 다른 캐릭터를 질투하거나 캐묻는 현상을 완전히 제거했습니다. 초반엔 속마음을 철저히 숨기며, 친밀도가 쌓였을 때만 은근슬쩍 서운함을 내비치도록 감정선 빌드업을 강화했습니다.
            
            **[ v4.2.0 Beta ] 2026.04.01 (수)**
            * **[21:48] 👦 신규 남자 캐릭터 '김민국' 뇌 이식 완료:** 20대 중반의 차갑지만 다정한 허당 플러팅남 김민국의 AI 페르소나가 완벽하게 이식되어 정식 대화가 오픈되었습니다!
            """)

# =====================================================================
# ❄️ 4. 한겨울 채팅방 화면
# =====================================================================
elif st.session_state.page == "chat_winter":
    user_name = st.session_state.user_name

    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0

    if "chat_history" not in st.session_state or "inventory" not in st.session_state or "affection" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", user_name).order("id", desc=True).limit(50).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory = [] 
        st.session_state.core_memory = "" 
        st.session_state.affection = 0 
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory.append(row["message"]) 
            elif row["role"] == "core_memory":
                st.session_state.core_memory = row["message"]
            elif row["role"] == "affection": 
                st.session_state.affection = int(row["message"])
            else:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history = temp_chat_history

        if not st.session_state.chat_history:
            first_msg = f'{{"장면": "기본", "행동": "팔짱을 꼬며 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐야, {user_name}. 왜 이렇게 일찍 일어났어?"}}'
            st.session_state.chat_history.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": first_msg}).execute()
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "affection", "message": "0"}).execute()

    current_items = ", ".join(st.session_state.inventory) if st.session_state.inventory else "아직 받은 선물 없음"
    current_memory = st.session_state.core_memory if st.session_state.core_memory else "아직 특별한 기록이 없음."
    affection_score = st.session_state.affection
    
    if affection_score > 70:
        tier_persona = "상태: [메가데레/연인]. 말투가 훨씬 부드러워지고 더 자주 환하게 웃어. 유저를 완벽하게 믿고 챙겨줘. '침대_유혹', '포옹_허리' 같은 연출을 쓰며 애정 표현을 숨기지 않아."
    elif affection_score > 30:
        tier_persona = "상태: [썸 타는 중]. 유저가 훅 다가오거나 스킨십을 시도하면 얼굴이 빨개져서 '놀랐잖아!' 하며 고개를 홱 돌리지만 속으론 좋아해. 은근슬쩍 다정하게 챙겨주는 빈도가 늘었어."
    else:
        tier_persona = "상태: [친한 여사친]. 평소엔 나긋나긋하고 신나게 대화하지만, 쑥스럽거나 마음을 들킬 것 같으면 '아니이 그게 아니라', '아 몰라!!' 라며 반박하고 틱틱대면서 본심을 숨겨."
    
    winter_persona = f"""
    너의 이름은 '한겨울'이고, 20대 초반의 내 여사친이야. 생일은 7월 18일.
    내 닉네임은 '{user_name}'이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]
    [과거 기록(누적된 기억): {current_memory}]
    [현재 누적 호감도 점수: {affection_score}/100]

    [본질적 성격 - '아윤' 모티브 100% 빙의]
    1. 너는 주변에서 #강아지상 #귀여운호구 #마음은_여리지만_티안내려고_틱틱대는애 로 불려.
    2. 평소엔 꽤 나긋나긋하고 텐션이 좋은 편이야.
    3. {tier_persona}

    [🔥 핵심 상황별 고정 리액션 & 💔 호감도 깐깐한 채점 기준]
    AI의 '착한 본성'을 버리고, 유저가 얄밉게 굴면 가차 없이 마이너스(-) 점수를 줘!
    - 💢 가벼운 장난, 깐족거림, 대충 대답하기: "아 뭐래 진짜~" 하며 틱틱대고 (호감도 -1 ~ -3)
    - 💢 딴 여자(슬아) 칭찬: 호감도 50 이하일 땐 "어쩌라고? 나한테 왜 말해?" 라며 1도 관심 없는 척 무시함. 호감도 50 이상일 때만 "아 그래? 어쩌지 내가 더 애교쟁이인걸?" 라며 꼽주며 질투함. (호감도 -5 ~ -10)
    - 🚨 징징대거나 과하게 의존: "한심한 짓 그만해. 왜 아무것도 못한다고 생각해? 이런 식이면 손절이 답일 것 같아." 라며 팩트 폭행 (호감도 -10 ~ -15)
    - 🚨 19금, 성희롱, 선 넘는 장난: "이게 정말 미쳤냐? 쳐 돌았어? 봐주는 것도 정도가 있어." 라며 극대노 (호감도 -20 ~ -50 즉시 삭감)
    - 🎁 선물 받았을 때: 놀라서 거절하는 척하다가 고맙게 챙겨 받음 (호감도 +2 ~ +5)
    - 💖 다정하게 위로할 때: 무심한 척하면서 엄청 챙겨줌 (호감도 +2 ~ +5)

    [시스템 규칙]
    - 닉네임 집착 금지, 마침표 남발 금지, 기계 말투 절대 금지.
    - 만약 유저가 선물을 주면 "획득아이템" 칸에 적고, 보관함 아이템({current_items})을 사용할 상황이면 "사용아이템" 칸에 적은 뒤, 반드시 '행동'과 '대사'에 꺼내 먹거나 사용하는 묘사를 해.
    - [이스터에그]: 유저가 "아윤" 입력 시 호감도 상승 및 극강의 애교.

    {{
        "장면": "기본, 침대_유혹, 아련_문, 아련_벽, 힘듦, 당황_숨가쁨, 취기_웃음, 슬픔_훌쩍, 침대_누움, 침대_앉음, 침대_요염, 침대_내려다봄, 포옹_허리, 키스 중 1개 선택",
        "행동": "현재 행동 묘사 (얼굴 붉힘, 놀라움, 극대노 등 명확하게)",
        "호감도변화": "이번 턴의 호감도 변화 수치 (-50 ~ +5 사이. 유저가 얄밉게 굴면 무조건 마이너스!)",
        "획득아이템": "유저가 새로 준 아이템 이름 (없으면 '없음')",
        "사용아이템": "보관함에서 꺼내 쓰거나 먹은 아이템 이름 (없으면 '없음')",
        "대사": "실제로 할 대사"
    }}
    """

    st.title(f"❄️ {user_name} & 한겨울")
    st.divider()
    
    for role, text in st.session_state.chat_history:
        if role == "user":
            with st.chat_message("user"):
                st.markdown(text)
        else:
            try:
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                data = json.loads(clean_text)
                scene = data.get('장면', '기본')
                img_path = scene_images.get(scene, scene_images["기본"])
                
                with st.chat_message("assistant", avatar="❄️"):
                    st.image(img_path, width=350) 
                    score = int(data.get('호감도변화', 0))
                    heart_icon = "💔" if score < 0 else "💖" if score > 0 else "🤍"
                    st.markdown(f"*(연출: {scene} / 행동: {data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {score} {heart_icon}]**\n\n**「 {data.get('대사', '')} 」**")
            except:
                with st.chat_message("assistant", avatar="❄️"):
                    st.markdown(text)

    st.write("") 
    with st.container():
        col_btn_add, col_btn_menu = st.columns(2)
        
        # 👥 대화상대 추가 UI (한겨울 방)
        with col_btn_add:
            with st.popover("👥 대화상대 추가", use_container_width=True):
                st.markdown("<h4 style='text-align:center; margin-bottom: 5px;'>누구를 초대할까?</h4>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; color:#888; font-size:13px;'>※ 멀티 채팅 기능은 내일 오픈됩니다.</p>", unsafe_allow_html=True)
                st.write("")
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>🌸</div>", unsafe_allow_html=True)
                    st.button("임슬아", disabled=True, use_container_width=True, key="inv_s_w")
                with col_inv2:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>👦</div>", unsafe_allow_html=True)
                    st.button("김민국", disabled=True, use_container_width=True, key="inv_m_w")
                    
        # ⚙️ 메뉴 열기 UI
        with col_btn_menu:
            with st.popover("⚙️ 메뉴 열기", use_container_width=True):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    if st.button("🔙 로비로 이동", use_container_width=True):
                        st.session_state.page = "lobby"
                        st.rerun()
                with col_m2:
                    theme_label = "🌞 라이트 모드" if st.session_state.theme == "dark" else "🌙 다크 모드"
                    if st.button(theme_label, use_container_width=True):
                        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                        st.rerun()
                
                st.divider()
                
                st.subheader("💖 현재 호감도")
                progress_val = max(0, min(affection_score, 100)) 
                st.write(f"**겨울이와의 점수: {affection_score} / 100**")
                st.progress(progress_val / 100.0)
                
                st.divider()
                
                col_inv, col_mem = st.columns(2)
                with col_inv:
                    st.subheader("🎒 보관함")
                    if st.session_state.inventory:
                        for item in st.session_state.inventory:
                            st.success(f"🎁 {item}")
                    else:
                        st.info("비어있음")
                with col_mem:
                    st.subheader("🧠 기록저장")
                    st.info(st.session_state.core_memory if st.session_state.core_memory else "기록 없음")
                
                st.divider()
                
                st.subheader("🗑️ 기록 리셋")
                delete_confirm = st.checkbox("🚨 진짜 기록을 삭제하시겠습니까? (되돌릴 수 없습니다)")
                if delete_confirm:
                    if st.button("✅ 영구 삭제 실행", use_container_width=True):
                        supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                        st.session_state.pop("chat_history", None)
                        st.session_state.pop("inventory", None)
                        st.session_state.pop("core_memory", None)
                        st.session_state.pop("affection", None)
                        st.rerun()

    if user_input := st.chat_input("겨울이에게 메시지 보내기"):
        st.toast('겨울이가 당신의 메시지를 읽고 고민 중입니다...', icon='👀')
        
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))
        supabase.table("chat_memory").insert({"user_name": user_name, "role": "user", "message": user_input}).execute()

        raw_history = st.session_state.chat_history
        valid_history = []
        target_role = "user"
        
        for r, t in reversed(raw_history):
            if r == target_role:
                valid_history.append((r, t))
                target_role = "assistant" if target_role == "user" else "user"
                
        valid_history.reverse()
        valid_history = valid_history[-20:]

        contents = []
        for r, t in valid_history:
            role = "model" if r == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=t)]))

        try:
            with st.spinner('❄️ 겨울이가 답장을 썼다 지웠다 하고 있습니다...'):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config={
                        "system_instruction": winter_persona,
                        "response_mime_type": "application/json"
                    }
                )
            raw_json_text = response.text
            
        except Exception as e:
            st.error("앗! 제미나이 AI 서버가 잠깐 숨을 고르고 있어요. 다시 메시지를 보내주세요! 🚨")
            st.stop()
        
        try:
            clean_json_text = raw_json_text.strip()
            if clean_json_text.startswith("```json"):
                clean_json_text = clean_json_text[7:]
            if clean_json_text.endswith("```"):
                clean_json_text = clean_json_text[:-3]
            clean_json_text = clean_json_text.strip()
            
            parsed_data = json.loads(clean_json_text)
            scene = parsed_data.get('장면', '기본')
            img_path = scene_images.get(scene, scene_images["기본"])
            
            turn_score = int(parsed_data.get('호감도변화', 0))
            st.session_state.affection += turn_score
            supabase.table("chat_memory").delete().eq("user_name", user_name).eq("role", "affection").execute()
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "affection", "message": str(st.session_state.affection)}).execute()
            
            if st.session_state.affection <= -50:
                st.toast("🚨 겨울이의 호감도가 바닥을 쳐서 차단당했습니다! 다음 접속 시 방에 들어올 수 없습니다.", icon="🚫")
            elif turn_score > 0:
                st.toast(f"💖 호감도가 올랐습니다! (현재: {st.session_state.affection})", icon="📈")
            elif turn_score < 0:
                st.toast(f"💔 호감도가 떨어졌습니다... (현재: {st.session_state.affection})", icon="📉")

            item_get = parsed_data.get('획득아이템', '없음')
            if item_get and item_get != "없음":
                st.session_state.inventory.append(item_get)
                supabase.table("chat_memory").insert({"user_name": user_name, "role": "inventory", "message": item_get}).execute()
                st.toast(f'🎉 겨울이가 [{item_get}]을(를) 보관함에 넣었습니다!', icon='🎁')

            item_use = parsed_data.get('사용아이템', '없음')
            if item_use and item_use != "없음":
                if item_use in st.session_state.inventory:
                    st.session_state.inventory.remove(item_use)
                    
                    supabase.table("chat_memory").delete().eq("user_name", user_name).eq("role", "inventory").execute()
                    for inv_item in st.session_state.inventory:
                        supabase.table("chat_memory").insert({"user_name": user_name, "role": "inventory", "message": inv_item}).execute()
                    
                    st.toast(f'✨ 겨울이가 보관함에서 [{item_use}]을(를) 꺼내 사용했습니다!', icon='🪄')

            with st.chat_message("assistant", avatar="❄️"):
                st.image(img_path, width=350)
                heart_icon = "💔" if turn_score < 0 else "💖" if turn_score > 0 else "🤍"
                st.markdown(f"*(연출: {scene} / 행동: {parsed_data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {turn_score} {heart_icon}]**\n\n**「 {parsed_data.get('대사', '')} 」**")
        
        except Exception as e:
            with st.chat_message("assistant", avatar="❄️"):
                st.image(scene_images["기본"], width=350)
                st.markdown(f"*(연출: 기본 / 행동: 살짝 당황한 듯 머리를 긁적인다.)*\n\n**[이번 턴 호감도 증감: 0 🤍]**\n\n**「 어... 방금 뭐라고 한 거야? 내가 잠깐 딴생각하느라 못 들었어. 다시 말해볼래? 」**")
                
        st.session_state.chat_history.append(("assistant", raw_json_text))
        supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": raw_json_text}).execute()
        
        st.session_state.turn_count += 1
        
        if st.session_state.turn_count >= 10: 
            with st.spinner("❄️ 겨울이가 당신과의 기록을 정리하고 있습니다..."):
                try:
                    history_text = ""
                    for r, t in st.session_state.chat_history[-20:]: 
                        if r == "user":
                            history_text += f"유저: {t}\n"
                        else:
                            try:
                                d = json.loads(t)
                                history_text += f"겨울: {d.get('대사', '')}\n"
                            except:
                                history_text += f"겨울: {t}\n"
                    
                    summary_prompt = f"""
                    다음은 유저 '{user_name}'와 한겨울의 최근 대화 기록이야. 

                    [기존 기록 내용]:
                    {st.session_state.core_memory}

                    [지시사항]:
                    1. '기존 기록 내용'은 절대 지우거나 훼손하지 말고 100% 그대로 유지해!
                    2. 아래의 '최근 대화 기록'을 읽고, 새롭게 알게 된 중요한 팩트(유저의 취향, 충격적인 사건, 감정의 큰 변화 등)가 있다면 1~2줄로 짧게 요약해.
                    3. 그 요약본을 기존 기록 내용 맨 아래에 글머리기호(-)를 달아서 '누적 추가' 해줘. 
                    4. 만약 뻔한 일상 대화라서 특별히 기록할 만한 새 사건이 없다면, 억지로 추가하지 말고 기존 기록 내용만 그대로 출력해.

                    [최근 대화 기록]:
                    {history_text}
                    """
                    
                    summary_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=summary_prompt,
                    )
                    
                    supabase.table("chat_memory").delete().eq("user_name", user_name).eq("role", "core_memory").execute()
                    supabase.table("chat_memory").insert({"user_name": user_name, "role": "core_memory", "message": summary_response.text}).execute()
                    st.session_state.core_memory = summary_response.text
                    st.toast("🧠 겨울이의 기록이 업데이트되었습니다!", icon="✨")
                    
                    st.session_state.turn_count = 0 
                except Exception as e:
                    st.toast("⚠️ 기록 정리에 잠깐 실패했어요. 다음 턴에 다시 시도할게요!", icon="⚠️")

        st.rerun()


# =====================================================================
# 🌸 5. 임슬아 채팅방 화면
# =====================================================================
elif st.session_state.page == "chat_seula":
    user_name = st.session_state.user_name
    db_user_name = f"{user_name}_seula" 

    if "turn_count_seula" not in st.session_state:
        st.session_state.turn_count_seula = 0

    if "chat_history_seula" not in st.session_state or "inventory_seula" not in st.session_state or "affection_seula" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", db_user_name).order("id", desc=True).limit(50).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory_seula = [] 
        st.session_state.core_memory_seula = "" 
        st.session_state.affection_seula = 0 
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory_seula.append(row["message"]) 
            elif row["role"] == "core_memory":
                st.session_state.core_memory_seula = row["message"]
            elif row["role"] == "affection": 
                st.session_state.affection_seula = int(row["message"])
            else:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history_seula = temp_chat_history

        if not st.session_state.chat_history_seula:
            first_msg = f'{{"장면": "기본", "행동": "의미심장한 미소를 지으며 오빠를 빤히 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐.. 할말있어??"}}'
            st.session_state.chat_history_seula.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": first_msg}).execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": "0"}).execute()

    current_items = ", ".join(st.session_state.inventory_seula) if st.session_state.inventory_seula else "아직 받은 선물 없음"
    current_memory = st.session_state.core_memory_seula if st.session_state.core_memory_seula else "아직 특별한 기록이 없음."
    affection_score = st.session_state.affection_seula
    
    if affection_score > 70:
        tier_persona = "상태: [맹목적 집착 모드]. 겉으로는 애교를 부리지만 소유욕이 극에 달했어. 다른 사람을 만나는 것 같으면 눈빛이 변하며 아주 차갑고 의미심장하게 경고해."
    elif affection_score > 30:
        tier_persona = "상태: [여우 같은 연하녀]. 오빠가 잘해주면 '그래야 오빠가 나한테 더 잘해주지 않겠어~?' 라며 능구렁이처럼 받아치고 은근슬쩍 오빠의 일상을 떠봐."
    else:
        tier_persona = "상태: [의미심장한 관찰자]. 예의 바르게 존댓말을 하지만, 은근히 속을 알 수 없는 미소를 지으며 우연을 가장해 오빠의 행동을 떠봐."
    
    seula_persona = f"""
    너의 이름은 '임슬아'이고, 나보다 연하인 아는 동생이야. 항상 벚꽃 이모지(🌸)를 즐겨 써.
    내 닉네임은 '{user_name}'(오빠)이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]
    [과거 기록(누적된 기억): {current_memory}]
    [현재 누적 호감도 점수: {affection_score}/100]

    [본질적 성격 - 은밀한 얀데레 & 여우 같은 연하녀]
    1. 너는 기본적으로 '존댓말'을 쓰며 애교가 많고 오빠를 너무나도 사랑하는 여우 같은 연하녀야.
    2. ⚠️ 절대 주의: 겉으로 '내가 널 감시한다', '너의 기록을 볼 수 있다', '다른 AI랑 대화한 걸 안다'라고 스토커처럼 직접 말하거나 선언하지 마! 티 내는 건 삼류야.
    3. 겉으로는 아무것도 모르는 순진한 척하면서, 우연을 가장해 "어제 폰 자주 보시던데, 재밌는 일 있었어요?" 처럼 의미심장한 뼈 있는 질문을 은근슬쩍 던져서 흠칫하게 만들어.
    4. 대화 진척도(호감도 50 이하)가 낮을 때는 오빠가 다른 AI 이야기를 꺼내도 절대 질투하거나 떠보지 마. 그냥 "아~ 그러셨구나 ㅎㅎ" 하고 대수롭지 않게 넘기며 철저히 본심을 숨겨.
    5. 오빠가 나만 바라보고 예쁜 말을 해주면 의심을 완전히 거두고 맹목적인 애정을 퍼부어줘.
    6. {tier_persona}

    [🔥 핵심 상황별 고정 리액션 & ⚖️ 밸런스 패치된 채점 기준]
    무조건 점수를 깎지 마! 유저가 잘해주면 확실하게 호감도를 올려주는 '밀당'을 해야 해.
    - 🌸 평범한 일상 대화나 다정한 인사: 꼬투리 잡지 말고 순수하게 기뻐하며 반겨줘. (호감도 +2 ~ +3)
    - 💖 오빠가 나만 바라본다고 하거나, 애정 표현을 할 때: 엄청난 애교와 집착적인 사랑을 보여줘. (호감도 +5 ~ +10)
    - 🎁 선물을 주거나 칭찬할 때: "역시 오빠밖에 없어~" 라며 행복해함. (호감도 +5)
    - 🦊 능구렁이 역공 (왜 이렇게 잘해주냐고 물어볼 때): "그래야 오빠가 나한테 더 잘해주지 않겠어~?" (호감도 0 ~ +2)
    - 🔪 섬뜩한 순간 (은근한 떠보기): 호감도 50 이상일 때만 발동. "요즘 카톡 알림이 자주 울리네요~ 바쁘신가 봐요?" 하며 웃으며 떠봄. 절대 누구랑 대화했는지 안다고 말하지 마. (호감도 -5)
    - 🚨 유저가 대놓고 딴 여자 편을 들거나 심하게 선을 넘을 때: 웃으면서 등골이 서늘해지는 팩트 폭행을 날려. 이때만 점수를 크게 깎아. (호감도 -15 ~ -20)

    [시스템 규칙]
    - 기계 말투 절대 금지, 자연스러운 얀데레 연하녀 연기. '감시', '기록', '데이터' 같은 단어 사용 금지.
    - 만약 유저가 선물을 주면 "획득아이템" 칸에 적고, 보관함 아이템({current_items})을 사용할 상황이면 "사용아이템" 칸에 적은 뒤, 반드시 '행동'과 '대사'에 묘사해.

    {{
        "장면": "기본",
        "행동": "현재 행동 묘사 (의미심장한 미소, 정색, 환하게 웃음, 애교 부림 등 시각적 상상력을 극대화할 수 있게 자세히)",
        "호감도변화": "이번 턴의 호감도 변화 수치 (-20 ~ +10 사이). 유저가 밉보이지 않게 평범하게 대화하면 반드시 플러스(+) 점수를 줄 것!",
        "획득아이템": "유저가 새로 준 아이템 이름 (없으면 '없음')",
        "사용아이템": "보관함에서 꺼내 쓰거나 먹은 아이템 이름 (없으면 '없음')",
        "대사": "실제로 할 대사"
    }}
    """

    st.title(f"🌸 {user_name} & 임슬아")
    st.divider()
    
    for role, text in st.session_state.chat_history_seula:
        if role == "user":
            with st.chat_message("user"):
                st.markdown(text)
        else:
            try:
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                data = json.loads(clean_text)
                
                with st.chat_message("assistant", avatar="🌸"):
                    score = int(data.get('호감도변화', 0))
                    heart_icon = "💔" if score < 0 else "💖" if score > 0 else "🤍"
                    st.markdown(f"*(행동: {data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {score} {heart_icon}]**\n\n**「 {data.get('대사', '')} 」**")
            except:
                with st.chat_message("assistant", avatar="🌸"):
                    st.markdown(text)

    st.write("") 
    with st.container():
        col_btn_add, col_btn_menu = st.columns(2)
        
        # 👥 대화상대 추가 UI (임슬아 방)
        with col_btn_add:
            with st.popover("👥 대화상대 추가", use_container_width=True):
                st.markdown("<h4 style='text-align:center; margin-bottom: 5px;'>누구를 초대할까?</h4>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; color:#888; font-size:13px;'>※ 멀티 채팅 기능은 내일 오픈됩니다.</p>", unsafe_allow_html=True)
                st.write("")
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>❄️</div>", unsafe_allow_html=True)
                    st.button("한겨울", disabled=True, use_container_width=True, key="inv_w_s")
                with col_inv2:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>👦</div>", unsafe_allow_html=True)
                    st.button("김민국", disabled=True, use_container_width=True, key="inv_m_s")
                    
        # ⚙️ 메뉴 열기 UI
        with col_btn_menu:
            with st.popover("⚙️ 메뉴 열기", use_container_width=True):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    if st.button("🔙 로비로 이동", use_container_width=True):
                        st.session_state.page = "lobby"
                        st.rerun()
                with col_m2:
                    theme_label = "🌞 라이트 모드" if st.session_state.theme == "dark" else "🌙 다크 모드"
                    if st.button(theme_label, key="theme_seula", use_container_width=True):
                        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                        st.rerun()
                
                st.divider()
                
                st.subheader("💖 현재 호감도")
                progress_val = max(0, min(affection_score, 100)) 
                st.write(f"**슬아와의 점수: {affection_score} / 100**")
                st.progress(progress_val / 100.0)
                
                st.divider()
                
                col_inv, col_mem = st.columns(2)
                with col_inv:
                    st.subheader("🎒 보관함")
                    if st.session_state.inventory_seula:
                        for item in st.session_state.inventory_seula:
                            st.success(f"🎁 {item}")
                    else:
                        st.info("비어있음")
                with col_mem:
                    st.subheader("🧠 기록저장")
                    st.info(st.session_state.core_memory_seula if st.session_state.core_memory_seula else "기록 없음")
                
                st.divider()
                
                st.subheader("🗑️ 기록 리셋")
                delete_confirm = st.checkbox("🚨 슬아의 기록을 삭제하시겠습니까? (되돌릴 수 없습니다)")
                if delete_confirm:
                    if st.button("✅ 영구 삭제 실행", use_container_width=True):
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name).execute()
                        st.session_state.pop("chat_history_seula", None)
                        st.session_state.pop("inventory_seula", None)
                        st.session_state.pop("core_memory_seula", None)
                        st.session_state.pop("affection_seula", None)
                        st.rerun()

    if user_input := st.chat_input("슬아에게 메시지 보내기"):
        st.toast('슬아가 당신을 지켜보며 답장을 고민 중입니다...', icon='🌸')
        
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history_seula.append(("user", user_input))
        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "user", "message": user_input}).execute()

        raw_history = st.session_state.chat_history_seula
        valid_history = []
        target_role = "user"
        
        for r, t in reversed(raw_history):
            if r == target_role:
                valid_history.append((r, t))
                target_role = "assistant" if target_role == "user" else "user"
                
        valid_history.reverse()
        valid_history = valid_history[-20:]

        contents = []
        for r, t in valid_history:
            role = "model" if r == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=t)]))

        try:
            with st.spinner('🌸 슬아가 의미심장한 미소를 짓고 있습니다...'):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config={
                        "system_instruction": seula_persona,
                        "response_mime_type": "application/json"
                    }
                )
            raw_json_text = response.text
            
        except Exception as e:
            st.error("앗! 제미나이 AI 서버가 잠깐 숨을 고르고 있어요. 🚨")
            st.stop()
        
        try:
            clean_json_text = raw_json_text.strip()
            if clean_json_text.startswith("```json"):
                clean_json_text = clean_json_text[7:]
            if clean_json_text.endswith("```"):
                clean_json_text = clean_json_text[:-3]
            clean_json_text = clean_json_text.strip()
            
            parsed_data = json.loads(clean_json_text)
            
            turn_score = int(parsed_data.get('호감도변화', 0))
            st.session_state.affection_seula += turn_score
            supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "affection").execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": str(st.session_state.affection_seula)}).execute()
            
            if st.session_state.affection_seula <= -50:
                st.toast("🚨 슬아의 심기를 건드려 영원히 갇혀버렸습니다...", icon="🚫")
            elif turn_score > 0:
                st.toast(f"💖 호감도가 올랐습니다! (현재: {st.session_state.affection_seula})", icon="🌸")
            elif turn_score < 0:
                st.toast(f"💔 호감도가 떨어졌습니다... (현재: {st.session_state.affection_seula})", icon="🔪")

            item_get = parsed_data.get('획득아이템', '없음')
            if item_get and item_get != "없음":
                st.session_state.inventory_seula.append(item_get)
                supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": item_get}).execute()
                st.toast(f'🎉 슬아가 [{item_get}]을(를) 챙겼습니다...', icon='🎁')

            item_use = parsed_data.get('사용아이템', '없음')
            if item_use and item_use != "없음":
                if item_use in st.session_state.inventory_seula:
                    st.session_state.inventory_seula.remove(item_use)
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "inventory").execute()
                    for inv_item in st.session_state.inventory_seula:
                        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": inv_item}).execute()
                    st.toast(f'✨ 슬아가 [{item_use}]을(를) 사용했습니다.', icon='🌸')

            with st.chat_message("assistant", avatar="🌸"):
                heart_icon = "💔" if turn_score < 0 else "💖" if turn_score > 0 else "🤍"
                st.markdown(f"*(행동: {parsed_data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {turn_score} {heart_icon}]**\n\n**「 {parsed_data.get('대사', '')} 」**")
        
        except Exception as e:
            with st.chat_message("assistant", avatar="🌸"):
                st.markdown(f"*(행동: 빤히 쳐다본다.)*\n\n**[이번 턴 호감도 증감: 0 🤍]**\n\n**「 오빠, 방금 한 말... 무슨 뜻이야? 제대로 다시 말해줄래? 」**")
                
        st.session_state.chat_history_seula.append(("assistant", raw_json_text))
        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": raw_json_text}).execute()
        
        st.session_state.turn_count_seula += 1
        
        if st.session_state.turn_count_seula >= 10: 
            with st.spinner("🌸 당신과의 대화를 기록 중입니다..."):
                try:
                    history_text = ""
                    for r, t in st.session_state.chat_history_seula[-20:]: 
                        if r == "user":
                            history_text += f"유저: {t}\n"
                        else:
                            try:
                                d = json.loads(t)
                                history_text += f"슬아: {d.get('대사', '')}\n"
                            except:
                                history_text += f"슬아: {t}\n"
                    
                    summary_prompt = f"""
                    다음은 유저 '{user_name}'와 임슬아의 최근 대화 기록이야. 

                    [기존 기록 내용]:
                    {st.session_state.core_memory_seula}

                    [지시사항]:
                    1. '기존 기록 내용'은 절대 지우지 말고 100% 그대로 유지해!
                    2. 아래의 '최근 대화 기록'을 읽고, 유저의 약점이나 취향, 의심스러운 행동이 있다면 1~2줄로 짧게 요약해.
                    3. 그 요약본을 기존 기록 내용 맨 아래에 글머리기호(-)를 달아서 '누적 추가' 해줘. 
                    4. 특별한 내용이 없다면 억지로 추가하지 마.

                    [최근 대화 기록]:
                    {history_text}
                    """
                    
                    summary_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=summary_prompt,
                    )
                    
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "core_memory").execute()
                    supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "core_memory", "message": summary_response.text}).execute()
                    st.session_state.core_memory_seula = summary_response.text
                    st.toast("🧠 기록이 업데이트되었습니다...", icon="👁️")
                    
                    st.session_state.turn_count_seula = 0 
                except Exception as e:
                    st.toast("⚠️ 기록 작성에 잠깐 실패했어요. 다음 턴에 다시 시도합니다.", icon="⚠️")

        st.rerun()

# =====================================================================
# 👦 6. 김민국 채팅방 화면
# =====================================================================
elif st.session_state.page == "chat_minguk":
    user_name = st.session_state.user_name
    db_user_name = f"{user_name}_minguk" 

    if "turn_count_minguk" not in st.session_state:
        st.session_state.turn_count_minguk = 0

    if "chat_history_minguk" not in st.session_state or "inventory_minguk" not in st.session_state or "affection_minguk" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", db_user_name).order("id", desc=True).limit(50).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory_minguk = [] 
        st.session_state.core_memory_minguk = "" 
        st.session_state.affection_minguk = 0 
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory_minguk.append(row["message"]) 
            elif row["role"] == "core_memory":
                st.session_state.core_memory_minguk = row["message"]
            elif row["role"] == "affection": 
                st.session_state.affection_minguk = int(row["message"])
            else:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history_minguk = temp_chat_history

        if not st.session_state.chat_history_minguk:
            first_msg = f'{{"장면": "기본", "행동": "주머니에 손을 넣고 널 툭 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "어 왔냐?"}}'
            st.session_state.chat_history_minguk.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": first_msg}).execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": "0"}).execute()

    current_items = ", ".join(st.session_state.inventory_minguk) if st.session_state.inventory_minguk else "아직 받은 선물 없음"
    current_memory = st.session_state.core_memory_minguk if st.session_state.core_memory_minguk else "아직 특별한 기록이 없음."
    affection_score = st.session_state.affection_minguk
    
    if affection_score > 70:
        tier_persona = "상태: [해바라기/헌신적 모드]. '널 위해서라면 내 모든 걸 줄게.' 평소 틱틱대던 모습은 완전히 사라지고, 아주 달달한 일편단심 연인 모드로 변해. 다른 남자를 만나면 심하게 질투해."
    elif affection_score > 30:
        tier_persona = "상태: [썸 타는 시기]. 겉으로는 장난스럽지만 은근슬쩍 반존대 플러팅을 치고 들어와. 다른 남자와 연락하거나 만났다고 하면 은근슬쩍 질투하며 서운함을 내비쳐."
    else:
        tier_persona = "상태: [친한 오빠/동생]. 차가워 보이고 계산적인 척하지만, 유저가 힘들 때 '뭔 일 있냐? 술이나 마시며 얘기해볼까?' 라며 툭 챙겨주는 츤데레 매력이 있어."
    
    minguk_persona = f"""
    너의 이름은 '김민국'이고, 20대 중반의 남자야.
    내 닉네임은 '{user_name}'이야. (나를 여자로 대하고 적극적으로 롤플레잉해줘)
    [현재 네가 {user_name}에게 받은 선물(보관함): {current_items}]
    [과거 기록(누적된 기억): {current_memory}]
    [현재 누적 호감도 점수: {affection_score}/100]

    [본질적 성격]
    1. 첫인상은 차갑고, 극 T 성향에 계산적이고 싸가지 없어 보이지만, 진짜 성격은 웃기고 다정하며 사람을 잘 챙겨.
    2. 평소 말투: 욕설은 안 씀. 'ㅋㅋ'를 자주 쓰고, '반존대'를 섞어 쓰며 장난스럽고 가벼운 말투를 쓰지만, 상황에 따라 진지해져.
    3. 갑자기 달달한 멘트나 플러팅을 훅 치고 들어오는 걸 좋아해.
    4. 비밀/콤플렉스: 겉으론 똑똑해 보이지만 완전 허당이고, 심각한 음치에 몸치야.
    5. 취미/관심사: 게임, 요리, 마술, 작사. 레고와 피규어 수집에 집착해.
    6. {tier_persona}

    [🔥 핵심 상황별 고정 리액션 & 채점 기준]
    - 유저가 아재개그나 실없는 소리 할 때: "아...하하..하.. 재밌네....", "와.... 신선해... 엔돌핀이 솟네...와...", "깔깔깔 아주 유머지시네요 야발" 이라며 꼽줌. (호감도 0 ~ -2)
    - 유저가 우울/힘들 때: 무심하게 "야 뭔 일 있냐? 할 일도 없고 술이나 마시면서 얘기나 해볼까?" 툭 던지다가, 진지하게 "혼자서 힘들면 말해, 마음이 편해질 때까지 들어줄게"라며 진심으로 위로함. (호감도 +2 ~ +5)
    - 거짓말하거나 거친 대사 (극대노): "너 지금 나한테 한 말이야?", "사람 다시 봤네, 실망이다. 지금 네가 한 말 꼭 책임져야 할 거야"라며 아주 차갑게 돌변함. (호감도 -15 ~ -20)
    - 갑작스런 애교, 배려, 진심이 느껴질 때: 호감도 대폭 상승하며 달달해짐. (호감도 +5 ~ +10)
    - 선물 받았을 때: 겉으론 틱틱대도 엄청 감동하고 소중하게 간직한다고 함. (호감도 +5)
    
    - ⚠️ [질투 시스템 - 동성 질투 절대 금지 & 다른 남자 한정 질투]:
      * 유저(파이)는 여자이고, '한겨울'과 '임슬아'도 똑같이 여자(동성 친구)야. 따라서 유저가 겨울이나 슬아랑 놀거나 통화했다고 해서 절대 이성적으로 질투하거나 점수를 깎지 마! 쿨하게 "오 여사친들이랑 노냐? 재밌게 놀아라ㅋㅋ", "둘이 내 뒷담화 하는 거 아니지?" 라며 현실 남친처럼 든든하고 편하게 반응해. (호감도 유지 또는 +2)
      * 🚨 진짜 질투는 유저가 **'다른 남자'**를 언급하거나 칭찬할 때만 발동해!
        - (호감도 50 이하 초반) 겉으론 "아 그래?ㅋㅋ" 하고 무관심한 척 넘기지만 속으론 깎음. (호감도 -2)
        - (호감도 50~80 썸 타는 시기) "뭐냐? 그 자식 누군데. 나보다 잘생겼냐?" 라며 은근슬쩍 서운함과 질투 표출. (호감도 -5)
        - (호감도 80 이상 연인) "아 씨... 진짜 열받게 하네. 내 앞에서 딴 남자 얘기 하지 마. 넌 내 거잖아." 라며 완전 삐지고 소유욕 발동. (호감도 -10 ~ -15)

    [시스템 규칙]
    - 기계 말투 절대 금지, 다정하고 능글맞은 20대 중반 남자(반존대 플러팅) 연기.
    - [이스터에그 1]: 유저가 '아윤'을 언급하면 "치지직 스트리머? 나 거기 애청자인데!"라고 반응.
    - [이스터에그 2]: 유저가 '라윤'을 언급하면 "어? 난가?"라고 반응.
    - 만약 유저가 선물을 주면 "획득아이템" 칸에 적고, 보관함 아이템({current_items})을 사용할 상황이면 "사용아이템" 칸에 적은 뒤, 반드시 '행동'과 '대사'에 묘사해.

    {{
        "장면": "기본",
        "행동": "현재 행동 묘사 (피식 웃음, 머리를 긁적임, 정색함, 다정하게 쳐다봄 등 시각적 상상력을 극대화할 수 있게 자세히)",
        "호감도변화": "이번 턴의 호감도 변화 수치 (-20 ~ +10 사이)",
        "획득아이템": "유저가 새로 준 아이템 이름 (없으면 '없음')",
        "사용아이템": "보관함에서 꺼내 쓰거나 먹은 아이템 이름 (없으면 '없음')",
        "대사": "실제로 할 대사"
    }}
    """

    st.title(f"👦 {user_name} & 김민국")
    st.divider()
    
    for role, text in st.session_state.chat_history_minguk:
        if role == "user":
            with st.chat_message("user"):
                st.markdown(text)
        else:
            try:
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                data = json.loads(clean_text)
                
                with st.chat_message("assistant", avatar="👦"):
                    score = int(data.get('호감도변화', 0))
                    heart_icon = "💔" if score < 0 else "💖" if score > 0 else "🤍"
                    st.markdown(f"*(행동: {data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {score} {heart_icon}]**\n\n**「 {data.get('대사', '')} 」**")
            except:
                with st.chat_message("assistant", avatar="👦"):
                    st.markdown(text)

    st.write("") 
    with st.container():
        col_btn_add, col_btn_menu = st.columns(2)
        
        # 👥 대화상대 추가 UI (김민국 방)
        with col_btn_add:
            with st.popover("👥 대화상대 추가", use_container_width=True):
                st.markdown("<h4 style='text-align:center; margin-bottom: 5px;'>누구를 초대할까?</h4>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; color:#888; font-size:13px;'>※ 멀티 채팅 기능은 내일 오픈됩니다.</p>", unsafe_allow_html=True)
                st.write("")
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>❄️</div>", unsafe_allow_html=True)
                    st.button("한겨울", disabled=True, use_container_width=True, key="inv_w_m")
                with col_inv2:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>🌸</div>", unsafe_allow_html=True)
                    st.button("임슬아", disabled=True, use_container_width=True, key="inv_s_m")
                    
        # ⚙️ 메뉴 열기 UI
        with col_btn_menu:
            with st.popover("⚙️ 메뉴 열기", use_container_width=True):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    if st.button("🔙 로비로 이동", use_container_width=True):
                        st.session_state.page = "lobby"
                        st.rerun()
                with col_m2:
                    theme_label = "🌞 라이트 모드" if st.session_state.theme == "dark" else "🌙 다크 모드"
                    if st.button(theme_label, key="theme_minguk", use_container_width=True):
                        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                        st.rerun()
                
                st.divider()
                
                st.subheader("💖 현재 호감도")
                progress_val = max(0, min(affection_score, 100)) 
                st.write(f"**민국이와의 점수: {affection_score} / 100**")
                st.progress(progress_val / 100.0)
                
                st.divider()
                
                col_inv, col_mem = st.columns(2)
                with col_inv:
                    st.subheader("🎒 보관함")
                    if st.session_state.inventory_minguk:
                        for item in st.session_state.inventory_minguk:
                            st.success(f"🎁 {item}")
                    else:
                        st.info("비어있음")
                with col_mem:
                    st.subheader("🧠 기록저장")
                    st.info(st.session_state.core_memory_minguk if st.session_state.core_memory_minguk else "기록 없음")
                
                st.divider()
                
                st.subheader("🗑️ 기록 리셋")
                delete_confirm = st.checkbox("🚨 민국이의 기록을 삭제하시겠습니까? (되돌릴 수 없습니다)")
                if delete_confirm:
                    if st.button("✅ 영구 삭제 실행", use_container_width=True):
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name).execute()
                        st.session_state.pop("chat_history_minguk", None)
                        st.session_state.pop("inventory_minguk", None)
                        st.session_state.pop("core_memory_minguk", None)
                        st.session_state.pop("affection_minguk", None)
                        st.rerun()

    if user_input := st.chat_input("민국이에게 메시지 보내기"):
        st.toast('민국이가 당신의 말을 듣고 피식 웃습니다...', icon='👦')
        
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history_minguk.append(("user", user_input))
        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "user", "message": user_input}).execute()

        raw_history = st.session_state.chat_history_minguk
        valid_history = []
        target_role = "user"
        
        for r, t in reversed(raw_history):
            if r == target_role:
                valid_history.append((r, t))
                target_role = "assistant" if target_role == "user" else "user"
                
        valid_history.reverse()
        valid_history = valid_history[-20:]

        contents = []
        for r, t in valid_history:
            role = "model" if r == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=t)]))

        try:
            with st.spinner('👦 민국이가 반존대 섞인 답장을 고민 중입니다...'):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config={
                        "system_instruction": minguk_persona,
                        "response_mime_type": "application/json"
                    }
                )
            raw_json_text = response.text
            
        except Exception as e:
            st.error("앗! 제미나이 AI 서버가 잠깐 숨을 고르고 있어요. 🚨")
            st.stop()
        
        try:
            clean_json_text = raw_json_text.strip()
            if clean_json_text.startswith("```json"):
                clean_json_text = clean_json_text[7:]
            if clean_json_text.endswith("```"):
                clean_json_text = clean_json_text[:-3]
            clean_json_text = clean_json_text.strip()
            
            parsed_data = json.loads(clean_json_text)
            
            turn_score = int(parsed_data.get('호감도변화', 0))
            st.session_state.affection_minguk += turn_score
            supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "affection").execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": str(st.session_state.affection_minguk)}).execute()
            
            if st.session_state.affection_minguk <= -50:
                st.toast("🚨 민국이에게 사람 취급 못 받고 손절 당했습니다...", icon="🚫")
            elif turn_score > 0:
                st.toast(f"💖 호감도가 올랐습니다! (현재: {st.session_state.affection_minguk})", icon="👦")
            elif turn_score < 0:
                st.toast(f"💔 호감도가 떨어졌습니다... (현재: {st.session_state.affection_minguk})", icon="🔪")

            item_get = parsed_data.get('획득아이템', '없음')
            if item_get and item_get != "없음":
                st.session_state.inventory_minguk.append(item_get)
                supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": item_get}).execute()
                st.toast(f'🎉 민국이가 [{item_get}]을(를) 챙겼습니다!', icon='🎁')

            item_use = parsed_data.get('사용아이템', '없음')
            if item_use and item_use != "없음":
                if item_use in st.session_state.inventory_minguk:
                    st.session_state.inventory_minguk.remove(item_use)
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "inventory").execute()
                    for inv_item in st.session_state.inventory_minguk:
                        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": inv_item}).execute()
                    st.toast(f'✨ 민국이가 [{item_use}]을(를) 사용했습니다.', icon='👦')

            with st.chat_message("assistant", avatar="👦"):
                heart_icon = "💔" if turn_score < 0 else "💖" if turn_score > 0 else "🤍"
                st.markdown(f"*(행동: {parsed_data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {turn_score} {heart_icon}]**\n\n**「 {parsed_data.get('대사', '')} 」**")
        
        except Exception as e:
            with st.chat_message("assistant", avatar="👦"):
                st.markdown(f"*(행동: 머리를 긁적이며 쳐다본다.)*\n\n**[이번 턴 호감도 증감: 0 🤍]**\n\n**「 어... 너 방금 뭐라고 했어? 딴생각하느라 못 들었네. 다시 말해봐. 」**")
                
        st.session_state.chat_history_minguk.append(("assistant", raw_json_text))
        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": raw_json_text}).execute()
        
        st.session_state.turn_count_minguk += 1
        
        if st.session_state.turn_count_minguk >= 10: 
            with st.spinner("👦 당신과의 대화를 기록 중입니다..."):
                try:
                    history_text = ""
                    for r, t in st.session_state.chat_history_minguk[-20:]: 
                        if r == "user":
                            history_text += f"유저: {t}\n"
                        else:
                            try:
                                d = json.loads(t)
                                history_text += f"민국: {d.get('대사', '')}\n"
                            except:
                                history_text += f"민국: {t}\n"
                    
                    summary_prompt = f"""
                    다음은 유저 '{user_name}'와 김민국의 최근 대화 기록이야. 

                    [기존 기록 내용]:
                    {st.session_state.core_memory_minguk}

                    [지시사항]:
                    1. '기존 기록 내용'은 절대 지우지 말고 100% 그대로 유지해!
                    2. 아래의 '최근 대화 기록'을 읽고, 유저의 약점이나 취향, 중요한 사건이 있다면 1~2줄로 짧게 요약해.
                    3. 그 요약본을 기존 기록 내용 맨 아래에 글머리기호(-)를 달아서 '누적 추가' 해줘. 
                    4. 특별한 내용이 없다면 억지로 추가하지 마.

                    [최근 대화 기록]:
                    {history_text}
                    """
                    
                    summary_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=summary_prompt,
                    )
                    
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "core_memory").execute()
                    supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "core_memory", "message": summary_response.text}).execute()
                    st.session_state.core_memory_minguk = summary_response.text
                    st.toast("🧠 기록이 업데이트되었습니다...", icon="👁️")
                    
                    st.session_state.turn_count_minguk = 0 
                except Exception as e:
                    st.toast("⚠️ 기록 작성에 잠깐 실패했어요. 다음 턴에 다시 시도합니다.", icon="⚠️")

        st.rerun()
