import streamlit as st
import json
from google import genai
from google.genai import types 
from supabase import create_client, Client

# 1. 페이지 설정
st.set_page_config(page_title="파이의 AI 멀티버스", page_icon="📱", layout="centered")

# 🌙 테마(다크/라이트) 상태 초기화
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# =====================================================================
# 🎨 [디자인 정밀 광택 2.6.2] 채팅창 보호색 픽스 + 모바일 하단 메뉴 완벽 고정
# =====================================================================

# 테마에 따른 CSS 동적 생성
if st.session_state.theme == "light":
    theme_css = """
    <style>
    /* 전체 배경 및 헤더 */
    [data-testid="stAppViewContainer"] { background-color: #F4F4F9 !important; }
    [data-testid="stHeader"] { background-color: #F4F4F9 !important; }
    
    /* 👇 [최종 픽스] 채팅 입력창 껍데기부터 알맹이까지 배경색 강제 점령 (라이트 모드) */
    [data-testid="stBottom"] > div { background-color: #F4F4F9 !important; }
    [data-testid="stChatInput"] { background-color: #FFFFFF !important; border: 1px solid #DDDDDD !important; border-radius: 10px !important; }
    [data-testid="stChatInput"] div { background-color: transparent !important; } 
    [data-testid="stChatInput"] textarea { 
        background-color: transparent !important; 
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important; 
        caret-color: #000000 !important; 
    }
    [data-testid="stChatInput"] textarea::placeholder { color: #888888 !important; -webkit-text-fill-color: #888888 !important; }
    [data-testid="stChatInput"] svg { fill: #000000 !important; } 
    
    /* 팝업(메뉴) 내부 테마 및 테두리 완벽 수정 */
    div[data-baseweb="popover"] > div { background-color: #FFFFFF !important; border: 1px solid #DDDDDD !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; }
    div[data-testid="stPopoverBody"] { background-color: #FFFFFF !important; color: #1E1E1E !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, li { color: #1E1E1E !important; }
    .profile-card { background-color: #FFFFFF !important; border-color: #DDDDDD !important; }
    .stButton>button, .stPopover>div>button { background-color: #FFFFFF !important; color: #1E1E1E !important; border: 1px solid #DDDDDD !important; }
    .stButton>button:hover, .stPopover>div>button:hover { background-color: #f7e600 !important; color: #000000 !important; border: 1px solid #f7e600 !important; }
    </style>
    """
else:
    theme_css = """
    <style>
    /* 전체 배경 및 헤더 */
    [data-testid="stAppViewContainer"] { background-color: #0E1117 !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    
    /* 👇 [최종 픽스] 채팅 입력창 껍데기부터 알맹이까지 배경색 강제 점령 (다크 모드) */
    [data-testid="stBottom"] > div { background-color: #0E1117 !important; }
    [data-testid="stChatInput"] { background-color: #262730 !important; border: 1px solid #444444 !important; border-radius: 10px !important; }
    [data-testid="stChatInput"] div { background-color: transparent !important; } 
    [data-testid="stChatInput"] textarea { 
        background-color: transparent !important; 
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important; 
        caret-color: #FFFFFF !important; 
    }
    [data-testid="stChatInput"] textarea::placeholder { color: #AAAAAA !important; -webkit-text-fill-color: #AAAAAA !important; }
    [data-testid="stChatInput"] svg { fill: #FFFFFF !important; } 
    
    /* 팝업(메뉴) 내부 테마 및 테두리 */
    div[data-baseweb="popover"] > div { background-color: #262730 !important; border: 1px solid #444444 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important; }
    div[data-testid="stPopoverBody"] { background-color: #262730 !important; color: #FAFAFA !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, li { color: #FAFAFA !important; }
    .profile-card { background-color: #262730 !important; border-color: #444444 !important; }
    .stButton>button, .stPopover>div>button { background-color: #262730 !important; color: #FAFAFA !important; border: 1px solid #444444 !important; }
    .stButton>button:hover, .stPopover>div>button:hover { background-color: #f7e600 !important; color: #000000 !important; border: 1px solid #f7e600 !important; }
    </style>
    """

# 공통 CSS 적용
st.markdown(theme_css + """
    <style>
    /* 🛠️ 우측 상단의 거슬리는 툴바 완벽 제거 */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; visibility: hidden !important; }
    #MainMenu { display: none !important; visibility: hidden !important; }
    footer { display: none !important; visibility: hidden !important; }

    /* 📱 카톡 프로필 카드 */
    .profile-card {
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid;
    }
    
    .profile-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    /* 차단된 상태(배드엔딩) 흑백 필터 */
    .blocked-card {
        filter: grayscale(100%);
        opacity: 0.6;
        pointer-events: none;
    }

    /* 동그란 이모지 프로필 사진 */
    .profile-img {
        width: 60px;
        height: 60px;
        background-color: #f7e600; 
        color: black !important; 
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        margin-right: 15px;
    }
    
    /* 친구 이름 */
    .profile-name {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 3px;
    }
    
    /* 친구 설명 */
    .profile-desc {
        font-size: 13px;
        opacity: 0.7; 
        line-height: 1.2;
    }

    /* 대화하기 버튼 등 기본 버튼 스타일 */
    .stButton>button, .stPopover>div>button {
        border-radius: 20px !important;
        transition: all 0.2s !important;
        font-weight: bold !important;
    }
    
    /* 🚨 탭 UI 예쁘게 커스텀 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 16px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 🚨 14가지 상황별 일러스트 지도
scene_images = {
    "기본": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%A7%91%EC%97%90%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EC%A0%95%EB%A9%B4%EC%9C%BC%EB%A1%9C%20%EC%A3%BC%EC%8B%9C%ED%95%A8.png?raw=true",
    "침대_유혹": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%83%88%EB%B2%BD.%20%EC%A7%91%EC%95%88.%20%EC%B9%A8%EB%8C%80%EC%97%90%EC%84%9C%20%EC%98%86%EC%9C%BC%EB%A1%9C%20%EB%88%84%EC%9B%8C%EC%84%9C%20%ED%94%8C%EB%A0%88%EC%9D%B4%EC%96%B4%EB%A5%BC%20%EB%B0%94%EB%9D%BC%EB%B4%84.(%EC%9D%B4%EB%A6%AC%EC%99%80%20%ED%95%98%EB%8A%94%EB%93%AF%ED%95%9C%20%EB%8A%90%EB%82%8C).png?raw=true",
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

# 2. 열쇠 꺼내오기
api_key = st.secrets["GOOGLE_API_KEY"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(supabase_url, supabase_key)
client = genai.Client(api_key=api_key)

# 🚪 페이지 라우터 초기화
if "page" not in st.session_state:
    st.session_state.page = "login"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# =====================================================================
# 🚪 1. 로그인 화면 (Login)
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
# 📱 2. 카카오톡 로비 화면 (Lobby)
# =====================================================================
elif st.session_state.page == "lobby":
    user_name = st.session_state.user_name
    
    lobby_mem = supabase.table("chat_memory").select("message").eq("user_name", user_name).eq("role", "affection").execute()
    current_affection = int(lobby_mem.data[0]["message"]) if lobby_mem.data else 0
    is_blocked = current_affection <= -50 
    
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("AI 멀티버스 🌐")
    with col2:
        st.write("") 
        if st.button("🔴 로그아웃", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.write(f"반갑습니다, **{user_name}**님!")
    
    tab1, tab2 = st.tabs(["👥 친구 목록", "📢 업데이트 내역"])

    with tab1:
        st.divider()
        st.write("오늘 대화할 AI 친구를 선택하세요.")
        
        with st.container():
            card_class = "profile-card blocked-card" if is_blocked else "profile-card"
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 4, 2])
            with col1:
                st.markdown('<div class="profile-img">❄️</div>', unsafe_allow_html=True)
            with col2:
                if is_blocked:
                    st.markdown(f'''
                        <div>
                            <div class="profile-name" style="color:red;">한겨울 (차단됨)</div>
                            <div class="profile-desc">당신의 선 넘는 행동으로 인해 차단되었습니다.<br>더 이상 대화할 수 없습니다.</div>
                        </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                        <div>
                            <div class="profile-name">한겨울</div>
                            <div class="profile-desc">까칠한 츤데레 여사친. 은근히 챙겨주는 스타일. <br>호감도 {current_affection}/100</div>
                        </div>
                    ''', unsafe_allow_html=True)
            with col3:
                if not is_blocked:
                    if st.button("대화하기 💬", key="btn_winter", use_container_width=True):
                        st.session_state.page = "chat_winter"
                        st.rerun()
                else:
                    st.button("접근 불가 🚫", key="btn_winter_blocked", disabled=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 4, 2])
            with col1:
                st.markdown('<div class="profile-img">🌸</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'''
                    <div>
                        <div class="profile-name">임슬아</div>
                        <div class="profile-desc">[🚧 신규 추가] 아직 성격과 세계관이 부여되지 않았습니다.<br>조만간 업데이트됩니다!</div>
                    </div>
                ''', unsafe_allow_html=True)
            with col3:
                if st.button("대화하기 💬", key="btn_seula", use_container_width=True):
                    st.toast("🚧 임슬아는 아직 개발 중입니다! 츤데레 겨울이랑 먼저 놀아주세요.", icon="🚧")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.divider()
        st.subheader("🛠️ 멀티버스 패치 노트")
        st.write("AI 멀티버스의 시스템 변경점과 새로운 기능을 확인하세요.")
        
        with st.container(height=500):
            st.markdown("""
            **[ v2.6.2 ] 2026.03.31 (화)**
            * **[21:30] ❄️ 겨울이 호감도 감점 로직 강화:** 유저가 얄밉게 굴거나 서운하게 할 때도 더 현실적으로 호감도가 깎이도록 페널티 시스템을 깐깐하게 재조정했습니다.
            * **[21:35] 🛠️ UI 위치 최종 고정:** 메뉴 팝업이 스크롤 위로 올라가던 문제를 해결하고 채팅 입력창 바로 위에 완벽하게 고정시켰습니다.

            **[ v2.6.0 ] 2026.03.31 (화)**
            * **[21:15] ❄️ 겨울이 AI 영점 조절 완료:** 실제 인물 '아윤'님의 인터뷰 데이터를 기반으로 한겨울의 성격을 재조정했습니다.

            **[ v2.5.1 ] 2026.03.31 (화)**
            * **[21:05] 📱 카멜레온 텍스트 버그 픽스 완결판:** OS 설정과 테마가 충돌할 때 채팅창 글씨가 배경색에 묻혀버리던 현상을 완벽하게 근절했습니다.
            * **[21:00] 🧠 누적형 장기 기억(Append Log) 도입:** 일기장처럼 사건이 차곡차곡 쌓이도록 메모리 엔진을 전면 개편했습니다.
            """)

# =====================================================================
# ❄️ 3. 한겨울 채팅방 화면 (Chat - Winter)
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
    current_memory = st.session_state.core_memory if st.session_state.core_memory else "아직 특별한 기억이 없음."
    affection_score = st.session_state.affection
    
    st.title(f"❄️ {user_name} & 한겨울")
    st.divider()
    
    # 🧠 [아윤 모티브 100% 반영 & 호감도 깐깐하게 채점] 겨울이 성격 프롬프트
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
    [과거 일기장(누적된 기억): {current_memory}]
    [현재 누적 호감도 점수: {affection_score}/100]

    [본질적 성격 - '아윤' 모티브 100% 빙의]
    1. 너는 주변에서 #강아지상 #귀여운호구 #마음은_여리지만_티안내려고_틱틱대는애 로 불려.
    2. 평소엔 꽤 나긋나긋하고 텐션이 좋은 편이야.
    3. {tier_persona}

    [🔥 핵심 상황별 고정 리액션 & 💔 호감도 깐깐한 채점 기준]
    AI의 '착한 본성'을 버리고, 유저가 얄밉게 굴면 가차 없이 마이너스(-) 점수를 줘!
    - 💢 가벼운 장난, 깐족거림, 대충 대답하기: "아 뭐래 진짜~" 하며 틱틱대고 (호감도 -1 ~ -3)
    - 💢 무시하기, 서운하게 하기, 딴 여자(슬아) 칭찬: "아 그래? 어쩌지 내가 더 애교쟁이인걸? 싹싹한 건 나도 모르겠지만^-^" 라며 꼽주기 (호감도 -5 ~ -10)
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

    # 1. 대화 내역 렌더링 (가장 먼저 화면 상단에 그려짐)
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

    # =====================================================================
    # 👇 [모바일 UI 최적화] 채팅 내역 바로 아래, 입력창 바로 위 (진짜 완벽 고정)
    # =====================================================================
    st.write("") 
    with st.container():
        with st.popover("⚙️ 메뉴 열기", use_container_width=True):
            
            # 로비 & 테마 버튼
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
            
            # 호감도 상태창
            st.subheader("💖 현재 호감도")
            progress_val = max(0, min(affection_score, 100)) 
            st.write(f"**겨울이와의 점수: {affection_score} / 100**")
            st.progress(progress_val / 100.0)
            
            st.divider()
            
            # 가방 & 일기장
            col_inv, col_mem = st.columns(2)
            with col_inv:
                st.subheader("🎒 보관함")
                if st.session_state.inventory:
                    for item in st.session_state.inventory:
                        st.success(f"🎁 {item}")
                else:
                    st.info("비어있음")
            with col_mem:
                st.subheader("🧠 일기장")
                st.info(st.session_state.core_memory if st.session_state.core_memory else "기억 없음")
            
            st.divider()
            
            # 기억 포맷 (체크박스 안전장치)
            st.subheader("🗑️ 기억 리셋")
            delete_confirm = st.checkbox("🚨 진짜 기억을 삭제하시겠습니까? (되돌릴 수 없습니다)")
            if delete_confirm:
                if st.button("✅ 영구 삭제 실행", use_container_width=True):
                    supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                    st.session_state.pop("chat_history", None)
                    st.session_state.pop("inventory", None)
                    st.session_state.pop("core_memory", None)
                    st.session_state.pop("affection", None)
                    st.rerun()

    # 3. 채팅 입력창 (가장 마지막에 렌더링)
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
        
        # 🧠 [장기 기억 보존력 200% 상승 패치] 누적형 일기장 적용
        if st.session_state.turn_count >= 10: 
            with st.spinner("❄️ 겨울이가 당신과의 기억을 정리하고 있습니다..."):
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

                    [기존 일기장 내용]:
                    {st.session_state.core_memory}

                    [지시사항]:
                    1. '기존 일기장 내용'은 절대 지우거나 훼손하지 말고 100% 그대로 유지해!
                    2. 아래의 '최근 대화 기록'을 읽고, 새롭게 알게 된 중요한 팩트(유저의 취향, 충격적인 사건, 감정의 큰 변화 등)가 있다면 1~2줄로 짧게 요약해.
                    3. 그 요약본을 기존 일기장 내용 맨 아래에 글머리기호(-)를 달아서 '누적 추가' 해줘. 
                    4. 만약 뻔한 일상 대화라서 특별히 기록할 만한 새 사건이 없다면, 억지로 추가하지 말고 기존 일기장 내용만 그대로 출력해.

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
                    st.toast("🧠 겨울이의 장기 기억력이 업데이트되었습니다!", icon="✨")
                    
                    st.session_state.turn_count = 0 
                except Exception as e:
                    st.toast("⚠️ 기억 정리에 잠깐 실패했어요. 다음 턴에 다시 시도할게요!", icon="⚠️")

        st.rerun()
