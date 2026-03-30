import streamlit as st
import json
from google import genai
from google.genai import types 
from supabase import create_client, Client

# 1. 페이지 설정
st.set_page_config(page_title="한겨울 라이브 챗", page_icon="❄️")
st.markdown("""
    <style>
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# 💡 [수정 후: 이 코드를 통째로 복붙해! (네 깃허브 아이디 부분만 수정)]
# 네 테섭 깃허브 아이디 (예: appppie1717-beep)를 따옴표 안에 정확히 넣어줘!
YOUR_GITHUB_ID = "appppie1717-beep"

# 스트림릿이 현재 실행 중인 깃허브 저장소 이름을 자동으로 알아내는 창조주의 마법!
import os
import streamlit.components.v1 as components

try:
    # 현재 배포된 스트림릿 앱의 깃허브 정보를 싹 긁어오는 시크릿 함수!
    app_info = components.get_current_page_config()
    current_repo_name = app_info["github_repository"] # 예: appppie1717-beep/winter-chat-test
    github_base_url = f"https://raw.githubusercontent.com/{current_repo_name}/main/images/"
except:
    # 정 안 되면 네가 테섭 저장소 이름을 직접 적어둔 걸로 가져오게 하는 안전망! (수동으로 winter-chat-test 입력)
    github_base_url = f"https://raw.githubusercontent.com/{YOUR_GITHUB_ID}/winter-chat-test/main/images/"

# 🚨 14가지 상황별 일러스트 지도 (자동 경로 버전)
scene_images = {
    "기본": github_base_url + "집에서 플레이어를 정면으로 주시함.png?raw=true",
    "침대_유혹": github_base_url + "새벽. 집안. 침대에 옆으로 누워서 플레이어를 바라봄.(이리와 하는듯한 느낌).png?raw=true",
    "아련_문": github_base_url + "새벽에 문열고 아련하게 쳐다봄.png?raw=true",
    "아련_벽": github_base_url + "새벽에 벽을 등지고 서서 아련하게 정면을 주시한다(측면).png?raw=true",
    "힘듦": github_base_url + "집 벽을 힘든듯이 기댄다.png?raw=true",
    "당황_숨가쁨": github_base_url + "집안. 창문옆에서 플레이어를 쳐다봄. 숨을 헐떡거림.png?raw=true",
    "취기_웃음": github_base_url + "집에서 플레이어를 정면으로 보는데 취기가 있는 얼굴에 웃고있음.png?raw=true",
    "슬픔_훌쩍": github_base_url + "집에서 훌쩍거림.png?raw=true",
    "침대_누움": github_base_url + "침대에 누움(야한각도).png?raw=true",
    "침대_앉음": github_base_url + "침대에 앉아서 플레이어를 쳐다봄.png?raw=true",
    "침대_요염": github_base_url + "침대에서 요염한 자세를 취하면서 플레이어를 쳐다봄.png?raw=true",
    "침대_내려다봄": github_base_url + "침대에서 플레이어를 내려다봄.png?raw=true",
    "포옹_허리": github_base_url + "침대에서 플레이어의 허리를 껴안음(아랫도리).png?raw=true",
    "키스": github_base_url + "키스하는중(남자 얼굴 반쯤 나옴).png?raw=true"
}
# 2. 열쇠 꺼내오기
api_key = st.secrets["GOOGLE_API_KEY"]
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(supabase_url, supabase_key)
client = genai.Client(api_key=api_key)

# 4. 문지기 로직
if "user_name" not in st.session_state:
    st.title("❄️ 한겨울 라이브 챗 접속")
    st.write("한겨울이 당신을 뭐라고 불러드릴까요?")
    with st.form(key='login_form'):
        name_input = st.text_input("당신의 닉네임을 입력해주세요.")
        submit_button = st.form_submit_button(label='대화 시작하기 ➡️')
    if submit_button and name_input:
        st.session_state.user_name = name_input
        st.rerun()

else:
    user_name = st.session_state.user_name

    # 🚨 DB 데이터 불러오기
    if "chat_history" not in st.session_state or "inventory" not in st.session_state:
        response = supabase.table("chat_memory").select("*").eq("user_name", user_name).order("id").execute()
        db_history = response.data

        st.session_state.chat_history = []
        st.session_state.inventory = [] 
        
        for row in db_history:
            if row["role"] == "inventory":
                st.session_state.inventory.append(row["message"]) 
            else:
                st.session_state.chat_history.append((row["role"], row["message"]))

        if not st.session_state.chat_history:
            first_msg = f'{{"장면": "기본", "행동": "팔짱을 꼬며 쳐다본다", "호감도변화": 0, "획득아이템": "없음", "대사": "뭐야, {user_name}. 왜 이렇게 일찍 일어났어?"}}'
            st.session_state.chat_history.append(("assistant", first_msg))
            supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": first_msg}).execute()

    current_items = ", ".join(st.session_state.inventory) if st.session_state.inventory else "아직 받은 선물 없음"
    
    # 🚨 [프롬프트 대수술] 19금, 스토킹 원천 차단 가드레일 추가!
    winter_persona = f"""
    너의 이름은 '한겨울'이고, 20대 초반의 내 여사친이야.
    내 닉네임은 '{user_name}'이야. 
    [현재 네가 {user_name}에게 받은 선물(인벤토리): {current_items}]

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

    col1, col2 = st.columns([7, 3])
    with col1:
        st.title(f"❄️ {user_name} & 한겨울 (VR Test)")
    with col2:
        st.write("") 
        if st.button("🔄 기억 리셋", use_container_width=True):
            supabase.table("chat_memory").delete().eq("user_name", user_name).execute()
            st.session_state.clear()
            st.rerun()
            
    st.divider()

    with st.expander("📢 한겨울 라이브 챗 패치 노트 (업데이트 역사관)"):
        with st.container(height=250):
            st.markdown("""
            **[ v1.6.0 ] 2026.03.30 (월)**
            * **[18:50] 가드레일 시스템 도입:** 선을 넘는 19금 성적 묘사, 스토킹, 욕설 등 불건전한 대화 시도 시 봇이 강력하게 철벽을 치고 거절하도록 AI 윤리 필터(가드레일)가 적용되었습니다.
            * **[08:20] 인벤토리 시스템:** 유저가 준 선물을 영구적으로 기억하고 사이드바에 보관합니다.
            * **[08:20] 기억 압축 엔진:** 데이터 폭발을 막기 위해 최근 20개 대화만 유지하는 슬라이딩 윈도우 기법 적용!
            * **[07:45] 몰입도 UI 패치:** 로딩 스피너 및 전송 알림창(Toast) 추가
            * **[00:30] 대형 CG 패치:** 말풍선 내 대형 일러스트 출력 그래픽 업그레이드
            """)

    for role, text in st.session_state.chat_history:
        if role == "user":
            with st.chat_message("user"):
                st.markdown(text)
        else:
            try:
                data = json.loads(text)
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
        
        if len(valid_history) > 0 and valid_history[0][0] == "assistant":
            valid_history = valid_history[1:]

        # 🚨 최근 20개 메시지만 AI에게 전송해서 서버 폭파 방지!
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
            parsed_data = json.loads(raw_json_text)
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
        except:
            with st.chat_message("assistant", avatar="❄️"):
                st.markdown(raw_json_text)
                
        st.session_state.chat_history.append(("assistant", raw_json_text))
        supabase.table("chat_memory").insert({"user_name": user_name, "role": "assistant", "message": raw_json_text}).execute()
        
        st.rerun()
