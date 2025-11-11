# streamlit_app.py
import os
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
    precision_recall_curve,
)

# ---------------------- 환경 변수 / 엔진 ----------------------
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "1234")
DB_NAME = os.getenv("DB_NAME", "tipsdb")
URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(URL, pool_pre_ping=True)

# ---------------------- Streamlit 기본 설정 ----------------------
st.set_page_config(page_title="Tips ML Dashboard", layout="wide")

# 데이터 버전 키(캐시 무효화용)
if "ver" not in st.session_state:
    st.session_state["ver"] = 0

# ---------------------- DB 유틸 ----------------------
@st.cache_data(ttl=0, show_spinner=False)
def load_tips(ver: int) -> pd.DataFrame:
    """ver를 키로 받아 캐시를 제어한다."""
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM tips", conn)
    return df

def insert_row(row: dict) -> None:
    """tips에 신규행 삽입 + 감사 로그 기록"""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO tips (total_bill, tip, sex, smoker, day, time, size, source)
                VALUES (:total_bill, :tip, :sex, :smoker, :day, :time, :size, 'manual')
                """
            ),
            row,
        )
        tips_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        conn.execute(
            text(
                "INSERT INTO tips_audit (tips_id, source) VALUES (:tips_id, 'manual')"
            ),
            {"tips_id": tips_id},
        )
    # 간헐적 최신화 지연 방지
    engine.dispose()

# ---------------------- 모델 유틸 ----------------------
def train_eval(df, eval_mode: str = "holdout", seed: int = 42):
    """
    eval_mode:
      - 'holdout' : 20% 테스트셋으로 평가 (현재 방식)
      - 'all'     : 전체 데이터로 학습 후, 전체 데이터에 대해 예측/평가(표 수치가 데이터 수 증가만큼 즉시 변함)
                    ※ 통계적으로 관대(낙관적)한 평가임을 UI에 표시하세요.
    """
    y = df["time"].astype(str).values
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    X = df[["tip", "size"]].astype(float).values

    if eval_mode == "all":
        model = LogisticRegression(max_iter=500)
        model.fit(X, y_enc)
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)[:, 1]
        cm = confusion_matrix(y_enc, y_pred)
        report = classification_report(y_enc, y_pred, target_names=list(le.classes_), output_dict=True)
        fpr, tpr, _ = roc_curve(y_enc, y_proba); roc_auc = auc(fpr, tpr)
        prec, rec, _ = precision_recall_curve(y_enc, y_proba)
        sizes = {"train": len(df), "test": len(df)}  # 표기용
        return {"model": model,"le": le,"cm": cm,"report": report,"classes": list(le.classes_),
                "roc": (fpr, tpr, roc_auc),"pr": (prec, rec),"sizes": sizes}

    # holdout (기본)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y_enc, test_size=0.2, random_state=seed, stratify=y_enc
    )
    model = LogisticRegression(max_iter=500)
    model.fit(Xtr, ytr)
    y_pred = model.predict(Xte)
    y_proba = model.predict_proba(Xte)[:, 1]
    cm = confusion_matrix(yte, y_pred)
    report = classification_report(yte, y_pred, target_names=list(le.classes_), output_dict=True)
    fpr, tpr, _ = roc_curve(yte, y_proba); roc_auc = auc(fpr, tpr)
    prec, rec, _ = precision_recall_curve(yte, y_proba)
    sizes = {"train": len(ytr), "test": len(yte)}
    return {"model": model,"le": le,"cm": cm,"report": report,"classes": list(le.classes_),
            "roc": (fpr, tpr, roc_auc),"pr": (prec, rec),"sizes": sizes}


def infer_new_and_merge(df: pd.DataFrame, model, le):
    """
    - source == 'manual' 신규행만 예측
    - 신규행: y_pred_label / y_pred_proba / correct 컬럼 추가
    - 전체 df: 신규행 위치에만 예측 컬럼 채워 결합본 반환
    """
    full = df.copy()
    new_mask = full["source"] == "manual"
    new_df = full.loc[new_mask, ["id", "tip", "size", "time"]].copy()

    full["y_pred_label"] = np.nan
    full["y_pred_proba"] = np.nan
    full["correct"] = np.nan

    if new_df.empty:
        return full, new_df.assign(
            y_pred_label=[], y_pred_proba=[], correct=[]
        )

    X_new = new_df[["tip", "size"]].astype(float).values
    y_pred_idx = model.predict(X_new)
    y_pred_label = le.inverse_transform(y_pred_idx)
    y_pred_proba = model.predict_proba(X_new).max(axis=1)

    new_df["y_pred_label"] = y_pred_label
    new_df["y_pred_proba"] = y_pred_proba
    new_df["correct"] = (new_df["time"].astype(str).values == y_pred_label).astype(int)

    full.loc[new_mask, "y_pred_label"] = new_df["y_pred_label"].values
    full.loc[new_mask, "y_pred_proba"] = new_df["y_pred_proba"].values
    full.loc[new_mask, "correct"] = new_df["correct"].values

    return full, new_df

# ---------------------- 페이지 구성 ----------------------
page = st.sidebar.radio("Pages", ["Model Dashboard", "Full Data Dashboard"])

# 공통: 최신 데이터 로드
df = load_tips(st.session_state["ver"])

if page == "Model Dashboard":
    st.title("🔁 Tips ML — Model Dashboard")

    # KPI
    total = int(len(df))
    initial = int((df["source"] == "initial").sum()) if "source" in df.columns else 0
    manual = int((df["source"] == "manual").sum()) if "source" in df.columns else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total rows", value=total)
    c2.metric("Initial rows", value=initial)
    c3.metric("New rows (manual)", value=manual)

    # 신규 입력 + 재학습
    with st.expander("➕ Add New Row & Retrain"):
        with st.form("add_row"):
            total_bill = st.number_input("total_bill", min_value=0.0, value=20.0, step=0.5)
            tip = st.number_input("tip", min_value=0.0, value=3.0, step=0.5)
            sex = st.selectbox("sex", ["Male", "Female"])
            smoker = st.selectbox("smoker", ["Yes", "No"])
            day = st.selectbox("day", ["Thur", "Fri", "Sat", "Sun"])
            time_val = st.selectbox("time (target)", ["Lunch", "Dinner"])
            size = st.number_input("size", min_value=1, value=2, step=1)

            submitted = st.form_submit_button("Insert & Retrain")
            if submitted:
                insert_row(
                    {
                        "total_bill": float(total_bill),
                        "tip": float(tip),
                        "sex": sex,
                        "smoker": smoker,
                        "day": day,
                        "time": time_val,
                        "size": int(size),
                    }
                )
                st.session_state["ver"] += 1   # 캐시 키 증가
                st.cache_data.clear()          # 캐시 무효화
                st.success("Inserted! Retraining with fresh data...")
                st.rerun()                     # 즉시 전체 재실행

    # 재로딩된 최신 데이터로 학습/평가
    df = load_tips(st.session_state["ver"])
    try:
        # 평가 모드 선택 (Hold-out vs All)
        eval_mode = st.radio("Evaluation mode", ["holdout", "all"], horizontal=True,
                            help="holdout: 20% 테스트셋 평가 / all: 전체 데이터로 평가(표 숫자 증가가 즉시 반영)")

        # 새 데이터 추가 시 분할도 바뀌도록 seed에 ver 반영
        seed = 42 + st.session_state["ver"]

        out = train_eval(df, eval_mode=eval_mode, seed=seed)
        cm = out["cm"]; classes = out["classes"]; report = out["report"]
        fpr, tpr, roc_auc = out["roc"]; prec, rec = out["pr"]
        sizes = out.get("sizes", {})
        st.caption(f"Train size: {sizes.get('train','?')}  |  Test size: {sizes.get('test','?')}  |  Mode: {eval_mode}")

        # 혼동행렬
        st.subheader("📦 Confusion Matrix")
        cm_df = pd.DataFrame(
            cm,
            index=[f"True {c}" for c in classes],
            columns=[f"Pred {c}" for c in classes],
        )
        st.table(cm_df)

        # 분류 리포트
        st.subheader("📑 Classification Report")
        rep_df = pd.DataFrame(report).T
        st.dataframe(rep_df, use_container_width=True)

        # ROC / PR
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader(f"📈 ROC Curve (AUC={roc_auc:.3f})")
            roc_df = pd.DataFrame({"FPR": fpr, "TPR": tpr}).set_index("FPR")
            st.line_chart(roc_df)
        with col_b:
            st.subheader("📈 Precision-Recall Curve")
            pr_df = pd.DataFrame({"Recall": rec, "Precision": prec}).set_index("Recall")
            st.line_chart(pr_df)

        # 신규행 예측 + 결합본 + 다운로드
        st.subheader("🧩 Predictions for NEW rows (source='manual')")
        combined_df, new_pred_df = infer_new_and_merge(df, out["model"], out["le"])

        if new_pred_df.empty:
            st.info("아직 신규 데이터(source='manual')가 없습니다. 폼으로 추가해 보세요.")
        else:
            left, right = st.columns(2)
            with left:
                st.markdown("**New rows with predictions**")
                view_new = new_pred_df[
                    ["id", "tip", "size", "time", "y_pred_label", "y_pred_proba", "correct"]
                ]
                st.dataframe(view_new, use_container_width=True)
                csv_new = new_pred_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇️ Download NEW predictions (CSV)",
                    data=csv_new,
                    file_name="new_rows_predictions.csv",
                    mime="text/csv",
                )
            with right:
                st.markdown("**Combined data (existing + predicted columns on new rows)**")
                cols = [
                    "id","total_bill","tip","size","sex","smoker","day","time","source",
                    "y_pred_label","y_pred_proba","correct",
                ]
                cols = [c for c in cols if c in combined_df.columns]
                st.dataframe(combined_df[cols], use_container_width=True)

    except Exception as e:
        st.error(f"Training failed: {e}")

elif page == "Full Data Dashboard":
    st.title("📊 Full Data Dashboard")
    # 간단 필터
    dfx = df.copy()
    c1, c2 = st.columns(2)
    with c1:
        day_opts = sorted(dfx["day"].dropna().unique()) if "day" in dfx.columns else []
        day_sel = st.multiselect("day", options=day_opts, default=day_opts)
    with c2:
        time_opts = sorted(dfx["time"].dropna().unique()) if "time" in dfx.columns else []
        time_sel = st.multiselect("time", options=time_opts, default=time_opts)

    if day_opts and time_opts:
        dfx = dfx[dfx["day"].isin(day_sel) & dfx["time"].isin(time_sel)]
    st.write(f"Total rows: **{len(dfx)}**")
    st.dataframe(dfx, use_container_width=True)
