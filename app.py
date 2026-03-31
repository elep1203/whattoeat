import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import json
import random # 🌟 랜덤 기능을 위해 추가!

# --- [1. 쿠팡 API 설정] ---
ACCESS_KEY = "79a39820-24f1-4f82-9f85-1a057ef8e147"
SECRET_KEY = "f1dff873f80f9600417e3dca6359bff5d68e7a42"

def get_coupang_deep_link(keyword):
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
        response = requests.post(domain + path, headers=headers, data=payload)
        return response.json()['data'][0]['shortenUrl']
    except: return f"https://www.coupang.com/np/search?q={keyword}"

# --- [2. 웹앱 화면 설정] ---
st.set_page_config(page_title="스마트 식단 매니저", layout="wide")

st.sidebar.header("🏠 우리 집 정보")
selected_meals = st.sidebar.multiselect("🍱 식단 선택", ["아침", "점심", "저녁"], default=["저녁"])
budget = st.sidebar.number_input("일주일 예산 (원)", 120000)
fridge = st.sidebar.text_area("냉장고 재료", "양파, 파프리카, 양상추")

st.title("🚀 중복 방지 스마트 식단 매니저")

if st.sidebar.button("✨ 새로운 식단 생성하기"):
    if not selected_meals:
        st.warning("⚠️ 최소 한 개 이상의 끼니를 선택해주세요!")
    else:
        with st.spinner('중복되지 않는 새로운 식단을 구성 중입니다...'):
            # 🌟 메뉴 후보군을 넉넉하게 준비 (각 10개 이상)
            db = {
                "아침": [
                    {"menu": "토스트 & 우유", "item": "서울우유"}, {"menu": "사과 & 요거트", "item": "요거트"},
                    {"menu": "계란 후라이 & 베이컨", "item": "베이컨"}, {"menu": "누룽지 & 김치", "item": "누룽지"},
                    {"menu": "시리얼", "item": "켈로그 시리얼"}, {"menu": "바나나 & 두유", "item": "두유"},
                    {"menu": "프렌치 토스트", "item": "식빵"}, {"menu": "감자 샐러드", "item": "감자"},
                    {"menu": "모닝빵 샌드위치", "item": "모닝빵"}, {"menu": "오트밀", "item": "오트밀"}
                ],
                "점심": [
                    {"menu": "새우 볶음밥", "item": "냉동볶음밥"}, {"menu": "잔치국수", "item": "소면"},
                    {"menu": "참치 비빔밥", "item": "캔참치"}, {"menu": "떡볶이", "item": "밀떡"},
                    {"menu": "샌드위치", "item": "슬라이스 햄"}, {"menu": "카레 라이스", "item": "카레가루"},
                    {"menu": "냉면", "item": "함흥냉면"}, {"menu": "김치볶음밥", "item": "스팸"},
                    {"menu": "만두국", "item": "냉동만두"}, {"menu": "파스타", "item": "스파게티면"}
                ],
                "저녁": [
                    {"menu": "냉제육", "item": "앞다리살 2kg"}, {"menu": "차돌 양상추찜", "item": "차돌박이"},
                    {"menu": "미나리 제육", "item": "청도 미나리"}, {"menu": "훈제오리 볶음", "item": "다향 훈제오리"},
                    {"menu": "소고기 무국", "item": "국거리 소고기"}, {"menu": "수제 버거", "item": "햄버거 패티"},
                    {"menu": "파프리카 닭갈비", "item": "닭다리살"}, {"menu": "된장찌개", "item": "찌개용두부"},
                    {"menu": "고등어 구이", "item": "손질고등어"}, {"menu": "부대찌개", "item": "모듬소시지"}
                ]
            }

            days = ["월", "화", "수", "목", "금", "토", "일"]
            final_rows = []
            shopping_set = set()

            # 🌟 핵심: 메뉴 리스트를 랜덤하게 섞음!
            for m in db:
                random.shuffle(db[m])

            for i, day in enumerate(days):
                row = {"요일": day}
                for meal in ["아침", "점심", "저녁"]:
                    if meal in selected_meals:
                        # 섞인 리스트에서 순서대로 가져옴
                        meal_info = db[meal][i] 
                        row[meal] = meal_info["menu"]
                        shopping_set.add(meal_info["item"])
                    else:
                        row[meal] = "-"
                final_rows.append(row)

            # 결과 출력
            st.subheader("🗓️ 이번 주 맞춤 식단표")
            st.table(pd.DataFrame(final_rows).set_index('요일'))
            
            st.divider()
            st.subheader("🛒 실시간 수익 링크 (중복 제거)")
            
            cols = st.columns(3)
            for idx, item in enumerate(sorted(list(shopping_set))):
                with cols[idx % 3]:
                    link = get_coupang_deep_link(item)
                    st.link_button(f"👉 {item} 최저가", link)
                    
        st.balloons()