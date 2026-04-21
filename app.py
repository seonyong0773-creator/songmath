import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. 앱 설정 및 모바일 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 강력한 커스텀 디자인 (CSS)
st.markdown("""
    <style>
    /* 1. 라디오 버튼을 가로형 4칸 통합 바 디자인으로 개조 */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #f0f2f6;
        border-radius: 12px;
        padding: 5px;
        border: 1px solid #d1d5db;
    }
    div[data-testid="stRadio"] label {
        flex: 1;
        text-align: center;
        background-color: transparent;
        padding: 10px;
        border-radius: 8px;
        cursor: pointer;
        margin: 0 2px;
        font-weight: bold;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: white !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        color: #007BFF;
    }
    div[data-testid="stRadio"] input {
        display: none;
    }

    /* 2. 모바일 화면 여백 및 스크롤 최적화 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* 3. 제목 크기 축소하여 공간 확보 */
    h1 {
        font-size: 1.8rem !important;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 및 고정비 상태 초기화
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    # 샘플 데이터 초기화
    st.session_state.student_data = pd.DataFrame([
        {"Name": "김철수", "Class": "17:00 (고1)", "Last Payment": today - timedelta(days=5)},
        {"Name": "이영희", "Class": "19:00 (고2)", "Last Payment": today - timedelta(days=28)},
        {"Name": "박지민", "Class": "21:00 (고3)", "Last Payment": today - timedelta(days=15)}
    ])

if 'rent_cost' not in st.session_state: st.session_state.rent_cost = 800000
if 'other_cost' not in st.session_state: st.session_state.other_cost = 300000

# 데이터 가공 함수
def get_processed_df():
    df = st.session_state.student_data.copy()
    if df.empty:
        return pd.DataFrame(columns=['Name', 'Class', 'Last Payment', 'Next Due', 'D-Day'])
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 인터페이스 시작 ---
st.title("🏫 송수학 통합 관리")

# 4. 가로 통합 메뉴 바 (알림 추가하여 4칸으로 구성)
menu_choice = st.radio(
    "메뉴", 
    ["📍현황", "👤관리", "💰회계", "🔔알림"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

current_df = get_processed_df()
FEE_PER_STUDENT = 300000

# --- 5. 페이지 전환 로직 ---

# [1. 현황 페이지]
if menu_choice == "📍현황":
    st.subheader("타임별 인원 현황")
    target_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"], label_visibility="collapsed")
    filtered = current_df[current_df['Class'] == target_class]
    st.write(f"현재 인원: **{len(filtered)}명**")
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=300)

# [2. 관리 페이지]
elif menu_choice == "👤관리":
    st.subheader("원생 등록 및 퇴원")
    tab1, tab2 = st.tabs(["➕ 등록", "❌ 퇴원"])
    with tab1:
        with st.form("add_form", clear_on_submit=True):
            n_name = st.text_input("학생 이름")
            n_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
            if st.form_submit_button("등록 완료"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    st.rerun()
    with tab2:
        del_target = st.selectbox("삭제 대상", [""] + current_df['Name'].tolist())
        if st.button("학생 정보 삭제"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                st.rerun()

# [3. 회계 페이지] - 여기는 이제 숫자만 보여서 스크롤 필요 없음!
elif menu_choice == "💰회계":
    st.subheader("이번 달 회계 장부")
    
    total_revenue = len(current_df) * FEE_PER_STUDENT
    total_expenses = st.session_state.rent_cost + st.session_state.other_cost
    net_profit = total_revenue - total_expenses
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("이번 달 총 매출", f"{total_revenue:,.0f}원")
    with c2:
        st.metric("이번 달 순수익", f"{net_profit:,.0f}원")

    st.divider()
    
    with st.expander("🛠️ 지출 설정 수정"):
        st.session_state.rent_cost = st.number_input("월세", value=st.session_state.rent_cost)
        st.session_state.other_cost = st.number_input("기타 지출", value=st.session_state.other_cost)

# [4. 알림 페이지] - 새로 추가된 전용 칸!
elif menu_choice == "🔔알림":
    st.subheader("결제 예정 및 일정 관리")
    
    # 미납 알림 (가장 위로 배치)
    st.write("**🔔 결제 알림 (D-5)**")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    if not alerts.empty:
        st.dataframe(alerts[['Name', 'Class', 'D-Day']], use_container_width=True, height=200)
    else:
        st.success("현재 결제 예정 학생이 없습니다.")
    
    st.divider()
    
    # 일정 연장 (별도 섹션)
    with st.expander("🗓️ 일정 연장 (휴강/보강)", expanded=True):
        target_s = st.selectbox("학생 선택", current_df['Name'].tolist())
        days = st.number_input("연장 일수", value=1, min_value=1)
        if st.button("연장 적용"):
            idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
            st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=days)
            st.rerun()