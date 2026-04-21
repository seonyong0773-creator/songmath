import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 1. 앱 기본 설정 및 모바일 최적화 레이아웃
st.set_page_config(page_title="송수학 관리앱", layout="centered")

# 2. 커스텀 디자인 (CSS) - 버튼 크기 키우기 및 새로고침 방지
st.markdown("""
    <style>
    /* 상단 메뉴 버튼 스타일 */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 4em;
        background-color: #f8f9fa;
        border: 2px solid #e9ecef;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        border-color: #007BFF;
        color: #007BFF;
    }
    
    /* 모바일 당겨서 새로고침 방지 및 스크롤 최적화 */
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: none !important;
        -webkit-overflow-scrolling: touch;
    }

    /* 탭 메뉴 강조 표시용 (임시) */
    .st-emotion-cache-12w0qpk {
        padding-top: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 초기화 및 상태 관리
if 'student_data' not in st.session_state:
    # 초기 샘플 데이터 생성
    today = datetime.now().date()
    names = ["김철수", "이영희", "박지민", "최하늘", "정민수", "강다은", "조세호", "윤서아", "한가람", "임재현"]
    classes = ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"]
    data = []
    for i, name in enumerate(names):
        data.append({
            "Name": name,
            "Class": classes[i % 3],
            "Last Payment": today - timedelta(days=np.random.randint(0, 30))
        })
    st.session_state.student_data = pd.DataFrame(data)

if 'current_page' not in st.session_state:
    st.session_state.current_page = "📍 현황"

# 상수 설정
RENT, UTILITY, FEE = 800000, 300000, 300000

# 데이터 처리 함수
def get_processed_df():
    df = st.session_state.student_data.copy()
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['Days Left'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 화면 시작 ---
st.title("🏫 송수학 통합 관리")

# 4. 상단 네비게이션 버튼 (엘리베이터 버튼 방식)
m1, m2, m3 = st.columns(3)
with m1:
    if st.button("📍 현황"):
        st.session_state.current_page = "📍 현황"
with m2:
    if st.button("👤 관리"):
        st.session_state.current_page = "👤 관리"
with m3:
    if st.button("💰 회계"):
        st.session_state.current_page = "💰 회계"

st.divider()
df_main = get_processed_df()

# 5. 페이지별 화면 렌더링
# --- [페이지 1: 인원 현황] ---
if st.session_state.current_page == "📍 현황":
    st.subheader("타임별 수강 현황")
    for t in ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"]:
        with st.expander(f"📌 {t} 원생 목록", expanded=(t == "17:00 (고1)")):
            filtered = df_main[df_main['Class'] == t]
            st.write(f"현재 인원: **{len(filtered)}명**")
            if not filtered.empty:
                st.table(filtered[['Name', 'Next Due']])
            else:
                st.write("등록된 원생이 없습니다.")

# --- [페이지 2: 원생 관리] ---
elif st.session_state.current_page == "👤 관리":
    st.subheader("원생 등록 및 퇴원")
    
    # 원생 추가 폼
    with st.form("add_student", clear_on_submit=True):
        st.write("**➕ 신규 원생 등록**")
        n_name = st.text_input("이름")
        n_class = st.selectbox("반 선택", ["17:00 (고1)", "19:00 (고2)", "21:00 (고3)"])
        if st.form_submit_button("등록 완료"):
            if n_name:
                new_row = {"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}
                st.session_state.student_data = pd.concat([st.session_state.student_data, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"{n_name} 학생이 등록되었습니다.")
                st.rerun()
            else:
                st.error("이름을 입력해주세요.")

    st.divider()

    # 원생 삭제
    st.write("**❌ 퇴원 처리**")
    del_target = st.selectbox("삭제할 학생 선택", [""] + df_main['Name'].tolist())
    if st.button("선택한 학생 영구 삭제"):
        if del_target:
            st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
            st.warning(f"{del_target} 학생이 삭제되었습니다.")
            st.rerun()

# --- [페이지 3: 회계 및 연장] ---
elif st.session_state.current_page == "💰 회계":
    st.subheader("회계 및 일정 관리")
    
    # 결제일 연장
    st.write("**🗓️ 개인 사정/휴강 일수 연장**")
    target_s = st.selectbox("연장 대상 학생", df_main['Name'].tolist())
    add_days = st.number_input("추가할 일수", value=1, min_value=1)
    if st.button("연장 적용하기"):
        idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
        st.session_state.student_data.at[idx, 'Last Payment'] += timedelta(days=add_days)
        st.success(f"{target_s} 학생의 결제일이 {add_days}일 연장되었습니다.")
        st.rerun()

    st.divider()

    # 수익 지표
    col_rev, col_exp = st.columns(2)
    total_revenue = len(df_main) * FEE
    with col_rev:
        st.metric("예상 월 매출", f"{total_revenue:,.0f}원")
    with col_exp:
        net_profit = total_revenue - (RENT + UTILITY)
        st.metric("예상 순수익", f"{net_profit:,.0f}원", delta=f"지출 {RENT+UTILITY:,.0f}원", delta_color="inverse")

    # 미납 알림
    st.write("**🔔 결제 임박 알림 (5일 이내)**")
    alerts = df_main[df_main['Days Left'] <= 5].sort_values('Days Left')
    if not alerts.empty:
        for _, row in alerts.iterrows():
            c = "red" if row['Days Left'] < 0 else "orange"
            st.markdown(f":{c}[[{row['Class']}] {row['Name']} : {row['Days Left']}일 남음]")
    else:
        st.write("현재 결제 임박 원생이 없습니다.")