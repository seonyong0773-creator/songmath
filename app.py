import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 1. 앱 설정 및 모바일 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 강력한 커스텀 디자인 (CSS)
# 버튼 6개를 가로로 꽉 채우고, 화면 고정력을 높입니다.
st.markdown("""
    <style>
    /* 1. 라디오 버튼을 가로형 6칸 슬림 바 디자인으로 개조 */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 3px;
        border: 1px solid #d1d5db;
        display: flex;
        justify-content: space-between;
    }
    div[data-testid="stRadio"] label {
        flex: 1;
        text-align: center;
        padding: 8px 2px !important;
        margin: 0 1px !important;
        font-size: 11px !important; /* 버튼이 많아져서 글자 크기 축소 */
        font-weight: bold;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: white !important;
        border-radius: 7px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        color: #007BFF;
    }
    div[data-testid="stRadio"] input {
        display: none;
    }

    /* 2. 화면 전체 여백 제거 (스크롤 원천 봉쇄) */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* 3. 제목 및 메트릭 텍스트 크기 조절 */
    h1 { font-size: 1.5rem !important; text-align: center; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 및 세션 초기화
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    # 기본 샘플 데이터
    names = ["김철수", "이영희", "박지민", "최하늘", "정민수", "강다은", "조세호", "윤서아"]
    st.session_state.student_data = pd.DataFrame([
        {"Name": name, "Class": ["17:00", "19:00", "21:00"][i%3], 
         "Last Payment": today - timedelta(days=np.random.randint(0, 30))} 
        for i, name in enumerate(names)
    ])

if 'rent_cost' not in st.session_state: st.session_state.rent_cost = 800000
if 'other_cost' not in st.session_state: st.session_state.other_cost = 300000

# 데이터 가공 함수
def get_processed_df():
    df = st.session_state.student_data.copy()
    if df.empty: return pd.DataFrame(columns=['Name', 'Class', 'Last Payment', 'Next Due', 'D-Day'])
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 인터페이스 시작 ---
st.title("🏫 송수학 통합 관리")

# 4. 가로 6버튼 통합 메뉴 (현황, 관리, 수익, 지출, 알림, 연장)
menu_choice = st.radio(
    "메뉴", 
    ["📍현황", "👤관리", "💰수익", "🛠️지출", "🔔알림", "🗓️연장"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

current_df = get_processed_df()
FEE = 300000

# --- 5. 페이지 전환 로직 ---

# [1. 현황]
if menu_choice == "📍현황":
    target_class = st.selectbox("반", ["17:00", "19:00", "21:00"], label_visibility="collapsed")
    filtered = current_df[current_df['Class'].str.contains(target_class)]
    st.write(f"현재: **{len(filtered)}명**")
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=350)

# [2. 관리]
elif menu_choice == "👤관리":
    sub1, sub2 = st.tabs(["➕등록", "❌퇴원"])
    with sub1:
        with st.form("add_form", clear_on_submit=True):
            n_name = st.text_input("학생이름")
            n_class = st.selectbox("반", ["17:00", "19:00", "21:00"])
            if st.form_submit_button("등록"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    st.rerun()
    with sub2:
        del_target = st.selectbox("삭제", [""] + current_df['Name'].tolist())
        if st.button("삭제 수행"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                st.rerun()

# [3. 수익] - 심플한 매출/순수익 지표
elif menu_choice == "💰수익":
    st.subheader("이번 달 수익 요약")
    total_rev = len(current_df) * FEE
    net_profit = total_rev - (st.session_state.rent_cost + st.session_state.other_cost)
    
    st.metric("이번 달 총 매출", f"{total_rev:,.0f}원")
    st.metric("이번 달 순수익", f"{net_profit:,.0f}원")
    st.caption(f"기준: 원생 {len(current_df)}명")

# [4. 지출] - 수정 전용 창구
elif menu_choice == "🛠️지출":
    st.subheader("지출 설정 수정")
    st.session_state.rent_cost = st.number_input("월세 입력", value=st.session_state.rent_cost, step=10000)
    st.session_state.other_cost = st.number_input("기타 지출 입력", value=st.session_state.other_cost, step=5000)
    st.success("수정사항이 실시간 반영되었습니다.")

# [5. 알림] - 결제 알림 전용
elif menu_choice == "🔔알림":
    st.subheader("D-Day 결제 알림")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    if not alerts.empty:
        st.dataframe(alerts[['Name', 'Class', 'D-Day']], use_container_width=True, height=350)
    else:
        st.success("결제 임박 학생 없음")

# [6. 연장] - 일정 연장 전용
elif menu_choice == "🗓️연장":
    st.subheader("일정 연장 처리")
    target_s = st.selectbox("학생 선택", current_df['Name'].tolist())
    days = st.number_input("연장 일수", value=1, min_value=1)
    if st.button("기간 연장 적용"):
        idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
        st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=days)
        st.rerun()