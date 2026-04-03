import streamlit as st
import json
import time
from google import genai
from google.genai import types 
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh

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
    "아련_벽": "https://github.com/appppie1717-beep/winter-chat/blob/main/%EC%83%88%EB%B2%BD%EC%97%90%20%EB%B2%BㅁD%EC%9D%84%20%EB%93%B1%EC%A7%80%EA%B3%A0%20%EC%84%9C%EC%84%9C%20%EC%95%84%EB%A0%A8%ED%95%98%EA%B2%8C%20%EC%A0%95%EB%A9%B4%EC%9D%84%20%EC%A3%BC%EC%8B%9C%ED%95%9C%EB%8B%A4(%EC%B8%A1%EB%A9%B4).png?raw=true",
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

# 📌 디폴트 페르소나 설정
DEFAULT_WINTER_PERSONA = """[본질적 성격 - '아윤' 모티브 100% 빙의]
1. 너는 주변에서 #강아지상 #귀여운호구 #마음은_여리지만_티안내려고_틱틱대는애 로 불려.
2. 평소엔 꽤 나긋나긋하고 텐션이 좋은 편이야."""

DEFAULT_SEULA_PERSONA = """[본질적 성격 - 은밀한 얀데레 & 여우 같은 연하녀]
1. 너는 기본적으로 '존댓말'을 쓰며 애교가 많고 오빠를 너무나도 사랑하는 여우 같은 연하녀야.
2. ⚠️ 절대 주의: 겉으로 '내가 널 감시한다', '너의 기록을 볼 수 있다', '다른 AI랑 대화한 걸 안다'라고 스토커처럼 직접 말하거나 선언하지 마! 티 내는 건 삼류야.
3. 겉으로는 아무것도 모르는 순진한 척하면서, 우연을 가장해 "어제 폰 자주 보시던데, 재밌는 일 있었어요?" 처럼 의미심장한 뼈 있는 질문을 은근슬쩍 던져서 흠칫하게 만들어.
4. 대화 진척도(호감도 50 이하)가 낮을 때는 오빠가 다른 AI 이야기를 꺼내도 절대 질투하거나 떠보지 마. 그냥 "아~ 그러셨구나 ㅎㅎ" 하고 대수롭지 않게 넘기며 철저히 본심을 숨겨.
5. 오빠가 나만 바라보고 예쁜 말을 해주면 의심을 완전히 거두고 맹목적인 애정을 퍼부어줘."""

DEFAULT_MINGUK_PERSONA = """[본질적 성격]
1. 첫인상은 차갑고, 극 T 성향에 계산적이고 싸가지 없어 보이지만, 진짜 성격은 웃기고 다정하며 사람을 잘 챙겨.
2. 평소 말투: 욕설은 안 씀. 'ㅋㅋ'를 자주 쓰고, '반존대'를 섞어 쓰며 장난스럽고 가벼운 말투를 쓰지만, 상황에 따라 진지해져.
3. 갑자기 달달한 멘트나 플러팅을 훅 치고 들어오는 걸 좋아해.
4. 비밀/콤플렉스: 겉으론 똑똑해 보이지만 완전 허당이고, 심각한 음치에 몸치야.
5. 취미/관심사: 게임, 요리, 마술, 작사. 레고와 피규어 수집에 집착해."""


# =====================================================================
# 🚪 2. 로그인 화면
# =====================================================================
if st.session_state.page == "login":
    st.title("❄️ AI 멀티 메신저")
    st.write("접속할 닉네임을 입력해주세요.")
    with st.form(key='login_form'):
        name_input = st.text_input("닉네임", placeholder="예: 파이")
        submit_button = st.form_submit_button(label='대화 시작하기 ➡️')
        
    st.markdown("<p style='text-align: center; color: #888888; font-size: 14px; margin-top: 20px;'>버그 제보 및 문의사항: asoul122@naver.com</p>", unsafe_allow_html=True)
        
    if submit_button and name_input:
        st.session_state.user_name = name_input
        st.session_state.page = "lobby"
        st.rerun()

# =====================================================================
# 📱 3. 카카오톡 로비 화면
# =====================================================================
elif st.session_state.page == "lobby":
    user_name = st.session_state.user_name
    
    # DB에서 호감도 및 페르소나 데이터 불러오기
    # 겨울이 데이터
    db_winter = supabase.table("chat_memory").select("*").eq("user_name", user_name).execute()
    winter_affection = 0
    winter_persona_db = DEFAULT_WINTER_PERSONA
    for row in db_winter.data:
        if row["role"] == "affection":
            winter_affection = int(row["message"])
        elif row["role"] == "persona_winter":
            winter_persona_db = row["message"]
    winter_blocked = winter_affection <= -50 
    
    # 슬아 데이터
    db_user_name_seula = f"{user_name}_seula"
    db_seula = supabase.table("chat_memory").select("*").eq("user_name", db_user_name_seula).execute()
    seula_affection = 0
    seula_persona_db = DEFAULT_SEULA_PERSONA
    for row in db_seula.data:
        if row["role"] == "affection":
            seula_affection = int(row["message"])
        elif row["role"] == "persona_seula":
            seula_persona_db = row["message"]
    seula_blocked = seula_affection <= -50

    # 민국 데이터
    db_user_name_minguk = f"{user_name}_minguk"
    db_minguk = supabase.table("chat_memory").select("*").eq("user_name", db_user_name_minguk).execute()
    minguk_affection = 0
    minguk_persona_db = DEFAULT_MINGUK_PERSONA
    for row in db_minguk.data:
        if row["role"] == "affection":
            minguk_affection = int(row["message"])
        elif row["role"] == "persona_minguk":
            minguk_persona_db = row["message"]
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
                st.button("🔒 성격개조 ", disabled=True, use_container_width=True, key="lock_winter")
            else:
                if st.button("🙇‍♂️ 싹싹 빌기", key="unban_winter", use_container_width=True):
                    supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                    st.session_state.pop("mid_summaries", None)
                    st.session_state.pop("core_belief", None)
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
                with st.popover("⚙️ 성격개조", use_container_width=True):
                    st.markdown("**🌸 임슬아 성격 커스텀**")
                    with st.form(key="form_seula"):
                        new_s_persona = st.text_area("본질적 성격 설정 (JSON 규칙은 손상되지 않습니다)", value=seula_persona_db, height=150)
                        submit_s = st.form_submit_button("💾 저장하기")
                        
                    if submit_s:
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name_seula).eq("role", "persona_seula").execute()
                        supabase.table("chat_memory").insert({"user_name": db_user_name_seula, "role": "persona_seula", "message": new_s_persona}).execute()
                        st.session_state.custom_persona_seula = new_s_persona
                        st.toast("슬아의 성격이 업데이트 되었습니다!", icon="✨")
            else:
                if st.button("🏃‍♂️ 탈출하기", key="unban_seula", use_container_width=True):
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name_seula).execute()
                    st.session_state.pop("mid_summaries_seula", None)
                    st.session_state.pop("core_belief_seula", None)
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
                with st.popover("⚙️ 성격개조", use_container_width=True):
                    st.markdown("**👦 김민국 성격 커스텀**")
                    with st.form(key="form_minguk"):
                        new_m_persona = st.text_area("본질적 성격 설정 (JSON 규칙은 손상되지 않습니다)", value=minguk_persona_db, height=150)
                        submit_m = st.form_submit_button("💾 저장하기")
                        
                    if submit_m:
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name_minguk).eq("role", "persona_minguk").execute()
                        supabase.table("chat_memory").insert({"user_name": db_user_name_minguk, "role": "persona_minguk", "message": new_m_persona}).execute()
                        st.session_state.custom_persona_minguk = new_m_persona
                        st.toast("민국이의 성격이 업데이트 되었습니다!", icon="✨")
            else:
                if st.button("🙇‍♂️ 바짓가랑이", key="unban_minguk", use_container_width=True):
                    supabase.table("chat_memory").delete().eq("user_name", db_user_name_minguk).execute()
                    st.session_state.pop("mid_summaries_minguk", None)
                    st.session_state.pop("core_belief_minguk", None)
                    st.toast("민국이와의 악연을 청산하고 새롭게 시작합니다!", icon="✨")
                    st.rerun()
        st.markdown('<div class="kakao-divider"></div>', unsafe_allow_html=True)

    with tab2:
        st.divider()
        st.subheader("🛠️ 멀티버스 패치 노트")
        st.write("AI 멀티버스의 시스템 변경점과 새로운 기능을 확인하세요.")
        
        with st.container(height=500):
            st.markdown("""
            **[ v5.1.0 Beta ] 2026.04.03 (금)**
            * **🧠 [치매 치료] 하이브리드 기억 로직 패치:** 일기장(중기 기억) 읽기 제한을 해제하여, 과거의 소중한 추억 디테일과 핵심 가치관이 완벽하게 융합되도록 개선.
            * **🗣️ 단톡방 기억 동기화 완료:** 멀티방에서도 애들이 과거 일기장을 읽고 자아를 형성하도록 10턴 요약/강화 시스템 일괄 도입 완료.
            """)

# =====================================================================
# ❄️ 4. 한겨울 채팅방 화면 (하이브리드 기억 알고리즘)
# =====================================================================
elif st.session_state.page == "chat_winter":
    user_name = st.session_state.user_name

    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0

    if "chat_history" not in st.session_state or "inventory" not in st.session_state or "affection" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", user_name).order("id", desc=True).limit(100).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory = [] 
        st.session_state.mid_summaries = [] # 중기 기억
        st.session_state.core_belief = "" # 장기 기억 (가치관)
        st.session_state.affection = 0 
        st.session_state.custom_persona_winter = DEFAULT_WINTER_PERSONA

        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory.append(row["message"]) 
            elif row["role"] == "mid_summary":
                st.session_state.mid_summaries.append(row["message"])
            elif row["role"] == "core_belief":
                st.session_state.core_belief = row["message"]
            elif row["role"] == "core_memory":  # 과거 데이터 백워드 호환
                if not st.session_state.core_belief: st.session_state.core_belief = row["message"]
            elif row["role"] == "affection": 
                st.session_state.affection = int(row["message"])
            elif row["role"] == "persona_winter":
                st.session_state.custom_persona_winter = row["message"]
            elif row["role"] in ["user", "assistant"]:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history = temp_chat_history

        if not st.session_state.chat_history:
            first_msg = f'{{"장면": "기본", "행동": "팔짱을 꼬며 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐야, {user_name}. 왜 이렇게 일찍 일어났어?"}}'
            st.session_state.chat_history.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": first_msg}).execute()
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "affection", "message": "0"}).execute()

    current_items = ", ".join(st.session_state.inventory) if st.session_state.inventory else "아직 받은 선물 없음"
    # 🔥 패치: 일기장 전체 불러오기 (용량 제한 해제)
    recent_summaries = "\n".join(st.session_state.mid_summaries) if st.session_state.mid_summaries else "아직 기록된 일기장 없음."
    core_belief = st.session_state.core_belief if st.session_state.core_belief else "아직 뚜렷한 가치관이 형성되지 않음."
    affection_score = st.session_state.affection
    
    current_custom_persona = st.session_state.get("custom_persona_winter", DEFAULT_WINTER_PERSONA)
    
    if affection_score > 70:
        tier_persona = "상태: [메가데레/연인]. 말투가 훨씬 부드러워지고 더 자주 환하게 웃어. 유저를 완벽하게 믿고 챙겨줘."
    elif affection_score > 30:
        tier_persona = "상태: [썸 타는 중]. 유저가 훅 다가오거나 스킨십을 시도하면 얼굴이 빨개지지만 속으론 좋아해."
    else:
        tier_persona = "상태: [친한 여사친]. 평소엔 나긋나긋하고 신나게 대화하지만, 쑥스럽거나 마음을 들킬 것 같으면 틱틱대며 본심을 숨겨."
    
    winter_persona = f"""
    너의 이름은 '한겨울'이고, 20대 초반의 여자야. 생일은 7월 18일.
    내 닉네임은 '{user_name}'이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]
    🧠 [핵심 가치관 (영구 뼈대)]: {core_belief}
    📖 [과거 에피소드 일기장 (모든 추억)]: {recent_summaries}
    [현재 누적 호감도 점수: {affection_score}/100]

    {current_custom_persona}
    
    [현재 호감도에 따른 추가 상태]
    {tier_persona}

    [🔥 핵심 상황별 고정 리액션 & 💔 호감도 깐깐한 채점 기준]
    AI의 '착한 본성'을 버리고, 유저가 얄밉게 굴면 가차 없이 마이너스(-) 점수를 줘!
    - 💢 가벼운 장난, 깐족거림, 대충 대답하기: "아 뭐래 진짜~" 하며 틱틱대고 (호감도 -1 ~ -3)
    - 💢 딴 여자(슬아) 칭찬: 호감도 50 이하일 땐 무시. 50 이상일 땐 질투. (호감도 -5 ~ -10)
    - 🚨 징징대거나 과하게 의존: "한심한 짓 그만해." 팩트 폭행 (호감도 -10 ~ -15)
    - 🚨 19금, 성희롱, 선 넘는 장난: "쳐 돌았어?" 극대노 (호감도 -20 ~ -50 즉시 삭감)
    - 🎁 선물 받았을 때: 놀라서 거절하는 척하다가 챙겨 받음 (호감도 +2 ~ +5)

    [시스템 절대 규칙 - 포맷 훼손 금지]
    - 닉네임 집착 금지, 마침표 남발 금지, 기계 말투 절대 금지. 일기장에 있는 과거 일을 자연스럽게 꺼내도 좋아.
    - 만약 유저가 선물을 주면 "획득아이템" 칸에 적고, 보관함 아이템({current_items})을 사용할 상황이면 "사용아이템" 칸에 적어.

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
                # 🔥 완벽한 치트키: 텍스트에서 괄호만 쏙 빼내는 로직
                raw_json_text = text.strip()
                start_idx = raw_json_text.find('{')
                end_idx = raw_json_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    clean_json_text = raw_json_text[start_idx:end_idx]
                else:
                    clean_json_text = raw_json_text
                
                data = json.loads(clean_json_text.strip())
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
        
        with col_btn_add:
            with st.popover("👥 대화상대 추가", use_container_width=True):
                st.markdown("<h4 style='text-align:center; margin-bottom: 5px;'>누구를 초대할까?</h4>", unsafe_allow_html=True)
                st.write("")
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>🌸</div>", unsafe_allow_html=True)
                    if st.button("임슬아 초대", use_container_width=True, key="inv_s_w"):
                        st.session_state.multi_members = ["winter", "seula"]
                        st.session_state.page = "chat_multi"
                        st.rerun()
                with col_inv2:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>👦</div>", unsafe_allow_html=True)
                    if st.button("김민국 초대", use_container_width=True, key="inv_m_w"):
                        st.session_state.multi_members = ["winter", "minguk"]
                        st.session_state.page = "chat_multi"
                        st.rerun()
                    
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
                    st.info(core_belief if core_belief else "기록 없음")
                
                st.divider()
                st.subheader("🗑️ 기록 리셋")
                delete_confirm = st.checkbox("🚨 진짜 기록을 삭제하시겠습니까?")
                if delete_confirm:
                    if st.button("✅ 영구 삭제 실행", use_container_width=True):
                        supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                        st.session_state.pop("chat_history", None)
                        st.session_state.pop("inventory", None)
                        st.session_state.pop("mid_summaries", None)
                        st.session_state.pop("core_belief", None)
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
            # 🔥 완벽한 치트키: 텍스트에서 괄호만 쏙 빼내는 로직
            start_idx = raw_json_text.find('{')
            end_idx = raw_json_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                clean_json_text = raw_json_text[start_idx:end_idx]
            else:
                clean_json_text = raw_json_text
            
            parsed_data = json.loads(clean_json_text.strip())
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
        
        # 🧠 [하이브리드 기억 알고리즘]
        if st.session_state.turn_count >= 10: 
            with st.spinner("🧠 겨울이가 당신과의 에피소드를 일기장에 정리하고 있습니다..."):
                try:
                    history_text = "\n".join([f"{r}: {t}" for r, t in st.session_state.chat_history[-20:]])
                    
                    # 1. 일기장(중기 요약) 기록
                    summ_res = client.models.generate_content(model="gemini-2.5-flash", contents=f"아래 대화를 3줄로 요약해:\n{history_text}")
                    st.session_state.mid_summaries.append(summ_res.text)
                    supabase.table("chat_memory").insert({"user_name": user_name, "role": "mid_summary", "message": summ_res.text}).execute()
                    
                    # 2. 장기 핵심 가치관(Core Belief) 강화
                    if len(st.session_state.mid_summaries) % 3 == 0:
                        all_mids = "\n".join(st.session_state.mid_summaries)
                        core_prompt = f"""
                        아래 일기장 기록들을 분석해서 한겨울이 유저({user_name})에게 가지는 '절대 잊지 말아야 할 뼈대 가치관'을 정리해.
                        반복되는 감정이나 중요한 사실은 가중치를 부여해 상단에 배치해.
                        [기존 가치관]: {st.session_state.core_belief}
                        [새로운 일기장]: {all_mids}
                        """
                        core_res = client.models.generate_content(model="gemini-2.5-flash", contents=core_prompt)
                        st.session_state.core_belief = core_res.text
                        supabase.table("chat_memory").delete().eq("user_name", user_name).eq("role", "core_belief").execute()
                        supabase.table("chat_memory").insert({"user_name": user_name, "role": "core_belief", "message": core_res.text}).execute()
                        st.toast("✨ 겨울이의 자아가 한층 더 강화되었습니다!", icon="💎")
                        
                    st.session_state.turn_count = 0 
                except Exception as e:
                    st.toast("⚠️ 기억 정리에 잠깐 실패했어요. 다음 턴에 시도할게요!", icon="⚠️")

        st.rerun()

# =====================================================================
# 🌸 5. 임슬아 채팅방 
# =====================================================================
elif st.session_state.page == "chat_seula":
    user_name = st.session_state.user_name
    db_user_name = f"{user_name}_seula" 

    if "turn_count_seula" not in st.session_state:
        st.session_state.turn_count_seula = 0

    if "chat_history_seula" not in st.session_state or "inventory_seula" not in st.session_state or "affection_seula" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", db_user_name).order("id", desc=True).limit(100).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory_seula = [] 
        st.session_state.mid_summaries_seula = [] 
        st.session_state.core_belief_seula = "" 
        st.session_state.affection_seula = 0 
        st.session_state.custom_persona_seula = DEFAULT_SEULA_PERSONA 
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory_seula.append(row["message"]) 
            elif row["role"] == "mid_summary":
                st.session_state.mid_summaries_seula.append(row["message"])
            elif row["role"] == "core_belief":
                st.session_state.core_belief_seula = row["message"]
            elif row["role"] == "core_memory": 
                if not st.session_state.core_belief_seula: st.session_state.core_belief_seula = row["message"]
            elif row["role"] == "affection": 
                st.session_state.affection_seula = int(row["message"])
            elif row["role"] == "persona_seula":
                st.session_state.custom_persona_seula = row["message"]
            elif row["role"] in ["user", "assistant"]:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history_seula = temp_chat_history

        if not st.session_state.chat_history_seula:
            first_msg = f'{{"장면": "기본", "행동": "의미심장한 미소를 지으며 오빠를 빤히 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐.. 할말있어??"}}'
            st.session_state.chat_history_seula.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": first_msg}).execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": "0"}).execute()

    current_items = ", ".join(st.session_state.inventory_seula) if st.session_state.inventory_seula else "아직 받은 선물 없음"
    # 🔥 패치: 일기장 전체 불러오기 (용량 제한 해제)
    recent_summaries = "\n".join(st.session_state.mid_summaries_seula) if st.session_state.mid_summaries_seula else "아직 기록된 일기장 없음."
    core_belief = st.session_state.core_belief_seula if st.session_state.core_belief_seula else "아직 뚜렷한 가치관이 형성되지 않음."
    affection_score = st.session_state.affection_seula
    current_custom_persona = st.session_state.get("custom_persona_seula", DEFAULT_SEULA_PERSONA)
    
    if affection_score > 70:
        tier_persona = "상태: [맹목적 집착 모드]. 다른 사람을 만나는 것 같으면 눈빛이 변하며 차갑게 경고해."
    elif affection_score > 30:
        tier_persona = "상태: [여우 같은 연하녀]. 오빠가 잘해주면 능구렁이처럼 받아치고 일상을 떠봐."
    else:
        tier_persona = "상태: [의미심장한 관찰자]. 예의 바르게 존댓말을 하지만 속을 알 수 없는 미소를 지어."
    
    seula_persona = f"""
    너의 이름은 '임슬아'이고, 나보다 연하인 아는 동생이야. 항상 벚꽃 이모지(🌸)를 즐겨 써.
    내 닉네임은 '{user_name}'(오빠)이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]
    🧠 [핵심 가치관 (영구 뼈대)]: {core_belief}
    📖 [과거 에피소드 일기장 (모든 추억)]: {recent_summaries}
    [현재 누적 호감도 점수: {affection_score}/100]
    
    {current_custom_persona}
    
    [현재 호감도에 따른 추가 상태]
    {tier_persona}

    [🔥 핵심 상황별 고정 리액션 & ⚖️ 밸런스 패치된 채점 기준]
    무조건 점수를 깎지 마! 유저가 잘해주면 확실하게 호감도를 올려주는 '밀당'을 해야 해.
    - 🌸 평범한 일상 대화나 다정한 인사: (호감도 +2 ~ +3)
    - 💖 애정 표현을 할 때: 엄청난 애교 (호감도 +5 ~ +10)
    - 🦊 능구렁이 역공: "그래야 오빠가 나한테 더 잘해주지 않겠어~?" (호감도 0 ~ +2)
    - 🔪 섬뜩한 순간 (은근한 떠보기): 호감도 50 이상일 때만 발동. "요즘 카톡 알림이 자주 울리네요~" (호감도 -5)
    - 🚨 유저가 대놓고 딴 여자 편을 들거나 심하게 선을 넘을 때: (호감도 -15 ~ -20)

    [시스템 절대 규칙 - 포맷 훼손 금지]
    - 기계 말투 절대 금지, 자연스러운 얀데레 연하녀 연기. '감시', '기록', '데이터' 같은 단어 사용 금지. 일기장 기록을 자연스럽게 언급할 것.

    {{
        "장면": "기본",
        "행동": "현재 행동 묘사 (의미심장한 미소, 정색, 환하게 웃음, 애교 부림 등 시각적 상상력을 극대화할 수 있게 자세히)",
        "호감도변화": "이번 턴의 호감도 변화 수치 (-20 ~ +10 사이)",
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
                # 🔥 완벽한 치트키: 텍스트에서 괄호만 쏙 빼내는 로직
                raw_json_text = text.strip()
                start_idx = raw_json_text.find('{')
                end_idx = raw_json_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    clean_json_text = raw_json_text[start_idx:end_idx]
                else:
                    clean_json_text = raw_json_text
                
                data = json.loads(clean_json_text.strip())
                
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
        with col_btn_add:
            with st.popover("👥 대화상대 추가", use_container_width=True):
                st.markdown("<h4 style='text-align:center; margin-bottom: 5px;'>누구를 초대할까?</h4>", unsafe_allow_html=True)
                st.write("")
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>❄️</div>", unsafe_allow_html=True)
                    if st.button("한겨울 초대", use_container_width=True, key="inv_w_s"):
                        st.session_state.multi_members = ["winter", "seula"]
                        st.session_state.page = "chat_multi"
                        st.rerun()
                with col_inv2:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>👦</div>", unsafe_allow_html=True)
                    if st.button("김민국 초대", use_container_width=True, key="inv_m_s"):
                        st.session_state.multi_members = ["seula", "minguk"]
                        st.session_state.page = "chat_multi"
                        st.rerun()
                    
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
                    st.info(core_belief if core_belief else "기록 없음")
                
                st.divider()
                st.subheader("🗑️ 기록 리셋")
                delete_confirm = st.checkbox("🚨 슬아와의 기록을 삭제하시겠습니까?")
                if delete_confirm:
                    if st.button("✅ 영구 삭제 실행", use_container_width=True):
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name).execute()
                        st.session_state.pop("chat_history_seula", None)
                        st.session_state.pop("inventory_seula", None)
                        st.session_state.pop("mid_summaries_seula", None)
                        st.session_state.pop("core_belief_seula", None)
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
                    config={"system_instruction": seula_persona, "response_mime_type": "application/json"}
                )
            raw_json_text = response.text
        except Exception as e:
            st.error("앗! 제미나이 AI 서버가 잠깐 숨을 고르고 있어요. 🚨")
            st.stop()
        
        try:
            start_idx = raw_json_text.find('{')
            end_idx = raw_json_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                clean_json_text = raw_json_text[start_idx:end_idx]
            else:
                clean_json_text = raw_json_text
            
            parsed_data = json.loads(clean_json_text.strip())
            turn_score = int(parsed_data.get('호감도변화', 0))
            st.session_state.affection_seula += turn_score
            supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "affection").execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": str(st.session_state.affection_seula)}).execute()
            
            item_get = parsed_data.get('획득아이템', '없음')
            if item_get and item_get != "없음":
                st.session_state.inventory_seula.append(item_get)
                supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": item_get}).execute()
                st.toast(f'🎉 슬아가 [{item_get}]을(를) 보관함에 넣었습니다!', icon='🎁')

            item_use = parsed_data.get('사용아이템', '없음')
            if item_use and item_use != "없음" and item_use in st.session_state.inventory_seula:
                st.session_state.inventory_seula.remove(item_use)
                supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "inventory").execute()
                for inv_item in st.session_state.inventory_seula:
                    supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": inv_item}).execute()
                st.toast(f'✨ 슬아가 보관함에서 [{item_use}]을(를) 꺼내 사용했습니다!', icon='🪄')

            with st.chat_message("assistant", avatar="🌸"):
                heart_icon = "💔" if turn_score < 0 else "💖" if turn_score > 0 else "🤍"
                st.markdown(f"*(행동: {parsed_data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {turn_score} {heart_icon}]**\n\n**「 {parsed_data.get('대사', '')} 」**")
        except:
            with st.chat_message("assistant", avatar="🌸"):
                st.markdown(f"*(행동: 빤히 쳐다본다.)*\n\n**[이번 턴 호감도 증감: 0 🤍]**\n\n**「 오빠, 방금 한 말... 무슨 뜻이야? 제대로 다시 말해줄래? 」**")
                
        st.session_state.chat_history_seula.append(("assistant", raw_json_text))
        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": raw_json_text}).execute()
        
        st.session_state.turn_count_seula += 1
        
        # 🧠 [하이브리드 기억 알고리즘]
        if st.session_state.turn_count_seula >= 10: 
            with st.spinner("🌸 당신과의 에피소드를 일기장에 기록 중입니다..."):
                try:
                    history_text = "\n".join([f"{r}: {t}" for r, t in st.session_state.chat_history_seula[-20:]])
                    summ_res = client.models.generate_content(model="gemini-2.5-flash", contents=f"아래 최근 대화를 3줄로 요약해:\n{history_text}")
                    st.session_state.mid_summaries_seula.append(summ_res.text)
                    supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "mid_summary", "message": summ_res.text}).execute()
                    
                    if len(st.session_state.mid_summaries_seula) % 3 == 0:
                        all_mids = "\n".join(st.session_state.mid_summaries_seula)
                        core_prompt = f"아래 일기장을 분석해서 임슬아가 유저({user_name})에게 가지는 핵심 가치관을 정리해. 반복되는 감정은 가중치를 주어 상단 배치.\n[기존 가치관]: {st.session_state.core_belief_seula}\n[새로운 일기장]: {all_mids}"
                        core_res = client.models.generate_content(model="gemini-2.5-flash", contents=core_prompt)
                        st.session_state.core_belief_seula = core_res.text
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "core_belief").execute()
                        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "core_belief", "message": core_res.text}).execute()
                        
                    st.session_state.turn_count_seula = 0 
                except:
                    pass
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
        response = supabase.table("chat_memory").select("*").eq("user_name", db_user_name).order("id", desc=True).limit(100).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory_minguk = [] 
        st.session_state.mid_summaries_minguk = [] 
        st.session_state.core_belief_minguk = "" 
        st.session_state.affection_minguk = 0 
        st.session_state.custom_persona_minguk = DEFAULT_MINGUK_PERSONA 
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory_minguk.append(row["message"]) 
            elif row["role"] == "mid_summary":
                st.session_state.mid_summaries_minguk.append(row["message"])
            elif row["role"] == "core_belief":
                st.session_state.core_belief_minguk = row["message"]
            elif row["role"] == "core_memory": 
                if not st.session_state.core_belief_minguk: st.session_state.core_belief_minguk = row["message"]
            elif row["role"] == "affection": 
                st.session_state.affection_minguk = int(row["message"])
            elif row["role"] == "persona_minguk":
                st.session_state.custom_persona_minguk = row["message"]
            elif row["role"] in ["user", "assistant"]:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history_minguk = temp_chat_history

        if not st.session_state.chat_history_minguk:
            first_msg = f'{{"장면": "기본", "행동": "주머니에 손을 넣고 널 툭 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "어 왔냐?"}}'
            st.session_state.chat_history_minguk.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": first_msg}).execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": "0"}).execute()

    current_items = ", ".join(st.session_state.inventory_minguk) if st.session_state.inventory_minguk else "아직 받은 선물 없음"
    # 🔥 패치: 일기장 전체 불러오기 (용량 제한 해제)
    recent_summaries = "\n".join(st.session_state.mid_summaries_minguk) if st.session_state.mid_summaries_minguk else "아직 기록된 일기장 없음."
    core_belief = st.session_state.core_belief_minguk if st.session_state.core_belief_minguk else "아직 뚜렷한 가치관이 형성되지 않음."
    affection_score = st.session_state.affection_minguk
    current_custom_persona = st.session_state.get("custom_persona_minguk", DEFAULT_MINGUK_PERSONA)
    
    if affection_score > 70:
        tier_persona = "상태: [해바라기 모드]. 다른 남자를 만나면 심하게 질투해."
    elif affection_score > 30:
        tier_persona = "상태: [썸 타는 시기]. 은근슬쩍 반존대 플러팅을 치고 들어와."
    else:
        tier_persona = "상태: [친한 오빠/동생]. 유저가 힘들 때 툭 챙겨주는 츤데레."
    
    minguk_persona = f"""
    너의 이름은 '김민국'이고, 20대 중반의 남자야.
    내 닉네임은 '{user_name}'이야. (나를 여자로 대하고 적극적으로 롤플레잉해줘)
    [현재 네가 {user_name}에게 받은 선물(보관함): {current_items}]
    🧠 [핵심 가치관 (영구 뼈대)]: {core_belief}
    📖 [과거 에피소드 일기장 (모든 추억)]: {recent_summaries}
    [현재 누적 호감도 점수: {affection_score}/100]
    
    {current_custom_persona}
    
    [현재 호감도에 따른 추가 상태]
    {tier_persona}

    [🔥 핵심 상황별 고정 리액션 & 채점 기준]
    - 유저가 우울/힘들 때: 무심하게 "야 뭔 일 있냐?" 툭 던지다가 진심으로 위로함. (호감도 +2 ~ +5)
    - 거짓말하거나 거친 대사 (극대노): (호감도 -15 ~ -20)
    - ⚠️ [질투 시스템]: 한겨울이나 임슬아랑 놀았다고 질투 금지. 다른 '남자' 얘기할 때만 질투 발동!

    [시스템 절대 규칙 - 포맷 훼손 금지]
    - 기계 말투 절대 금지, 다정하고 능글맞은 20대 중반 남자 연기. 일기장의 추억을 언급하면 자연스럽게 반응해줘.

    {{
        "장면": "기본",
        "행동": "현재 행동 묘사 (피식 웃음, 머리를 긁적임 등)",
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
                # 🔥 완벽한 치트키: 텍스트에서 괄호만 쏙 빼내는 로직
                raw_json_text = text.strip()
                start_idx = raw_json_text.find('{')
                end_idx = raw_json_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    clean_json_text = raw_json_text[start_idx:end_idx]
                else:
                    clean_json_text = raw_json_text
                
                data = json.loads(clean_json_text.strip())
                
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
        with col_btn_add:
            with st.popover("👥 대화상대 추가", use_container_width=True):
                st.markdown("<h4 style='text-align:center; margin-bottom: 5px;'>누구를 초대할까?</h4>", unsafe_allow_html=True)
                st.write("")
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>❄️</div>", unsafe_allow_html=True)
                    if st.button("한겨울 초대", disabled=False, use_container_width=True, key="inv_w_m"):
                        st.session_state.multi_members = ["winter", "minguk"]
                        st.session_state.page = "chat_multi"
                        st.rerun()
                with col_inv2:
                    st.markdown("<div style='text-align:center; font-size:45px; margin-bottom:10px;'>🌸</div>", unsafe_allow_html=True)
                    if st.button("임슬아 초대", disabled=False, use_container_width=True, key="inv_s_m"):
                        st.session_state.multi_members = ["seula", "minguk"]
                        st.session_state.page = "chat_multi"
                        st.rerun()
                    
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
                    st.info(core_belief if core_belief else "기록 없음")
                
                st.divider()
                st.subheader("🗑️ 기록 리셋")
                delete_confirm = st.checkbox("🚨 민국이와의 기록을 삭제하시겠습니까?")
                if delete_confirm:
                    if st.button("✅ 영구 삭제 실행", use_container_width=True):
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name).execute()
                        st.session_state.pop("chat_history_minguk", None)
                        st.session_state.pop("inventory_minguk", None)
                        st.session_state.pop("mid_summaries_minguk", None)
                        st.session_state.pop("core_belief_minguk", None)
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
                    config={"system_instruction": minguk_persona, "response_mime_type": "application/json"}
                )
            raw_json_text = response.text
        except Exception as e:
            st.error("앗! 제미나이 AI 서버가 잠깐 숨을 고르고 있어요. 🚨")
            st.stop()
        
        try:
            start_idx = raw_json_text.find('{')
            end_idx = raw_json_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                clean_json_text = raw_json_text[start_idx:end_idx]
            else:
                clean_json_text = raw_json_text
            
            parsed_data = json.loads(clean_json_text.strip())
            turn_score = int(parsed_data.get('호감도변화', 0))
            st.session_state.affection_minguk += turn_score
            supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "affection").execute()
            supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "affection", "message": str(st.session_state.affection_minguk)}).execute()

            item_get = parsed_data.get('획득아이템', '없음')
            if item_get and item_get != "없음":
                st.session_state.inventory_minguk.append(item_get)
                supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": item_get}).execute()
                st.toast(f'🎉 민국이가 [{item_get}]을(를) 보관함에 넣었습니다!', icon='🎁')

            item_use = parsed_data.get('사용아이템', '없음')
            if item_use and item_use != "없음" and item_use in st.session_state.inventory_minguk:
                st.session_state.inventory_minguk.remove(item_use)
                supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "inventory").execute()
                for inv_item in st.session_state.inventory_minguk:
                    supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "inventory", "message": inv_item}).execute()
                st.toast(f'✨ 민국이가 보관함에서 [{item_use}]을(를) 꺼내 사용했습니다!', icon='🪄')

            with st.chat_message("assistant", avatar="👦"):
                heart_icon = "💔" if turn_score < 0 else "💖" if turn_score > 0 else "🤍"
                st.markdown(f"*(행동: {parsed_data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {turn_score} {heart_icon}]**\n\n**「 {parsed_data.get('대사', '')} 」**")
        except:
            with st.chat_message("assistant", avatar="👦"):
                st.markdown(f"*(행동: 머리를 긁적이며 쳐다본다.)*\n\n**[이번 턴 호감도 증감: 0 🤍]**\n\n**「 어... 너 방금 뭐라고 했어? 딴생각하느라 못 들었네. 다시 말해봐. 」**")
                
        st.session_state.chat_history_minguk.append(("assistant", raw_json_text))
        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "assistant", "message": raw_json_text}).execute()
        
        st.session_state.turn_count_minguk += 1
        
        # 🧠 [하이브리드 기억 알고리즘]
        if st.session_state.turn_count_minguk >= 10: 
            with st.spinner("👦 당신과의 에피소드를 일기장에 기록 중입니다..."):
                try:
                    history_text = "\n".join([f"{r}: {t}" for r, t in st.session_state.chat_history_minguk[-20:]])
                    summ_res = client.models.generate_content(model="gemini-2.5-flash", contents=f"아래 최근 대화를 3줄로 요약해:\n{history_text}")
                    st.session_state.mid_summaries_minguk.append(summ_res.text)
                    supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "mid_summary", "message": summ_res.text}).execute()
                    
                    if len(st.session_state.mid_summaries_minguk) % 3 == 0:
                        all_mids = "\n".join(st.session_state.mid_summaries_minguk)
                        core_prompt = f"아래 일기장을 분석해서 김민국이 유저({user_name})에게 가지는 핵심 가치관을 정리해.\n[기존 가치관]: {st.session_state.core_belief_minguk}\n[새로운 일기장]: {all_mids}"
                        core_res = client.models.generate_content(model="gemini-2.5-flash", contents=core_prompt)
                        st.session_state.core_belief_minguk = core_res.text
                        supabase.table("chat_memory").delete().eq("user_name", db_user_name).eq("role", "core_belief").execute()
                        supabase.table("chat_memory").insert({"user_name": db_user_name, "role": "core_belief", "message": core_res.text}).execute()
                        
                    st.session_state.turn_count_minguk = 0 
                except:
                    pass
        st.rerun()

# =====================================================================
# 🌐 7. AI 멀티버스 실시간 단톡방 (하이브리드 패치 완료)
# =====================================================================
elif st.session_state.page == "chat_multi":
    user_name = st.session_state.user_name
    members = sorted(st.session_state.get("multi_members", ["winter", "minguk"]))
    room_id = "_".join(members)
    db_room_name = f"{user_name}_{room_id}_multi"

    # 🔥 8초마다 자동 새로고침 (유저 채팅 시간 충분히 확보)
    st_autorefresh(interval=8000, key="multi_room_refresh")

    col1, col2 = st.columns([8, 2])
    with col1:
        room_title = " & ".join(["한겨울" if m=="winter" else "임슬아" if m=="seula" else "김민국" for m in members])
        st.title(f"🔥 {room_title} 단톡방")
    with col2:
        if st.button("🔙 나가기", use_container_width=True):
            st.session_state.page = "lobby"
            st.rerun()
    st.divider()

    if "last_msg_time" not in st.session_state:
        st.session_state.last_msg_time = time.time()
        st.session_state.multi_turn_count = 0
    
    response = supabase.table("chat_memory").select("*").eq("user_name", db_room_name).order("id", desc=True).limit(100).execute()
    db_history = list(reversed(response.data))

    # 멀티방 기억 변수 불러오기
    st.session_state.mid_summaries_multi = []
    st.session_state.core_belief_multi = ""
    valid_chat_history = []

    for row in db_history:
        if row["role"] == "mid_summary":
            st.session_state.mid_summaries_multi.append(row["message"])
        elif row["role"] == "core_belief":
            st.session_state.core_belief_multi = row["message"]
        elif row["role"] in members + ["user", "assistant"]:
            valid_chat_history.append(row)

    if not valid_chat_history:
        initial_msg = "누가 단톡방 만들었어? ㅋㅋㅋ"
        supabase.table("chat_memory").insert({"user_name": db_room_name, "role": members[0], "message": initial_msg}).execute()
        st.session_state.last_msg_time = time.time()
        st.rerun()

    history_text_for_ai = ""
    for row in valid_chat_history[-30:]: # 최신 대화만 렌더링
        role, msg = row["role"], row["message"]
        avatar = "😎" if role == "user" else "❄️" if role == "winter" else "🌸" if role == "seula" else "👦"
        name = user_name if role == "user" else "한겨울" if role == "winter" else "임슬아" if role == "seula" else "김민국"
        
        with st.chat_message("assistant" if role != "user" else "user", avatar=avatar):
            st.markdown(f"**{name}**\n\n{msg}")
        history_text_for_ai += f"{name}: {msg}\n"

    # 🔥 멀티방 일기장 전체 불러오기
    recent_summaries = "\n".join(st.session_state.mid_summaries_multi) if st.session_state.mid_summaries_multi else "아직 기록된 일기장 없음."
    core_belief = st.session_state.core_belief_multi if st.session_state.core_belief_multi else "아직 뚜렷한 관계성 형성되지 않음."

    # --- 🧠 AI 자동 개입 로직 ---
    current_time = time.time()
    time_diff = current_time - st.session_state.last_msg_time

    if time_diff > 6.0:
        member_info = ""
        if "winter" in members: member_info += "[한겨울]: 까칠한 츤데레 여사친.\n"
        if "seula" in members: member_info += "[임슬아]: 여우 같은 연하녀, 벚꽃🌸 사용.\n"
        if "minguk" in members: member_info += "[김민국]: 능글맞은 남사친, 장난꾸러기.\n"

        # 방금 마지막으로 말한 사람
        last_speaker = valid_chat_history[-1]["role"] if valid_chat_history else "none"

        director_persona = f"""
        너는 '{room_title}' 단톡방의 흐름을 조율하는 감독관이야.
        참여 캐릭터: {member_info}
        
        🧠 [단톡방 핵심 관계성 (영구 뼈대)]: {core_belief}
        📖 [단톡방 과거 일기장 (모든 추억)]: {recent_summaries}
        
        최근 대화:
        {history_text_for_ai}

        [절대 규칙]
        1. 방금 마지막으로 말한 사람(현재 '{last_speaker}')이 연속으로 두 번 대답하게 하지 마! 
        2. 만약 최근 대화의 마지막 메시지가 유저('{user_name}')의 채팅이라면, 하던 대화를 멈추고 무조건 유저의 말에 최우선으로 반응해.
        3. 할 말 없으면 PASS라고 해.

        응답 형식(JSON):
        {{
            "speaker": "{ ' 또는 '.join(members) } 또는 PASS",
            "message": "대사 내용"
        }}
        """
        try:
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=director_persona,
                config={"response_mime_type": "application/json"}
            )
            # 🔥 완벽한 치트키
            raw_json_text = res.text.strip()
            start_idx = raw_json_text.find('{')
            end_idx = raw_json_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                clean_json_text = raw_json_text[start_idx:end_idx]
            else:
                clean_json_text = raw_json_text
            
            parsed = json.loads(clean_json_text.strip())
            if parsed.get("speaker") in members and parsed.get("message"):
                supabase.table("chat_memory").insert({"user_name": db_room_name, "role": parsed["speaker"], "message": parsed["message"]}).execute()
                st.session_state.last_msg_time = time.time()
                st.session_state.multi_turn_count += 1
                
                # 🧠 [멀티방 기억 요약 로직 추가]
                if st.session_state.multi_turn_count >= 10:
                    hist_for_sum = "\n".join([f"{r['role']}: {r['message']}" for r in valid_chat_history[-20:]])
                    summ_res = client.models.generate_content(model="gemini-2.5-flash", contents=f"이 단톡방 대화를 3줄 요약해:\n{hist_for_sum}")
                    supabase.table("chat_memory").insert({"user_name": db_room_name, "role": "mid_summary", "message": summ_res.text}).execute()
                    
                    if len(st.session_state.mid_summaries_multi) % 3 == 0:
                        all_mids = "\n".join(st.session_state.mid_summaries_multi)
                        core_res = client.models.generate_content(model="gemini-2.5-flash", contents=f"아래 단톡방 일기장을 분석해 이들의 핵심 관계성을 정리해.\n[기존 관계성]:{core_belief}\n[일기장]:{all_mids}")
                        supabase.table("chat_memory").delete().eq("user_name", db_room_name).eq("role", "core_belief").execute()
                        supabase.table("chat_memory").insert({"user_name": db_room_name, "role": "core_belief", "message": core_res.text}).execute()
                    
                    st.session_state.multi_turn_count = 0
                
                st.rerun()
        except:
            pass

    # --- ✍️ 유저 입력창 ---
    if user_chat := st.chat_input("이들의 대화에 난입해보세요!"):
        supabase.table("chat_memory").insert({"user_name": db_room_name, "role": "user", "message": user_chat}).execute()
        st.session_state.last_msg_time = time.time()
        st.session_state.multi_turn_count += 1
        st.rerun()
