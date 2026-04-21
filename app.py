import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import numpy as np

# 1. 앱 설정 및 모바일 최적화
st.set_page_config(page_title="송수학", layout="centered")

# 2. 프리미엄 디자인 (CSS) - 네이비 & 화이트 테마
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    
    /* 7칸 가로 메뉴 바 디자인 */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 4px;
        border: 1px solid #E0E0E0;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
    }
    div[data-testid="stRadio"] label {
        flex: 1; text-align: center; padding: 10px 1px !important;
        margin: 0 1px !important; font-size: 11px !important;
        font-weight: 700; color: #444; transition: all 0.2s ease;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: #002B5B !important;
        border-radius: 8px; color: white !important;
    }
    div[data-testid="stRadio"] input { display: none; }

    /* UI 요소 다듬기 */
    h1 { color: #002B5B; font-size: 1.6rem !important; font-weight: 800 !important; text-align: center; }
    [data-testid="stMetric"] { background-color: white; padding: 15px; border-radius: 12px; box-shadow: 0px 2px 8px rgba(0,0,0,0.05); }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 오프라인 파일 저장 시스템 (CSV) ---
DB_FILE = "students.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Class", "Last Payment"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if 'student_data' not in st.session_state:
    st.session_state.student_data = load_data()

# 설정값 유지
settings = {'rent': 800000, 'other': 300000, 'f17': 300000, 'f19': 350000, 'f21': 400000}
for k, v in settings.items():
    if k not in st.session_state: st.session_state[k] = v

def get_processed_df():
    df = st.session_state.student_data.copy()
    if df.empty: return pd.DataFrame(columns=['Name', 'Class', 'Last Payment', 'Next Due', 'D-Day'])
    df['Last Payment'] = pd.to_datetime(df['Last Payment']).dt.date
    df['Next Due'] = df['Last Payment'] + timedelta(days=30)
    df['D-Day'] = (df['Next Due'] - datetime.now().date()).apply(lambda x: x.days)
    return df

# --- 메인 인터페이스 시작 ---
st.title("🏫 송수학 통합 관리")

menu = st.radio(
    "메뉴", 
    ["📍현황", "👤관리", "💰수익", "🛠️지출", "🔔알림", "🗓️연장", "⚙️기타"], 
    horizontal=True, label_visibility="collapsed"
)

st.divider()
current_df = get_processed_df()

# [1. 현황]
if menu == "📍현황":
    target = st.selectbox("반", ["17:00", "19:00", "21:00"], label_visibility="collapsed")
    filtered = current_df[current_df['Class'].astype(str).str.contains(target, na=False)]
    st.markdown(f"현재 인원: **{len(filtered)}명**")
    st.dataframe(filtered[['Name', 'Next Due', 'D-Day']], use_container_width=True, height=350)

# [2. 관리] - 등록 및 삭제 확인 알림 강화
elif menu == "👤관리":
    sub1, sub2 = st.tabs(["➕등록", "❌퇴원"])
    with sub1:
        with st.form("add_form", clear_on_submit=True):
            n_class = st.selectbox("반 선택", ["17:00", "19:00", "21:00"])
            n_name = st.text_input("학생 이름 입력")
            if st.form_submit_button("등록 완료"):
                if n_name:
                    new_row = pd.DataFrame([{"Name": n_name, "Class": n_class, "Last Payment": datetime.now().date()}])
                    st.session_state.student_data = pd.concat([st.session_state.student_data, new_row], ignore_index=True)
                    save_data(st.session_state.student_data)
                    # 알림 콤보!
                    st.success(f"✅ {n_name} 학생이 [{n_class}] 반에 등록되었습니다!")
                    st.toast(f"{n_name} 등록 완료! 🎉")
                else:
                    st.error("이름을 입력해주세요.")
    with sub2:
        del_target = st.selectbox("삭제 대상 선택", [""] + current_df['Name'].tolist())
        if st.button("학생 삭제 수행"):
            if del_target:
                st.session_state.student_data = st.session_state.student_data[st.session_state.student_data['Name'] != del_target]
                save_data(st.session_state.student_data)
                # 삭제 알림
                st.warning(f"🗑️ {del_target} 학생 정보가 삭제되었습니다.")
                st.toast(f"{del_target} 삭제 완료")
                st.rerun()

# [3. 수익]
elif menu == "💰수익":
    r17 = len(current_df[current_df['Class'] == "17:00"]) * st.session_state.f17
    r19 = len(current_df[current_df['Class'] == "19:00"]) * st.session_state.f19
    r21 = len(current_df[current_df['Class'] == "21:00"]) * st.session_state.f21
    total_rev = r17 + r19 + r21
    st.metric("이번 달 총 매출", f"{total_rev:,.0f}원")
    st.metric("이번 달 순수익", f"{total_rev - (st.session_state.rent + st.session_state.other):,.0f}원")

# [4. 지출] - 설정 저장 확인 알림 추가
elif menu == "🛠️지출":
    st.write("**[단가 및 고정비 설정]**")
    st.session_state.f17 = st.number_input("고1 수강료", value=st.session_state.f17, step=10000)
    st.session_state.f19 = st.number_input("고2 수강료", value=st.session_state.f19, step=10000)
    st.session_state.f21 = st.number_input("고3 수강료", value=st.session_state.f21, step=10000)
    st.session_state.rent = st.number_input("월세", value=st.session_state.rent, step=10000)
    st.session_state.other = st.number_input("기타 지출", value=st.session_state.other, step=5000)
    if st.button("수정 내용 저장"):
        st.success("✅ 지출 및 단가 설정이 저장되었습니다!")
        st.toast("설정 저장 완료 ⚙️")

# [5. 알림]
elif menu == "🔔알림":
    st.subheader("결제 알림 (D-5)")
    alerts = current_df[current_df['D-Day'] <= 5].sort_values('D-Day')
    if not alerts.empty:
        st.dataframe(alerts[['Name', 'Class', 'D-Day']], use_container_width=True, height=350)
    else:
        st.success("결제 예정 학생이 없습니다.")

# [6. 연장] - 기한 조정 확인 알림 강화
elif menu == "🗓️연장":
    st.subheader("결제 기한 조정 (+/-)")
    target_s = st.selectbox("학생 선택", current_df['Name'].tolist())
    adjust_days = st.number_input("조정 일수 (양수:연장 / 음수:단축)", value=0, step=1)
    if st.button("조정 사항 적용"):
        if target_s:
            idx = st.session_state.student_data.index[st.session_state.student_data['Name'] == target_s][0]
            curr_date = pd.to_datetime(st.session_state.student_data.at[idx, 'Last Payment']).date()
            new_date = curr_date + timedelta(days=adjust_days)
            st.session_state.student_data.at[idx, 'Last Payment'] = str(new_date)
            save_data(st.session_state.student_data)
            # 연장/단축 결과 알림
            msg = f"{abs(adjust_days)}일 연장" if adjust_days >= 0 else f"{abs(adjust_days)}일 단축"
            st.success(f"🗓️ {target_s} 학생 기한이 {msg}되었습니다.")
            st.toast(f"{target_s} 조정 완료 ✨")
            st.rerun()

# [7. 기타] - 백업 확인 알림 추가
elif menu == "⚙️기타":
    st.subheader("⚙️ 백업 및 관리")
    csv_data = st.session_state.student_data.to_csv(index=False).encode('utf-8-sig')
    if st.download_button(
        label="📥 현재 명단 다운로드 (CSV)",
        data=csv_data,
        file_name=f"songmath_backup_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    ):
        st.toast("파일 다운로드 시작!")