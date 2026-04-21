import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. 앱 설정
st.set_page_config(page_title="송수학 관리", layout="centered")

# 2. 커스텀 디자인 (CSS)
# 라디오 버튼을 가로형 '하나의 큰 바'처럼 보이게 개조합니다.
st.markdown("""
    <style>
    /* 1. 라디오 버튼 그룹을 가로로 길게 배치 */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #f0f2f6;
        border-radius: 12px;
        padding: 5px;
        border: 1px solid #d1d5db;
    }
    
    /* 2. 각 라디오 버튼 항목을 하나의 칸처럼 디자인 */
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

    /* 3. 선택된 항목만 흰색 배경으로 강조 (버튼 느낌) */
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: white !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        color: #007BFF;
    }

    /* 4. 기존 라디오 동그라미 숨기기 */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        font-size: 14px;
    }
    div[data-testid="stRadio"] input {
        display: none;
    }

    /* 5. 스크롤 에러 방지: 강제 고정 대신 자연스러운 흐름 */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 초기화
if 'student_data' not in st.session_state:
    today = datetime.now().date()
    st.session_state.student_data = pd.DataFrame([
        {"Name": "김철수", "Class": "17:00 (고1)", "Last Payment": today - timedelta(days=10)},
        {"Name": "이영희", "Class": "19:00 (고2)", "Last Payment": today - timedelta(days=5)}
    ])

# 데이터 처리 함수
def get_processed_df():
    df = st.session_state.student_data.copy()
    if df.empty:
        return pd.DataFrame(columns=['Name', 'Class', 'Last Payment', 'Next Due', 'D-Day'])
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 인터페이스 ---
st.title("🏫 송수학 통합 관리")

# 4. '하나의 바' 형태의 가로 메뉴 (라디오 버튼 개조)
# 이 부분이 선용님이 말씀하신 "칸만 나눈 가로 버튼" 역할을 합니다.
menu_choice = st.radio(
    "메뉴 선택", 
    ["📍현황", "👤관리", "💰회계"], 
    horizontal=True,
    label_visibility="collapsed" # 제목은 숨기고 버튼만 노출
)

st.divider()

current_df = get_processed_df()

# --- 5. 페이지 전환 로직 ---

if menu_choice == "📍현황":
    st.subheader("타임별 인원 현황")
    target_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
    filtered = current_df[current_df['Class'] == target_class]
    st.write(f"현재 인원: **{len(filtered)}명**")
    # 표 높이를 적절히 조절하여 화면 밖으로 나가지 않게 함
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=250)

elif menu_choice == "👤관리":
    st.subheader("원생 등록 및 삭제")
    tab1, tab2 = st.tabs(["➕ 등록", "❌ 퇴원"])
    
    with tab1:
        with st.form("add_form", clear_on_submit=True):
            n_name = st.text_input("학생 성함")
            n_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
            if st.form_submit_button("등록 하기"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    st.rerun()
    
    with tab2:
        del_target = st.selectbox("삭제 대상", [""] + current_df['Name'].tolist())
        if st.button("원생 정보 삭제"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                st.rerun()

elif menu_choice == "💰회계":
    st.subheader("회계 관리")
    c1, c2 = st.columns(2)
    total_rev = len(current_df) * 300000
    c1.metric("월 수익 (예상)", f"{total_rev - 1100000:,.0f}원")
    c2.metric("총 인원", f"{len(current_df)}명")
    
    st.divider()
    
    # 일정 연장 기능 (자주 쓰시니 여기에 추가)
    with st.expander("🗓️ 결제 기간 연장"):
        target_s = st.selectbox("학생 선택", current_df['Name'].tolist())
        days = st.number_input("연장 일수", value=1, min_value=1)
        if st.button("연장 적용"):
            idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
            st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=days)
            st.success("완료!")
            st.rerun()

    st.write("**🔔 결제 알림 (D-5)**")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    st.dataframe(alerts[['Name', 'D-Day']], use_container_width=True, height=150)