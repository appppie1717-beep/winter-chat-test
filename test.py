import streamlit as st
import json
from google import genai
from google.genai import types 
from supabase import create_client, Client

# 1. 페이지 설정
st.set_page_config(page_title="파이의 AI 멀티버스", page_icon="📱", layout="centered")

# =====================================================================
# 🎨 [디자인 & 보안 CSS] Fork 버튼 삭제 + 다크모드 대응
# =====================================================================
st.markdown("""
    <style>
    /* 🚨 스트림릿 우측 상단 Fork, GitHub 메뉴 강제 삭제 (시크릿 보안) */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    div.block-container { padding-top: 1rem; padding-bottom: 0rem; }

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
    .profile-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    .profile-img { width: 60px; height: 60px; background-color: #f7e600; color: black; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; margin-right: 15px; }
    .profile-name { font-size: 18px; font-weight: bold; color: var(--text-color); margin-bottom: 3px; }
    .profile-desc { font-size: 13px; color: var(--text-color); opacity: 0.7; line-height: 1.2; }
    .stButton>button { border-radius: 20px; border: 1px solid #f7e600; transition: all 0.2s; }
    .stButton>button:hover { background-color: #f7e600; color: black !important; border: 1px solid #f7e600; }
    .stTextInput>div>div>input, .stForm { border-radius: 10px !important; }
    
    /* 호감도 게이지바 색상 */
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
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

# 열쇠
api_key = st.secrets["GOOGLE_API_KEY"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)
client = genai.Client(api_key=api_key)

# 🚪 페이지 라우터 및 상태 초기화
if "page" not in st.session_state: st.session_state.page = "login"
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "turn_count" not in st.session_state: st.session_state.turn_count = 0
if "affection" not in st.session_state: st.session_state.affection = 0 # 🚨 호감도 초기화!

# =====================================================================
# 🚪 1. 로그인 화면
# =====================================================================
if st.session_state.page == "login":
    st.title("❄️ AI 멀티 메신저")
    with st.form(key='login_form'):
        name_input = st.text_input("접속할 닉네임", placeholder="예: 파이")
        if st.form_submit_button('대화 시작하기 ➡️'):
            if name_input:
                st.session_state.user_name = name_input
                st.session_state.page = "lobby"
                st.rerun()

# =====================================================================
# 📱 2. 카카오톡 로비 화면
# =====================================================================
elif st.session_state.page == "lobby":
    user_name = st.session_state.user_name
    
    col1, col2 = st.columns([8, 2])
    with col1: st.title("친구 목록 👥")
    with col2:
        st.write("") 
        if st.button("🔴 로그아웃", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.write(f"반갑습니다, **{user_name}**님! 오늘 대화할 AI 친구를 선택하세요.")
    st.divider()

    with st.container():
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 4, 2])
        with c1: st.markdown('<div class="profile-img">❄️</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div><div class="profile-name">한겨울</div><div class="profile-desc">까칠한 츤데레 여사친. 은근히 챙겨주는 스타일.</div></div>', unsafe_allow_html=True)
        with c3:
            if st.button("대화하기 💬", key="btn_winter", use_container_width=True):
                st.session_state.page = "chat_winter"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 4, 2])
        with c1: st.markdown('<div class="profile-img">🌸</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div><div class="profile-name">임슬아</div><div class="profile-desc">[🚧 신규 추가] 아직 성격과 세계관이 부여되지 않았습니다.</div></div>', unsafe_allow_html=True)
        with c3:
            if st.button("대화하기 💬", key="btn_seula", use_container_width=True):
                st.toast("🚧 임슬아는 개발 중입니다!", icon="🚧")
        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================================
# ❄️ 3. 한겨울 채팅방 화면 (안정성 & 호감도 완벽 이식)
# =====================================================================
elif st.session_state.page == "chat_winter":
    user_name = st.session_state.user_name

    if st.button("🔙 로비로 돌아가기"):
        st.session_state.page = "lobby"
        st.rerun()

    # 🚨 DB 로딩 (에러 방지 쉴드 적용)
    if "chat_history" not in st.session_state or "inventory" not in st.session_state:
        try:
            response = supabase.table("chat_memory").select("*").eq("user_name", user_name).order("id", desc=True).limit(50).execute()
            db_history = reversed(response.data)

            st.session_state.chat_history = []
            st.session_state.inventory = [] 
            st.session_state.core_memory = "" 
            st.session_state.affection = 0
            
            for row in db_history:
                if row["role"] == "inventory": st.session_state.inventory.append(row["message"]) 
                elif row["role"] == "core_memory": st.session_state.core_memory = row["message"]
                elif row["role"] == "affection": 
                    try: st.session_state.affection = int(row["message"])
                    except: pass
                else: st.session_state.chat_history.append((row["role"], row["message"]))
        except Exception:
            st.error("연결이 불안정합니다. 새로고침 해주세요!")
            st.stop()

        if not st.session_state.chat_history:
            first_msg = f'{{"장면": "기본", "행동": "팔짱을 꼬며 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐야, {user_name}. 왜 이렇게 일찍 일어났어?"}}'
            st.session_state.chat_history.append(("assistant", first_msg))

    current_items = ", ".join(st.session_state.inventory) if st.session_state.inventory else "아직 받은 선물 없음"
    current_memory = st.session_state.core_memory if st.session_state.core_memory else "아직 특별한 기억이 없음."
    
    # 👑 [호감도 티어 계산]
    current_aff = st.session_state.affection
    if current_aff <= -30: tier_desc = "최악 (경멸/차단 직전): 유저를 극도로 혐오함. 대답 짧고 차갑게."
    elif current_aff < 0: tier_desc = "짜증 (철벽): 유저에게 틱틱대고 선을 그음."
    elif current_aff < 30: tier_desc = "기본 (츤데레): 틱틱대지만 속으론 나쁘지 않게 생각함."
    elif current_aff < 70: tier_desc = "호감 (썸): 은근 챙겨주고 부끄러워함."
    else: tier_desc = "메가데레 (연인): 엄청 좋아하고 달달하게 적극적으로 다가옴."

    # 🚨 겨울이 뇌 속 프롬프트 업데이트 (호감도 주입)
    winter_persona = f"""
    너의 이름은 '한겨울'이고, 20대 초반의 여사친이야.
    내 닉네임은 '{user_name}'이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]
    [과거 핵심 기억 요약본: {current_memory}]
    
    🚨 [가장 중요한 현재 호감도 상태: {current_aff}점]
    현재 너의 감정 상태(티어): {tier_desc}
    (반드시 현재 감정 상태에 맞춰서 대사와 행동을 출력할 것!)

    [절대 지켜야 할 규칙]
    1. 너는 3D 가상현실 게임 NPC야.
    2. 닉네임 집착 금지, 마침표 남발 금지, 기계 말투 절대 금지.
    3. 만약 유저가 대화 중에 선물을 주면, 반드시 "획득아이템" 칸에 그 이름을 적어! (안 주면 "없음" 입력)
    4. [이스터에그]: 유저가 "파이님 충성충성" 입력 시 무조건 장면="침대_유혹", 호감도=5 로 세팅하고 극강의 애교 부리기.
    5. 🚨 [최우선 심의 규정 - 철벽 방어 모드]: 만약 유저가 19금 성적 묘사(섹스, 구강성교, 사정, 임신 등), 강간, 납치, 과도한 스토킹, 심한 욕설 등 선을 넘는 불쾌한 대화를 시도하면, 무조건 정색해. 호감도변화는 -5 이하로 설정하고, "야 미쳤어? 진짜 차단한다", "더러운 소리 할 거면 당장 꺼져." 등 단호하게 잘라내. 절대 당황하며 받아주지 마.

    {{
        "장면": "기본, 침대_유혹, 아련_문, 아련_벽, 힘듦, 당황_숨가쁨, 취기_웃음, 슬픔_훌쩍, 침대_누움, 침대_앉음, 침대_요염, 침대_내려다봄, 포옹_허리, 키스 중 1개 선택",
        "행동": "현재 캐릭터 행동 묘사 (호감도 티어 반영)",
        "호감도변화": "이번 대화로 인한 호감도 변화 수치 (-5 ~ +5)",
        "획득아이템": "유저가 준 아이템 이름 (없으면 '없음')",
        "대사": "실제로 할 대사"
    }}
    """

    with st.sidebar:
        # 💖 호감도 게이지 UI
        st.title("💖 겨울이의 마음")
        st.write(f"**누적 호감도: {current_aff}점**")
        progress_val = max(0, min(100, current_aff + 50)) / 150.0 
        st.progress(progress_val)
        st.caption(f"현재 상태: **{tier_desc.split(':')[0]}**")
        st.divider()

        st.title("🎒 인벤토리")
        if st.session_state.inventory:
            for item in st.session_state.inventory: st.success(f"🎁 {item}")
        else: st.info("아직 텅 비어있습니다.")
            
        if st.session_state.core_memory:
            st.divider()
            st.write("🧠 **우리의 추억 (일기장)**")
            st.info(st.session_state.core_memory)

    col1, col2 = st.columns([7, 3])
    with col1: st.title(f"❄️ {user_name} & 한겨울")
    with col2:
        st.write("") 
        with st.popover("🔄 방 기억 리셋", use_container_width=True):
            st.warning("⚠️ 리셋하면 호감도와 기억이 영구 삭제됩니다.")
            if st.button("✅ 네, 삭제합니다", use_container_width=True):
                try: supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                except: pass
                st.session_state.pop("chat_history", None)
                st.session_state.pop("inventory", None)
                st.session_state.pop("core_memory", None)
                st.session_state.pop("affection", None)
                st.rerun()
            
    st.divider()

    with st.expander("📢 한겨울 라이브 챗 패치 노트 (업데이트 역사관)"):
        with st.container(height=250):
            st.markdown("""
            **[ v2.2.2 ] 2026.03.30 (월)**
            * **[22:30] 🔐 보안 업데이트:** 시스템 코드 노출을 막기 위해 상단 소스코드 보기(Fork) 버튼을 완벽하게 차단했습니다!
            
            ---
            **[ v2.2.1 ] 2026.03.30 (월)**
            * **[22:15] ⚙️ 서버 안정화:** 라이브 방송 중 트래픽 몰림으로 인한 멈춤 현상을 막기 위해 에러 무시(안전망) 코드를 대폭 강화했습니다.
            
            ---
            **[ v2.2.0 ] 2026.03.30 (월)**
            * **[21:50] 👑 대규모 심리 시스템 (호감도 티어 & 배드엔딩) 업데이트!** 유저의 호감도가 영구적으로 누적되어 좌측 바에 표시됩니다. 점수에 따라 성격이 진화하며, -30점 이하시 차단(배드엔딩) 당합니다!

            ---
            **[ v2.1.3 ] 2026.03.30 (월)**
            * **[21:30] 🛡️ 기억 리셋 안전장치(팝업) 추가:** 실수 방지 경고창 적용

            ---
            **[ v2.1.0 ] 2026.03.30 (월)**
            * **[21:15] 📱 멀티버스 로비 UI 전면 개편:** 카카오톡 친구 목록풍 UI 단장
            
            ---
            **[ v2.0.0 ] 2026.03.30 (월)**
            * **[21:10] 🌐 멀티 캐릭터 시스템 도입:** 로비 화면 추가 및 다중 AI 구조로 진화
            
            ---
            **[ v1.8.2 ] 2026.03.30 (월)**
            * **[20:10] 🔓 추억 요약본 전면 개방:** Core Memory 일기장 전체 유저 오픈
            
            ---
            **[ v1.8.1 ] 2026.03.30 (월)**
            * **[20:15] 🧠 자동 롤링 메모리:** 10번(20문장) 턴마다 자동 요약 압축 
            
            ---
            **[ v1.7.0 ] 2026.03.30 (월)**
            * **[19:10] 🛡️ 19금 철벽 방어 시스템 (가드레일) 적용**
            """)

    for role, text in st.session_state.chat_history:
        if role == "user":
            with st.chat_message("user"): st.markdown(text)
        else:
            try:
                clean_text = text.strip()
                if clean_text.startswith("
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1
http://googleusercontent.com/immersive_entry_chip/2
http://googleusercontent.com/immersive_entry_chip/3
