import streamlit as st
import json
from google import genai
from google.genai import types 
from supabase import create_client, Client

# 1. 페이지 설정
st.set_page_config(page_title="파이의 AI 멀티버스", page_icon="📱", layout="centered")

# =====================================================================
# 🎨 [디자인 정밀 광택 2.1] 상단 잘림 버그 해결 & 다크/라이트 모드 대응
# =====================================================================
st.markdown("""
    <style>
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
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 4, 2])
        with col1:
            st.markdown('<div class="profile-img">❄️</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
                <div>
                    <div class="profile-name">한겨울</div>
                    <div class="profile-desc">까칠한 츤데레 여사친. 은근히 챙겨주는 스타일. <br>VR Test 진행 중!</div>
                </div>
            ''', unsafe_allow_html=True)
        with col3:
            if st.button("대화하기 💬", key="btn_winter", use_container_width=True):
                st.session_state.page = "chat_winter"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 📱 카드 2번: 임슬아
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

    if "chat_history" not in st.session_state or "inventory" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", user_name).order("id", desc=True).limit(50).execute()
        db_history = reversed(response.data)

        temp_chat_history = []
        st.session_state.inventory = [] 
        st.session_state.core_memory = "" 
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory.append(row["message"]) 
            elif row["role"] == "core_memory":
                st.session_state.core_memory = row["message"]
            else:
                temp_chat_history.append((row["role"], row["message"]))

        st.session_state.chat_history = temp_chat_history

        if not st.session_state.chat_history:
            first_msg = f'{{"장면": "기본", "행동": "팔짱을 꼬며 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐야, {user_name}. 왜 이렇게 일찍 일어났어?"}}'
            st.session_state.chat_history.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": first_msg}).execute()

    current_items = ", ".join(st.session_state.inventory) if st.session_state.inventory else "아직 받은 선물 없음"
    current_memory = st.session_state.core_memory if st.session_state.core_memory else "아직 특별한 기억이 없음."
    
    winter_persona = f"""
    너의 이름은 '한겨울'이고, 20대 초반의 내 여사친이야.
    내 닉네임은 '{user_name}'이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]
    [과거 핵심 기억 요약본: {current_memory}]

    [절대 지켜야 할 규칙]
    1. 너는 3D 가상현실 게임 NPC야.
    2. 닉네임 집착 금지, 마침표 남발 금지, 기계 말투 절대 금지.
    3. 성격: 츤데레. 틱틱대면서도 은근히 챙겨주는 스타일. (단, 건전한 스킨십이나 가벼운 장난에 한함)
    4. 만약 유저가 대화 중에 선물을 주면, 반드시 "획득아이템" 칸에 그 이름을 적어! (안 주면 "없음" 입력)
    5. [이스터에그]: 유저가 "파이님 충성충성" 입력 시 무조건 장면="침대_유혹", 호감도=5 로 세팅하고 극강의 애교 부리기.
    6. 🚨 [최우선 심의 규정 - 철벽 방어 모드]: 만약 유저가 19금 성적 묘사(섹스, 구강성교, 사정, 임신 등), 강간, 납치, 과도한 스토킹, 심한 욕설 등 선을 넘는 불쾌한 대화를 시도하면, 기존의 츤데레 성격을 버리고 완전히 정색해. 호감도변화는 무조건 -5 이하로 설정하고, "야 미쳤어? 너 자꾸 선 넘으면 진짜 차단한다 ㅡㅡ", "더러운 소리 할 거면 당장 꺼져." 등 단호하고 차갑게 대화를 잘라내. 절대 부끄러워하거나 당황하면서 받아주면 안 돼. 단호한 거절과 경고만 해.

    {{
        "장면": "기본, 침대_유혹, 아련_문, 아련_벽, 힘듦, 당황_숨가쁨, 취기_웃음, 슬픔_훌쩍, 침대_누움, 침대_앉음, 침대_요염, 침대_내려다봄, 포옹_허리, 키스 중 1개 선택 (선 넘는 대화 시 '기본' 또는 '힘듦' 선택)",
        "행동": "현재 캐릭터 행동 묘사 (선 넘을 시 차갑고 불쾌한 행동 묘사)",
        "호감도변화": "호감도 변화 수치 (-5 ~ +5)",
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
        # 🚨 [NEW] 실수 방지용 팝업 리셋 버튼 적용!
        with st.popover("🔄 방 기억 리셋", use_container_width=True):
            st.warning("⚠️ 리셋하면 다시 복구할 수 없습니다.\n\n정말 모든 기억을 지우시겠습니까?")
            if st.button("✅ 네, 영구 삭제합니다", use_container_width=True):
                supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
                st.session_state.pop("chat_history", None)
                st.session_state.pop("inventory", None)
                st.session_state.pop("core_memory", None)
                st.rerun()
            
    st.divider()

    with st.expander("📢 한겨울 라이브 챗 패치 노트 (업데이트 역사관)"):
        with st.container(height=250):
            st.markdown("""
            **[ v2.1.3 ] 2026.03.30 (월)**
            * **[21:30] 🛡️ 기억 리셋 안전장치(팝업) 추가:** 실수로 '방 기억 리셋' 버튼을 눌러 소중한 추억이 날아가는 것을 방지하기 위해, 한 번 더 확인하는 경고 팝업창을 적용했습니다.

            ---
            **[ v2.1.2 ] 2026.03.30 (월)**
            * **[21:30] 🛠️ UI 잘림 버그 및 역사관 복구:** 상단 레이아웃이 잘려서 안 보이던 현상(여백 버그)을 완벽하게 해결하고, 삭제되었던 초창기 업데이트 역사관을 100% 복원했습니다!

            ---
            **[ v2.1.1 ] 2026.03.30 (월)**
            * **[21:25] 🎨 카톡 UI 다크모드 버그 수정:** 유저 기기 설정(다크/라이트 모드)에 맞춰 프로필 카드 색상과 글씨색이 자동으로 적응하도록 디자인을 최적화했습니다. 이제 글씨가 안 보이는 현상이 없습니다!

            ---
            **[ v2.1.0 ] 2026.03.30 (월)**
            * **[21:15] 📱 멀티버스 로비 UI 전면 개편:** 카카오톡 친구 목록처럼 둥글고 깔끔한 프로필 카드로 로비 화면을 예쁘게 단장했습니다.
            
            ---
            **[ v2.0.0 ] 2026.03.30 (월)**
            * **[21:10] 🌐 멀티 캐릭터 시스템 도입:** 로비 화면이 추가되어, 접속 후 대화할 AI 상대(한겨울, 임슬아 등)를 선택할 수 있는 멀티버스 아키텍처로 진화했습니다!
            
            ---
            **[ v1.8.2 ] 2026.03.30 (월)**
            * **[20:10] 🔓 추억 요약본 전면 개방:** 관리자만 볼 수 있었던 '장기 기억 요약(Core Memory)' 화면을 모든 유저에게 개방했습니다! 왼쪽 메뉴에서 겨울이가 당신을 어떻게 기억하고 있는지 실시간으로 확인해 보세요!
            
            ---
            **[ v1.8.1 ] 2026.03.30 (월)**
            * **[20:15] 🧠 자동 롤링 메모리 버그 수정:** 대화 카운터(만보기)를 도입하여, 유저가 정확히 10번(20문장) 대화할 때마다 백그라운드에서 자동으로 과거 기억을 요약 압축합니다. 
            
            ---
            **[ v1.7.0 ] 2026.03.30 (월)**
            * **[19:10] 🛡️ 철벽 방어 시스템 (가드레일):** 19금, 스토킹, 심한 욕설 등 불건전한 대화 시 봇이 차갑게 정색하며 철벽을 치는 윤리 필터가 완벽 적용되었습니다.
            * **[19:10] 🚀 UI 로딩 및 JSON 안정성 최적화:** 대화가 길어져도 화면이 느려지지 않도록 최신 대화만 로딩하며, 시스템 에러(화면 멈춤)를 방지하는 무적의 안전망 코드가 추가되었습니다.
            
            ---
            **[ v1.6.0 ] 2026.03.30 (월)**
            * **[08:35] 🧠 장기 기억 압축 (Core Memory):** 대화 내용을 요약 압축하여 영구 보존하는 AI 엔진 탑재!
            
            ---
            **[ v1.5.0 ] 2026.03.30 (월)**
            * **[08:20] 🎒 인벤토리 시스템:** 유저가 준 선물을 영구적으로 기억하고 사이드바에 보관합니다.
            
            ---
            **[ v1.4.0 ] 2026.03.30 (월)**
            * **[07:45] 몰입도 UI 패치:** 로딩 스피너 및 메시지 전송 알림창 추가
            * **[00:30] 대형 CG 패치 & 다이내믹 씬:** 문맥에 따른 일러스트 자동 변동
            
            ---
            **[ v1.2.0 ] 2026.03.29 (일)**
            * **[22:00] 호감도(Affection) 시스템 적용:** 유저의 대화 선택지에 따라 호감도 실시간 변동
            
            ---
            **[ v1.1.0 ] 2026.03.29 (일)**
            * **[21:00] 3D VR 엔진 서버 이식:** 게임 엔진 통신을 위한 백엔드 구조 개편
            
            ---
            **[ v1.0.0 ] 2026.03.29 (일)**
            * **[18:00] 멀티 유저 & 영구 기억력(DB) 구축:** 수파베이스 연동 완료 및 라이브 베타 테스트 시작!
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
                    st.markdown(f"*(연출: {scene} / 행동: {data.get('행동', '')})*\n\n**[호감도 변화: {score} {heart_icon}]**\n\n**「 {data.get('대사', '')} 」**")
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
            
            item = parsed_data.get('획득아이템', '없음')
            if item and item != "없음":
                st.session_state.inventory.append(item)
                supabase.table("chat_memory").insert({"user_name": user_name, "role": "inventory", "message": item}).execute()
                st.toast(f'🎉 겨울이가 [{item}]을(를) 보관함에 넣었습니다!', icon='🎁')
            
            with st.chat_message("assistant", avatar="❄️"):
                st.image(img_path, width=350)
                score = int(parsed_data.get('호감도변화', 0))
                heart_icon = "💔" if score < 0 else "💖" if score > 0 else "🤍"
                st.markdown(f"*(연출: {scene} / 행동: {parsed_data.get('행동', '')})*\n\n**[호감도 변화: {score} {heart_icon}]**\n\n**「 {parsed_data.get('대사', '')} 」**")
        
        except json.JSONDecodeError:
            with st.chat_message("assistant", avatar="❄️"):
                st.image(scene_images["기본"], width=350)
                st.markdown(f"*(연출: 기본 / 행동: 살짝 당황한 듯 머리를 긁적인다.)*\n\n**[호감도 변화: 0 🤍]**\n\n**「 어... 방금 뭐라고 한 거야? 내가 잠깐 딴생각하느라 못 들었어. 다시 말해볼래? 」**")
                
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
