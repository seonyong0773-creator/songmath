import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 1. 앱 기본 설정 및 모바일 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 강력한 커스텀 디자인 (CSS)
# 버튼을 가로로 강제 배치하고, 제목과 여백을 조절합니다.
st.markdown("""
    <style>
    /* 상단 제목과 메뉴 사이 여백 조절 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* 버튼 가로 배치를 위한 스타일 */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        background-color: #f8f9fa;
        border: 1px solid #d1d5db;
        font-size: 14px;
    }
    
    /* 버튼 클릭 시 강조 효과 */
    div.stButton > button:focus {
        background-color: #007BFF !important;
        color: white !important;
        border-color: #007BFF !important;
    }

    /* 스마트폰 '당겨서 새로고침' 방지 */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        overflow: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 초기화 및 세션 상태 관리
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    sample_names = ["김철수", "이영희", "박지민", "최하늘", "정민수", "강다은", "조세호", "윤서아", "한가람", "임재현"]
    sample_data = []
    for i, name in enumerate(sample_names):
        sample_data.append({
            "Name": name, 
            "Class": ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"][i%3], 
            "Last Payment": today - timedelta(days=i*3)
        })
    st.session_state.student_data = pd.DataFrame(sample_data)

# 현재 어떤 방(페이지)에 있는지 기억
if 'page' not in st.session_state:
    st.session_state.page = "📍 현황"

# 상수 설정
FEE = 300000
EXPENSES = 1100000

# 데이터 처리 함수
def get_processed_df():
    df = st.session_state.student_data.copy()
    df['Next Due'] = pd.to_datetime(df['Last Payment']).dt.date + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 타이틀 (슬림화 취소) ---
st.title("🏫 송수학 통합 관리")

# --- 4. 가로 배치 버튼 메뉴 (가로 3칸 구성) ---
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("📍 현황"):
        st.session_state.page = "📍 현황"
with m2:
    if st.button("👤 관리"):
        st.session_state.page = "👤 관리"
with m3:
    if st.button("💰 회계"):
        st.session_state.page = "💰 회계"

st.divider()

# 최신 데이터 불러오기
current_df = get_processed_df()

# --- 5. 페이지 전환 (선택된 방의 내용만 보여줌) ---

# [방 1: 인원 현황]
if st.session_state.page == "📍 현황":
    st.write("### 📍 실시간 수강 현황")
    target_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
    filtered = current_df[current_df['Class'] == target_class]
    
    st.write(f"현재 인원: **{len(filtered)}명**")
    # 표 높이를 고정하여 스크롤이 앱 전체를 키우지 않게 함
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], height=300, use_container_width=True)

# [방 2: 원생 관리]
elif st.session_state.page == "👤 관리":
    st.write("### 👤 원생 등록 및 삭제")
    
    with st.expander("➕ 신규 원생 등록", expanded=True):
        with st.form("add_student_form", clear_on_submit=True):
            n_name = st.text_input("이름")
            n_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
            if st.form_submit_button("등록 완료"):
                if n_name:
                    new_student = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_student], ignore_index=True)
                    st.success(f"{n_name} 등록 성공!")
                    st.rerun()
    
    st.divider()
    
    with st.expander("❌ 퇴원 처리"):
        del_target = st.selectbox("삭제할 학생", [""] + current_df['Name'].tolist())
        if st.button("영구 삭제"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                st.rerun()

# [방 3: 회계 및 알림]
elif st.session_state.page == "💰 회계":
    st.write("### 💰 회계 및 일정")
    
    # 수익 지표
    total_revenue = len(current_df) * FEE
    profit = total_revenue - EXPENSES
    st.metric("예상 순수익", f"{profit:,.0f}원", delta=f"매출 {total_revenue:,.0f}원")

    # 결제일 연장
    with st.expander("🗓️ 일정 연장 (휴강/보강)"):
        target_s = st.selectbox("대상 학생", current_df['Name'].tolist())
        add_days = st.number_input("연장 일수", value=1, min_value=1)
        if st.button("기간 연장 적용"):
            idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
            st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=add_days)
            st.success("연장 완료!")
            st.rerun()

    st.divider()

    # 미납 알림 (내부 스크롤 적용)
    st.write("**🔔 결제 알림 (D-5 이내)**")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    st.dataframe(alerts[['Class', 'Name', 'D-Day']], height=200, use_container_width=True)