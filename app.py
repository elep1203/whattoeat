import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import json
import google.generativeai as genai

# --- [1. API 키 설정] ---
ACCESS_KEY = st.secrets["ACCESS_KEY"]
SECRET_KEY = st.secrets["SECRET_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# 제미나이 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- [함수: 제미나이 AI 식단 생성] ---
def get_ai_meal_plan(selected_meals, avoid_food, fridge_input):
    prompt = f"""
    당신은 한국 최고의 요리사입니다. 아래 조건에 맞춰 일주일 식단을 짜주세요.
    - 선택된 끼니: {', '.join(selected_meals)}
    - 제외할 재료(알러지/싫음): {avoid_food}
    - 냉장고에 이미 있는 재료: {fridge_input}
    
    [조건]
    1. '만개의레시피'에서 가장 인기 있는 한국 가정식 메뉴 위주로 선정하세요.
    2. 결과는 반드시 아래 JSON 형식으로만 출력하세요. (JSON 외 텍스트 금지)
       Format: [{{"요일": "월", "아침": "메뉴명", "아침재료": "장볼것", "점심": "...", "점심재료": "...", "저녁": "...", "저녁재료": "..."}}]
    3. 냉장고 재료가 활용되면 재료 칸에 '이미있음'이라고 적으세요.
    """
    response = model.generate_content(prompt)
    json_text = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(json_text)

# --- [함수: 쿠팡 수익 링크 생성] ---
def get_coupang_link(keyword):
    if keyword == "이미있음" or not keyword: return None
    domain = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplinks"
    target_url = f"https://www.coupang.com/np/search?q={keyword}"
    data = {"coupangUrls": [target_url]}
    payload = json.dumps(data)
    timestamp = time.strftime('%y%m%d') + 'T' + time.strftime('%H%M%S') + 'Z'
    message = timestamp + "POST" + path
    signature = hmac.new(bytes(SECRET_KEY, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={signature}"
    headers = {"Content-Type": "application/json", "Authorization": authorization}
    try:
        res = requests.post(domain + path, headers=headers, data=payload)
        return res.json()['data'][0]['shortenUrl']
    except: return f"https://www.coupang.com/np/search?q={keyword}"

# --- [2. 화면 구성] ---
st.set_page_config(page_title="끼니워리 AI", layout="wide")
st.sidebar.header("🏠 우리 집 정보")
selected_meals = st.sidebar.multiselect("🍱 식단 선택", ["아침", "점심", "저녁"], default=["저녁"])
avoid_food = st.sidebar.text_input("❌ 못 먹는 재료", placeholder="예: 오이, 땅콩")
fridge_input = st.sidebar.text_area("🧊 냉장고 재료", "양파, 파, 마늘")

st.title("🚀 식단짜기 (Gemini AI)")

if st.sidebar.button("✨ AI 맞춤 식단 생성"):
    with st.spinner('제미나이가 식단을 짜고 있습니다...'):
        try:
            meal_plan = get_ai_meal_plan(selected_meals, avoid_food, fridge_input)
            
            st.subheader("🗓️ 이번 주 맞춤 식단표")
            st.info("💡 메뉴를 클릭하면 '만개의레시피' 조리법으로 연결됩니다.")
            
            # 식단표 예쁘게 출력
            df = pd.DataFrame(meal_plan).set_index('요일')
            display_cols = [m for m in ["아침", "점심", "저녁"] if m in selected_meals]
            
            # 클릭 가능한 링크로 변환하여 출력
            for day in ["월", "화", "수", "목", "금", "토", "일"]:
                cols = st.columns([1] + [2]*len(display_cols))
                cols[0].write(f"**{day}**")
                for i, m in enumerate(display_cols):
                    menu_name = df.loc[day, m]
                    url = f"https://www.10000recipe.com/recipe/list.html?q={menu_name}"
                    cols[i+1].markdown(f"[{menu_name}]({url})")

            st.divider()
            st.subheader("🛒 쿠팡에서 장보기")
            
            shopping_list = set()
            for day_data in meal_plan:
                for m in selected_meals:
                    item = day_data.get(f"{m}재료")
                    if item and item != "이미있음": shopping_list.add(item)
            
            if not shopping_list:
                st.success("✅ 모든 재료가 냉장고에 있네요!")
            else:
                c = st.columns(3)
                for idx, item in enumerate(sorted(list(shopping_list))):
                    link = get_coupang_link(item)
                    c[idx % 3].link_button(f"👉 {item} 구매", link)
            st.balloons()
        except Exception as e:
            st.error("AI와 대화 중 오류가 났어요. 다시 시도해 주세요!")
