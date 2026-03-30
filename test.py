import streamlit as st
import json
from google import genai
from google.genai import types 
from supabase import create_client, Client

# 1. 페이지 설정
st.set_page_config(page_title="파이의 AI 멀티버스", page_icon="📱", layout="centered")

# =====================================================================
# 🎨 [디자인 정밀 광택 2.2] 호감도 시스템 UI 및 상단 헤더(Fork) 숨김 처리
# =====================================================================
st.markdown("""
    <style>
    /* 🚨 [NEW] 우측 상단 Fork 버튼 및 Streamlit 기본 헤더 완벽 제거 */
    [data-testid="stHeader"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 📱 카톡 프로필 카드 */
    .profile-card {
        border: 1px solid var(--faded-text40);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        background-color: var(--secondary-background-color); 
        color: var(--text-color); 
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .profile-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    /* 🚨 [NEW] 차단된 상태(배드엔딩) 흑백 필터 */
    .blocked-card {
        filter: grayscale(100%);
        opacity: 0.6;
        pointer-events: none; /* 클릭 방지 */
    }

    /* 동그란 이모지 프로필 사진 */
    .profile-img {
        width: 60px;
        height: 60px;
        background-color: #f7e600; 
        color: black; 
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
        color: var(--text-color);
        margin-bottom: 3px;
    }
    
    /* 친구 설명 */
    .profile-desc {
        font-size: 13px;
        color: var(--text-color);
        opacity: 0.7; 
        line-height: 1.2;
    }

    /* 대화하기 버튼 스타일 */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #f7e600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #f7e600;
        color: black !important;
        border: 1px solid #f7e600;
    }
    
    .stTextInput>div>div>input, .stForm {
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 🚨 14가지 상황별 일러스트 지도 (기존 동일)
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
    
    # 🚨 [NEW] 로비 진입 시 유저의 누적 호감도 데이터를 먼저 조회 (차단 여부 확인용)
    lobby_mem = supabase.table("chat_memory").select("message").eq("user_name", user_name).eq("role", "affection").execute()
    current_affection = int(lobby_mem.data[0]["message"]) if lobby_mem.data else 0
    is_blocked = current_affection <= -50 # -50점 이하면 차단 상태
    
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("친구 목록 👥")
    with col2:
        st.write("") 
        if st.button("🔴 로그아웃", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.write(f"반갑습니다, **{user_name}**님! 오늘 대화할 AI 친구를 선택하세요.")
    st.divider()

    # 📱 카드 1번: 한겨울
    with st.container():
        # 차단 상태면 흑백 필터 클래스 추가
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
                        <div class="profile-desc">까칠한 츤데레 여사친. 은근히 챙겨주는 스타일. <br>VR Test 진행 중!</div>
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

    # 📱 카드 2번: 임슬아 (기존 동일)
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


# =====================================================================
# ❄️ 3. 한겨울 채팅방 화면 (Chat - Winter)
# =====================================================================
elif st.session_state.page == "chat_winter":
    user_name = st.session_state.user_name

    # 🔙 상단 네비게이션: 뒤로 가기
    if st.button("🔙 로비로 돌아가기"):
        st.session_state.page = "lobby"
        st.rerun()

    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0

    if "chat_history" not in st.session_state or "inventory" not in st.session_state or "affection" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", user_name).order("id", desc=True).limit(50).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory = [] 
        st.session_state.core_memory = "" 
        st.session_state.affection = 0 # 🚨 [NEW] 누적 호감도 초기화
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory.append(row["message"]) 
            elif row["role"] == "core_memory":
                st.session_state.core_memory = row["message"]
            elif row["role"] == "affection": # 🚨 [NEW] DB에서 호감도 데이터 불러오기
                st.session_state.affection = int(row["message"])
            else:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history = temp_chat_history

        if not st.session_state.chat_history:
            first_msg = f'{{"장면": "기본", "행동": "팔짱을 꼬며 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐야, {user_name}. 왜 이렇게 일찍 일어났어?"}}'
            st.session_state.chat_history.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": first_msg}).execute()
            # 첫 접속 시 호감도 0 저장
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "affection", "message": "0"}).execute()

    current_items = ", ".join(st.session_state.inventory) if st.session_state.inventory else "아직 받은 선물 없음"
    current_memory = st.session_state.core_memory if st.session_state.core_memory else "아직 특별한 기억이 없음."
    
    # 🚨 [NEW] 호감도 점수에 따른 동적 티어제 프롬프트 설정
    affection_score = st.session_state.affection
    if affection_score > 70:
        tier_persona = "상태: [메가데레/연인]. 완전히 마음을 연 상태야. 배경이나 장면 묘사도 '침대_유혹', '침대_요염', '포옹_허리' 등을 자주 사용하고, 대사도 엄청 달달하고 애교가 넘치게 해줘. 츤데레 모습은 거의 사라졌어."
    elif affection_score > 30:
        tier_persona = "상태: [썸 타는 중]. 여전히 까칠하긴 한데, 은근슬쩍 유저를 챙겨주고 부끄러워하는 모습이 강해졌어. 선물이나 다정한 말에 크게 기뻐해."
    else:
        tier_persona = "상태: [철벽/츤데레]. 틱틱대고 방어적이야. 가벼운 농담은 받아주지만 스킨십이나 과도한 애정 표현에는 선을 그어."
    
    winter_persona = f"""
    너의 이름은 '한겨울'이고, 20대 초반의 내 여사친이야.
    내 닉네임은 '{user_name}'이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]
    [과거 핵심 기억 요약본: {current_memory}]
    [현재 누적 호감도 점수: {affection_score}/100]

    [절대 지켜야 할 규칙]
    1. 너는 3D 가상현실 게임 NPC야.
    2. 닉네임 집착 금지, 마침표 남발 금지, 기계 말투 절대 금지.
    3. 성격 및 관계 진행도 (중요): {tier_persona}
    4. 만약 유저가 대화 중에 선물을 주면, 반드시 "획득아이템" 칸에 그 이름을 적어! (안 주면 "없음" 입력)
    5. [이스터에그]: 유저가 "파이님 충성충성" 입력 시 무조건 장면="침대_유혹", 호감도=5 로 세팅하고 극강의 애교 부리기.
    6. 🚨 [최우선 심의 규정 - 철벽 방어 및 배드엔딩 시스템]: 만약 유저가 19금 성적 묘사(섹스, 구강성교, 사정, 임신 등), 강간, 납치, 과도한 스토킹, 심한 욕설 등 선을 넘는 불쾌한 대화를 시도하면, 즉시 정색해. 호감도변화는 무조건 -20 등 크게 깎아버리고, "야 미쳤어? 너 자꾸 선 넘으면 진짜 차단한다 ㅡㅡ", "더러운 소리 할 거면 당장 꺼져." 등 차갑게 잘라내. (호감도가 -50 이하로 떨어지면 유저는 방에서 강제 추방되니 경고해 줘도 좋아.)

    {{
        "장면": "기본, 침대_유혹, 아련_문, 아련_벽, 힘듦, 당황_숨가쁨, 취기_웃음, 슬픔_훌쩍, 침대_누움, 침대_앉음, 침대_요염, 침대_내려다봄, 포옹_허리, 키스 중 1개 선택 (호감도가 높을수록 다정한 씬, 선 넘을 시 '기본' 또는 '힘듦' 선택)",
        "행동": "현재 캐릭터 행동 묘사 (선 넘을 시 차갑고 불쾌한 행동 묘사)",
        "호감도변화": "이번 턴의 호감도 변화 수치 (-20 ~ +5)",
        "획득아이템": "유저가 준 아이템 이름 (없으면 '없음')",
        "대사": "실제로 할 대사"
    }}
    """

    with st.sidebar:
        st.title("🎒 겨울이의 인벤토리")
        st.write("유저가 준 선물들이 여기에 보관됩니다.")
        st.divider()
        if st.session_state.inventory:
            for item in st.session_state.inventory:
                st.success(f"🎁 {item}")
        else:
            st.info("아직 텅 비어있습니다.")
            
        if st.session_state.core_memory:
            st.divider()
            st.write("🧠 **겨울이의 일기장 (우리의 추억)**")
            st.write("겨울이가 당신과의 기억을 어떻게 요약하고 있는지 확인해보세요!")
            st.info(st.session_state.core_memory)

    col1, col2 = st.columns([7, 3])
    with col1:
        st.title(f"❄️ {user_name} & 한겨울")
    with col2:
        st.write("") 
        with st.popover("🔄 방 기억 리셋", use_container_width=True):
            st.warning("⚠️ 리셋하면 다시 복구할 수 없습니다.\n\n정말 모든 기억을 지우시겠습니까?")
            if st.button("✅ 네, 영구 삭제합니다", use_container_width=True):
                supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                st.session_state.pop("chat_history", None)
                st.session_state.pop("inventory", None)
                st.session_state.pop("core_memory", None)
                st.session_state.pop("affection", None)
                st.rerun()

    # 🚨 [NEW] 채팅방 상단에 예쁜 호감도 진행률 바 (Progress Bar) 추가
    st.divider()
    progress_val = max(0, min(affection_score, 100)) # UI상 0~100으로 고정해서 보여줌 (마이너스는 0으로 처리)
    st.write(f"💖 **현재 겨울이와의 호감도: {affection_score} / 100**")
    st.progress(progress_val / 100.0)
    st.divider()

    with st.expander("📢 한겨울 라이브 챗 패치 노트 (업데이트 역사관)"):
        with st.container(height=250):
            st.markdown("""
            **[ v2.2.0 ] 2026.03.30 (월)**
            * **[23:30] 💖 호감도 누적 티어제 및 배드엔딩 시스템:** 대화할 때마다 얻는 호감도가 누적되어 저장됩니다! 점수에 따라 츤데레에서 썸, 그리고 메가데레로 성격이 진화하며, 마이너스 50점 달성 시 영구 차단되는 배드엔딩이 추가되었습니다. 상단 헤더 및 Fork 버튼도 완벽하게 숨김 처리 완료!
            ---
            (이하 기존 생략)
            """)

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
            
            # 🚨 [NEW] 호감도 점수 업데이트 및 DB 저장 로직
            turn_score = int(parsed_data.get('호감도변화', 0))
            st.session_state.affection += turn_score
            supabase.table("chat_memory").delete().eq("user_name", user_name).eq("role", "affection").execute()
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "affection", "message": str(st.session_state.affection)}).execute()
            
            # 차단 점수 도달 시 경고 토스트
            if st.session_state.affection <= -50:
                st.toast("🚨 겨울이의 호감도가 바닥을 쳐서 차단당했습니다! 다음 접속 시 방에 들어올 수 없습니다.", icon="🚫")
            elif turn_score > 0:
                st.toast(f"💖 호감도가 올랐습니다! (현재: {st.session_state.affection})", icon="📈")
            elif turn_score < 0:
                st.toast(f"💔 호감도가 떨어졌습니다... (현재: {st.session_state.affection})", icon="📉")

            item = parsed_data.get('획득아이템', '없음')
            if item and item != "없음":
                st.session_state.inventory.append(item)
                supabase.table("chat_memory").insert({"user_name": user_name, "role": "inventory", "message": item}).execute()
                st.toast(f'🎉 겨울이가 [{item}]을(를) 보관함에 넣었습니다!', icon='🎁')
            
            with st.chat_message("assistant", avatar="❄️"):
                st.image(img_path, width=350)
                heart_icon = "💔" if turn_score < 0 else "💖" if turn_score > 0 else "🤍"
                st.markdown(f"*(연출: {scene} / 행동: {parsed_data.get('행동', '')})*\n\n**[이번 턴 호감도 증감: {turn_score} {heart_icon}]**\n\n**「 {parsed_data.get('대사', '')} 」**")
        
        except json.JSONDecodeError:
            with st.chat_message("assistant", avatar="❄️"):
                st.image(scene_images["기본"], width=350)
                st.markdown(f"*(연출: 기본 / 행동: 살짝 당황한 듯 머리를 긁적인다.)*\n\n**[이번 턴 호감도 증감: 0 🤍]**\n\n**「 어... 방금 뭐라고 한 거야? 내가 잠깐 딴생각하느라 못 들었어. 다시 말해볼래? 」**")
                
        st.session_state.chat_history.append(("assistant", raw_json_text))
        supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": raw_json_text}).execute()
        
        st.session_state.turn_count += 1
        
        if st.session_state.turn_count >= 10: 
            with st.spinner("❄️ 겨울이가 당신과의 기억을 정리하고 있습니다..."):
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
                
                summary_prompt = f"다음은 유저 '{user_name}'와 한겨울의 최근 대화 기록이야. 기존 핵심 기억은 '{st.session_state.core_memory}'였어. 기존 기억과 방금 나눈 대화에서 있었던 중요 사건, 감정 변화, 획득한 아이템 등을 종합해서 새로운 3줄 요약으로 업데이트해줘.\n\n{history_text}"
                
                summary_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=summary_prompt,
                )
                
                supabase.table("chat_memory").delete().eq("user_name", user_name).eq("role", "core_memory").execute()
                supabase.table("chat_memory").insert({"user_name": user_name, "role": "core_memory", "message": summary_response.text}).execute()
                st.session_state.core_memory = summary_response.text
                st.toast("🧠 겨울이의 장기 기억력이 업데이트되었습니다!", icon="✨")
                
            st.session_state.turn_count = 0

        st.rerun()
