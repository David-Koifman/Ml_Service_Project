import os
import time
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

API = os.getenv("API_URL", "http://api:8000")
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL) if DATABASE_URL else None

st.set_page_config(page_title="ML Loan Service", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #e0e0e0 !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 2px; }
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 8px 12px;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(99,102,241,0.25);
    border-color: rgba(99,102,241,0.4);
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1); }
[data-testid="stSidebar"] .stMetric { background: rgba(255,255,255,0.07); border-radius: 10px; padding: 8px 12px; }
[data-testid="stSidebar"] .stMetric label { font-size: 11px !important; opacity: 0.7; }
[data-testid="stSidebar"] .stMetric [data-testid="metric-container"] { background: transparent !important; border: none !important; padding: 0 !important; }

/* ── Main background ── */
.stApp { background: #f0f2f6; }
.block-container { padding-top: 1.5rem; }

/* ── Metric cards ── */
div[data-testid="metric-container"] {
    background: white;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border-top: 3px solid #6366f1;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.15);
}
div[data-testid="metric-container"] label {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="metric-container"] [data-testid="metric-value"] {
    font-size: 1.8rem;
    font-weight: 700;
    color: #111827;
}

/* ── Page titles ── */
h1 { color: #4f46e5; font-weight: 700; font-size: 2rem; margin-bottom: 0.5rem; }
h2, h3 { color: #1f2937; font-weight: 600; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #e5e7eb;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    color: #6b7280;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
}

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    border-radius: 10px;
    font-weight: 600;
    letter-spacing: 0.02em;
    transition: all 0.2s ease;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3);
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.45);
}
.stButton > button[kind="secondary"] {
    border-radius: 8px;
    border-color: #d1d5db;
    color: #374151;
    transition: all 0.15s;
}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input,
.stTextInput > div > div > input,
.stPasswordInput input {
    background: white !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 15px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput input:focus, .stNumberInput input:focus,
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Tabs — fix active state ── */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid #e5e7eb;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-size: 15px;
    font-weight: 500;
    color: #6b7280 !important;
    background: transparent !important;
    border: none !important;
    padding: 8px 20px !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Containers / Cards ── */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > [data-testid="element-container"] > div[data-baseweb="notification"],
.stAlert {
    border-radius: 10px;
}
[data-testid="stExpander"],
[data-testid="stForm"] {
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

/* ── DataTable ── */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── Divider ── */
hr { border-color: #e5e7eb; }

/* ── Auth page card ── */
.auth-card {
    background: white;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
}
.auth-logo {
    text-align: center;
    margin-bottom: 24px;
}
.auth-logo h2 {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
}
.auth-logo p { color: #6b7280; margin: 4px 0 0; font-size: 14px; }

/* ── Result card ── */
.result-approved {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    animation: fadeIn 0.5s ease;
}
.result-rejected {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border: 2px solid #ef4444;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    animation: fadeIn 0.5s ease;
}
.result-title { font-size: 1.5rem; font-weight: 800; margin: 0; }
.result-approved .result-title { color: #065f46; }
.result-rejected .result-title { color: #991b1b; }

/* ── Stat badge ── */
.stat-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.badge-done   { background: #d1fae5; color: #065f46; }
.badge-failed { background: #fee2e2; color: #991b1b; }
.badge-pending { background: #fef3c7; color: #92400e; }

/* ── Sidebar brand ── */
.sidebar-brand {
    text-align: center;
    padding: 16px 0 8px;
}
.sidebar-brand h3 {
    color: #a5b4fc !important;
    font-size: 1.2rem;
    font-weight: 700;
    margin: 0;
}
.sidebar-brand p {
    color: rgba(255,255,255,0.55) !important;
    font-size: 12px;
    margin: 4px 0 0;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-green {
    0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }
    50%       { box-shadow: 0 0 0 8px rgba(16,185,129,0); }
}
</style>
""", unsafe_allow_html=True)


# ── helpers ──────────────────────────────────────────────
_MODEL_NAMES = {
    "loan model":   "Кредитный скоринг",
    "loan_model":   "Кредитный скоринг",
    "credit model": "Кредитный скоринг",
    "model v1":     "Кредитный скоринг v1",
    "model v2":     "Кредитный скоринг v2",
}

def fmt_model(name: str) -> str:
    return _MODEL_NAMES.get(name.lower(), name.replace("_", " ").replace("-", " ").title())


def api(method, path, token=None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = getattr(requests, method)(f"{API}{path}", headers=headers, timeout=10, **kwargs)
        return r
    except Exception as e:
        st.error(f"Нет связи с API: {e}")
        return None


def db(query):
    if not engine:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    except Exception:
        return pd.DataFrame()


def logout():
    for k in ["token", "user", "role", "page"]:
        st.session_state.pop(k, None)
    st.query_params.clear()


def restore_session():
    if "token" not in st.session_state and "token" in st.query_params:
        token = st.query_params["token"]
        me = api("get", "/users/me", token=token)
        if me and me.status_code == 200:
            u = me.json()
            st.session_state.token = token
            st.session_state.user  = u["email"]
            st.session_state.role  = u["role"]
            if "page" in st.query_params:
                st.session_state["_restored_page"] = st.query_params["page"]


# ── landing page ─────────────────────────────────────────
def page_landing():
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important; }
    .block-container { padding-top: 0 !important; max-width: 860px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:72px 0 48px">
        <div style="display:inline-flex;align-items:center;justify-content:center;
                    width:72px;height:72px;border-radius:20px;margin-bottom:24px;
                    background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    font-size:34px;font-weight:800;color:white;
                    box-shadow:0 8px 32px rgba(99,102,241,0.5)">M</div>
        <h1 style="color:white;font-size:3rem;font-weight:800;margin:0;line-height:1.1">
            ML Loan Service
        </h1>
        <p style="color:rgba(255,255,255,0.6);font-size:1.1rem;margin:16px 0 0">
            Скоринг кредитных заявок на основе машинного обучения.<br>
            Результат за секунды — точность модели <strong style="color:#a5b4fc">93%</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    features = [
        ("93%", "Точность модели", "GradientBoosting на 58k реальных заявок", "#6366f1"),
        ("<2 сек", "Время ответа", "Асинхронная обработка через Celery + Redis", "#8b5cf6"),
        ("10 кр.", "Цена запроса", "Платите только за результат, без подписки", "#06b6d4"),
    ]
    for col, (val, title, desc, color) in zip([f1, f2, f3], features):
        col.markdown(f"""
        <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
                    border-radius:16px;padding:24px;text-align:center;
                    transition:transform 0.2s">
            <div style="font-size:2rem;font-weight:800;color:{color}">{val}</div>
            <div style="font-weight:600;color:white;margin:8px 0 6px;font-size:15px">{title}</div>
            <div style="color:rgba(255,255,255,0.5);font-size:13px;line-height:1.4">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                border-radius:16px;padding:28px 32px;margin-bottom:32px">
        <div style="font-weight:700;color:white;font-size:15px;margin-bottom:16px">
            Как это работает
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px">
            <div style="text-align:center">
                <div style="width:36px;height:36px;border-radius:50%;background:#6366f1;
                            color:white;font-weight:700;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 8px;font-size:14px">1</div>
                <div style="color:rgba(255,255,255,0.7);font-size:13px">Регистрация и<br>получение 100 кредитов</div>
            </div>
            <div style="text-align:center">
                <div style="width:36px;height:36px;border-radius:50%;background:#7c3aed;
                            color:white;font-weight:700;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 8px;font-size:14px">2</div>
                <div style="color:rgba(255,255,255,0.7);font-size:13px">Вводите данные<br>заёмщика</div>
            </div>
            <div style="text-align:center">
                <div style="width:36px;height:36px;border-radius:50%;background:#8b5cf6;
                            color:white;font-weight:700;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 8px;font-size:14px">3</div>
                <div style="color:rgba(255,255,255,0.7);font-size:13px">ML-модель<br>анализирует заявку</div>
            </div>
            <div style="text-align:center">
                <div style="width:36px;height:36px;border-radius:50%;background:#06b6d4;
                            color:white;font-weight:700;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 8px;font-size:14px">4</div>
                <div style="color:rgba(255,255,255,0.7);font-size:13px">Решение:<br>одобрено / отказано</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bc1, bc2, bc3, bc4 = st.columns([1.2, 1, 1, 1.2])
    with bc2:
        if st.button("Войти", use_container_width=True):
            st.session_state.show_auth = True
            st.session_state.auth_tab  = "login"
            st.rerun()
    with bc3:
        if st.button("Регистрация", use_container_width=True, type="primary"):
            st.session_state.show_auth = True
            st.session_state.auth_tab  = "register"
            st.rerun()
    st.markdown("""
    <p style="text-align:center;color:rgba(255,255,255,0.35);font-size:12px;margin-top:12px">
        При регистрации — 100 бесплатных кредитов
    </p>
    """, unsafe_allow_html=True)


# ── auth pages ────────────────────────────────────────────
def page_auth():
    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "login"

    col = st.columns([1, 1.2, 1])[1]
    with col:
        if st.session_state.get("reg_success"):
            st.success("Аккаунт создан! Войдите со своими данными.")
            st.session_state.pop("reg_success", None)
        if st.button("← На главную"):
            st.session_state.pop("show_auth", None)
            st.session_state.pop("auth_tab", None)
            st.rerun()

        st.markdown("""
        <div style="text-align:center;padding:32px 0 24px">
            <div style="display:inline-flex;align-items:center;justify-content:center;
                        width:56px;height:56px;border-radius:16px;margin-bottom:16px;
                        background:linear-gradient(135deg,#6366f1,#8b5cf6);
                        font-size:26px;color:white;font-weight:800">M</div>
            <div style="font-size:1.9rem;font-weight:800;color:#1f2937;line-height:1.1">ML Loan Service</div>
            <p style="color:#6b7280;margin:8px 0 0;font-size:14px">Платформа предсказания кредитных заявок</p>
        </div>
        """, unsafe_allow_html=True)

        # custom tab switcher
        t1, t2 = st.columns(2)
        active = st.session_state.auth_tab
        t1_type = "primary" if active == "login"    else "secondary"
        t2_type = "primary" if active == "register" else "secondary"
        if t1.button("Войти",          use_container_width=True, type=t1_type, key="tab_btn_login"):
            st.session_state.auth_tab = "login"
            st.rerun()
        if t2.button("Регистрация",    use_container_width=True, type=t2_type, key="tab_btn_reg"):
            st.session_state.auth_tab = "register"
            st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.session_state.auth_tab == "login":
            email = st.text_input("Email", key="li_email")
            pwd   = st.text_input("Пароль", type="password", key="li_pwd")
            if st.button("Войти", use_container_width=True, type="primary", key="do_login"):
                r = api("post", "/auth/login", data={"username": email, "password": pwd})
                if r and r.status_code == 200:
                    token = r.json()["access_token"]
                    me = api("get", "/users/me", token=token)
                    if me and me.status_code == 200:
                        u = me.json()
                        st.session_state.token = token
                        st.session_state.user  = u["email"]
                        st.session_state.role  = u["role"]
                        st.query_params.clear()
                        st.query_params["token"] = token
                        st.rerun()
                else:
                    st.error("Неверный email или пароль")
        else:
            r_email = st.text_input("Email", key="reg_email")
            r_pwd   = st.text_input("Пароль (мин. 6 символов)", type="password", key="reg_pwd", placeholder="Введите пароль вручную")
            if st.button("Зарегистрироваться", use_container_width=True, type="primary", key="do_reg"):
                if not r_email or not r_pwd:
                    st.error("Заполните все поля")
                elif len(r_pwd) < 6:
                    st.error("Пароль должен быть минимум 6 символов")
                else:
                    r = api("post", "/auth/register", json={"email": r_email, "password": r_pwd})
                    if r and r.status_code == 201:
                        st.session_state.reg_success = True
                        st.session_state.auth_tab = "login"
                        st.rerun()
                    elif r:
                        detail = r.json().get("detail", "Ошибка")
                        if "already" in str(detail):
                            st.error("Этот email уже зарегистрирован")
                        else:
                            st.error(detail)


# ── sidebar ───────────────────────────────────────────────
def sidebar():
    token = st.session_state.token
    role  = st.session_state.role

    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-brand">
            <h3>ML Loan Service</h3>
            <p>{st.session_state.user}</p>
        </div>
        """, unsafe_allow_html=True)
        bal = api("get", "/billing/balance", token=token)
        credits = bal.json()["credits_balance"] if bal and bal.status_code == 200 else "—"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.08);border-radius:10px;padding:10px 14px;margin:8px 0">
            <div style="font-size:10px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:0.08em;font-weight:600">Баланс</div>
            <div style="font-size:1.4rem;font-weight:700;color:#a5b4fc;margin-top:2px">{credits} <span style="font-size:13px;opacity:0.8">кр.</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        user_pages = ["Профиль", "Предсказание", "Мои предсказания", "Биллинг"]
        admin_pages = ["Аналитика", "Модели", "Промокоды", "Пользователи"]
        pages = user_pages + (admin_pages if role == "admin" else [])

        restored = st.session_state.pop("_restored_page", None)
        default_idx = pages.index(restored) if restored and restored in pages else 0
        page = st.radio("Меню", pages, index=default_idx, label_visibility="collapsed")
        st.divider()
        if st.button("Выйти", use_container_width=True):
            logout()
            st.rerun()
    return page


# ── страница: профиль ─────────────────────────────────────
def page_profile():
    st.title("Личный кабинет")
    token = st.session_state.token

    me = api("get", "/users/me", token=token)
    if not me or me.status_code != 200:
        st.error("Не удалось загрузить профиль")
        return
    u = me.json()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Профиль")
        role_label = "Администратор" if u["role"] == "admin" else "Пользователь"
        role_color = "#7c3aed" if u["role"] == "admin" else "#2563eb"
        initials = u["email"][0].upper()
        st.markdown(f"""
        <div style="background:white;border-radius:16px;padding:24px;border:1px solid #e5e7eb;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06)">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
                <div style="width:52px;height:52px;border-radius:50%;
                            background:linear-gradient(135deg,#6366f1,#8b5cf6);
                            display:flex;align-items:center;justify-content:center;
                            font-size:22px;font-weight:700;color:white">{initials}</div>
                <div>
                    <div style="font-weight:700;font-size:16px;color:#111827">{u['email']}</div>
                    <span style="background:{role_color}20;color:{role_color};
                                 padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600">
                        {role_label}
                    </span>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <div style="background:#f9fafb;border-radius:10px;padding:12px">
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;font-weight:600">Регистрация</div>
                    <div style="font-weight:600;color:#111827;margin-top:2px">{u['created_at'][:10]}</div>
                </div>
                <div style="background:#f0fdf4;border-radius:10px;padding:12px">
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;font-weight:600">Баланс</div>
                    <div style="font-weight:700;color:#059669;margin-top:2px">{u['credits_balance']} кр.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("Моя статистика")
        preds = api("get", "/predictions/", token=token)
        txns  = api("get", "/billing/transactions", token=token)

        pred_list = preds.json() if preds and preds.status_code == 200 else []
        txn_list  = txns.json()  if txns  and txns.status_code  == 200 else []

        total      = len(pred_list)
        done       = sum(1 for p in pred_list if p["status"] == "done")
        approved   = sum(1 for p in pred_list if p.get("result") and p["result"].get("approved"))
        spent      = sum(t["amount"] for t in txn_list if t["type"] == "debit")
        approval_rate = f"{approved/done*100:.0f}%" if done else "—"

        sc1, sc2 = st.columns(2)
        sc1.metric("Всего предсказаний", total)
        sc2.metric("Успешных", done)
        sc1.metric("Одобрено", approved)
        sc2.metric("% одобрений", approval_rate)
        st.metric("Кредитов потрачено", spent)

    if pred_list:
        st.divider()
        st.subheader("Одобрения vs Отказы")
        labels = ["Одобрено", "Отказано"]
        values = [approved, done - approved]
        if done > 0:
            fig = px.pie(names=labels, values=values,
                         color=labels,
                         color_discrete_map={"Одобрено": "#2ecc71", "Отказано": "#e74c3c"})
            fig.update_layout(margin=dict(t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)


# ── страница: предсказание ────────────────────────────────
def page_prediction():
    st.title("Новое предсказание")
    token = st.session_state.token

    models_r = api("get", "/models/", token=token)
    models = models_r.json() if models_r and models_r.status_code == 200 else []

    col_form, col_result = st.columns([1.2, 1])

    with col_form:
        if not models:
            st.warning("Нет доступных моделей. Обратитесь к администратору.")
            return

        model_options = {fmt_model(m["name"]): m["id"] for m in models}
        selected = st.selectbox("Модель скоринга", list(model_options.keys()))
        model_id = model_options[selected]

        GENDER_MAP  = {"Мужской": "male", "Женский": "female"}
        EDU_MAP     = {"Среднее": "High School", "Неполное высшее": "Associate",
                       "Бакалавр": "Bachelor", "Магистр": "Master", "Докторантура": "Doctorate"}
        HOME_MAP    = {"Аренда": "RENT", "Собственное": "OWN",
                       "Ипотека": "MORTGAGE", "Другое": "OTHER"}
        INTENT_MAP  = {"Личные нужды": "PERSONAL", "Образование": "EDUCATION",
                       "Медицина": "MEDICAL", "Бизнес": "VENTURE",
                       "Ремонт": "HOMEIMPROVEMENT", "Рефинансирование": "DEBTCONSOLIDATION"}
        DEFAULT_MAP = {"Нет": "No", "Да": "Yes"}

        st.markdown("**Данные заёмщика**")
        st.caption("Поля со * обязательны. Остальные можно оставить по умолчанию.")
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input(
                "Возраст *", 18, 100, 30,
                help="Полных лет заёмщика")
            gender_ru = st.selectbox(
                "Пол *", list(GENDER_MAP),
                help="Биологический пол заёмщика")
            edu_ru = st.selectbox(
                "Образование *", list(EDU_MAP),
                help="Наивысший полученный уровень образования")
            income = st.number_input(
                "Доход в год ($) *", 0, 10_000_000, 60000, step=1000,
                help="Годовой доход до вычета налогов")
            emp_exp = st.number_input(
                "Опыт работы (лет)", 0, 50, 0,
                help="Необязательно. Если неизвестно — оставьте 0")
            home_ru = st.selectbox(
                "Жильё", list(HOME_MAP),
                help="Необязательно. Тип проживания. По умолчанию — Аренда")
        with c2:
            loan_amnt = st.number_input(
                "Сумма займа ($) *", 0, 1_000_000, 10000, step=500,
                help="Запрашиваемая сумма кредита")
            intent_ru = st.selectbox(
                "Цель займа *", list(INTENT_MAP),
                help="На что будут потрачены средства")
            loan_rate = st.number_input(
                "Процентная ставка (%)", 0.0, 50.0, 10.5,
                help="Необязательно. Предлагаемая банком ставка. По умолчанию — 10.5%")
            cred_hist = st.number_input(
                "История кредитов (лет)", 0, 50, 0,
                help="Необязательно. Сколько лет назад открыт первый кредит. Если нет — оставьте 0")
            credit_score = st.number_input(
                "Кредитный рейтинг", 300, 850, 600,
                help="Необязательно. Если неизвестен — оставьте 600 (средний)")
            default_ru = st.selectbox(
                "Были ли дефолты?", list(DEFAULT_MAP),
                help="Необязательно. Были ли просрочки по прошлым кредитам")

        # авто-расчёт доли займа от дохода (не показываем пользователю)
        loan_pct_inc = round(loan_amnt / income, 4) if income > 0 else 0.0

        if st.button("Отправить на оценку", use_container_width=True, type="primary"):
            payload = {
                "person_age": age,
                "person_gender": GENDER_MAP[gender_ru],
                "person_education": EDU_MAP[edu_ru],
                "person_income": income,
                "person_emp_exp": emp_exp,
                "person_home_ownership": HOME_MAP[home_ru],
                "loan_amnt": loan_amnt,
                "loan_intent": INTENT_MAP[intent_ru],
                "loan_int_rate": loan_rate,
                "loan_percent_income": loan_pct_inc,
                "cb_person_cred_hist_length": cred_hist,
                "credit_score": credit_score,
                "previous_loan_defaults_on_file": DEFAULT_MAP[default_ru],
            }
            r = api("post", f"/predictions/?model_id={model_id}", token=token, json=payload)
            if r and r.status_code == 202:
                task = r.json()
                st.session_state["last_task_id"] = task["id"]
                st.session_state["last_result"] = None
            elif r:
                st.error(r.json().get("detail", "Ошибка"))

    with col_result:
        st.markdown("**Результат**")
        task_id = st.session_state.get("last_task_id")
        last_result = st.session_state.get("last_result")

        if last_result:
            res = last_result["result"]
            card_cls = "result-approved" if res["approved"] else "result-rejected"
            icon = "✓" if res["approved"] else "✗"
            verdict = "ОДОБРЕНО" if res["approved"] else "ОТКАЗАНО"
            st.markdown(f"""
            <div class="{card_cls}">
                <p class="result-title">{icon} {verdict}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            mc1, mc2 = st.columns(2)
            mc1.metric("Вероятность", f"{res['probability'] * 100:.1f}%")
            mc2.metric("Списано кредитов", last_result["credits_cost"])

        elif task_id:
            with st.spinner("Обрабатываем..."):
                for _ in range(15):
                    r = api("get", f"/predictions/{task_id}", token=token)
                    if r and r.json().get("status") in ("done", "failed"):
                        break
                    time.sleep(1)

            if r and r.status_code == 200:
                task = r.json()
                if task["status"] == "done" and task.get("result"):
                    st.session_state["last_result"] = task
                    st.rerun()
                elif task["status"] == "failed":
                    st.error(f"Ошибка: {task.get('result', {}).get('error', 'неизвестно')}")
                    st.session_state.pop("last_task_id", None)
        else:
            st.markdown("""
            <div style="background:white;border-radius:16px;padding:32px;text-align:center;
                        border:2px dashed #d1d5db;color:#9ca3af;margin-top:16px">
                <p style="font-size:2rem;margin:0">&#128203;</p>
                <p style="font-weight:600;font-size:14px;margin:8px 0 0">
                    Заполните форму и нажмите «Отправить на оценку»
                </p>
            </div>
            """, unsafe_allow_html=True)


# ── страница: мои предсказания ────────────────────────────
def page_my_predictions():
    st.title("Мои предсказания")
    token = st.session_state.token
    r = api("get", "/predictions/", token=token)
    if not r or r.status_code != 200:
        st.error("Не удалось загрузить")
        return
    data = r.json()
    if not data:
        st.info("У вас пока нет предсказаний")
        return

    done     = [p for p in data if p["status"] == "done"]
    approved = [p for p in done if p.get("result") and p["result"].get("approved")]
    spent    = sum(p["credits_cost"] for p in data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего запросов", len(data))
    c2.metric("Успешных", len(done))
    c3.metric("Одобрено", len(approved))
    c4.metric("Кредитов потрачено", spent)

    st.divider()

    STATUS_RU = {"done": "Выполнено", "failed": "Ошибка",
                 "pending": "В очереди", "running": "Обрабатывается"}
    DECISION_RU = {"Approved": "Одобрено", "Rejected": "Отказано"}

    rows = []
    for t in data:
        res = t.get("result") or {}
        label = res.get("label", "—")
        rows.append({
            "ID": t["id"],
            "Статус": STATUS_RU.get(t["status"], t["status"]),
            "Решение": DECISION_RU.get(label, label),
            "Вероятность": f"{float(res['probability'])*100:.1f}%" if res.get("probability") else "—",
            "Кредитов": t["credits_cost"],
            "Время": t["created_at"][:19].replace("T", " "),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── страница: биллинг ─────────────────────────────────────
def page_billing():
    st.title("Биллинг")
    token = st.session_state.token

    bal_r = api("get", "/billing/balance", token=token)
    balance = bal_r.json()["credits_balance"] if bal_r and bal_r.status_code == 200 else "—"

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Баланс")
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%);
                    border-radius:16px;padding:24px;margin-bottom:16px;color:white">
            <div style="font-size:12px;font-weight:600;opacity:0.8;text-transform:uppercase;letter-spacing:0.05em">
                Текущий баланс
            </div>
            <div style="font-size:2.5rem;font-weight:800;margin-top:4px">{balance}</div>
            <div style="font-size:14px;opacity:0.7;margin-top:2px">кредитов</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        st.subheader("Пополнить баланс")

        PACKAGES = {
            "Старт — 100 кр. / 50 ₽":    100,
            "Бизнес — 500 кр. / 200 ₽":  500,
            "Про — 1000 кр. / 350 ₽":    1000,
            "Своя сумма":                 None,
        }
        choice = st.selectbox("Тарифный пакет", list(PACKAGES.keys()))
        if PACKAGES[choice] is None:
            amount = st.number_input("Количество кредитов", 10, 100000, 100, step=10)
            price  = amount * 0.5
        else:
            amount = PACKAGES[choice]
            price  = {100: 50, 500: 200, 1000: 350}[amount]

        st.markdown(f"""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                    padding:12px 16px;margin:8px 0;display:flex;justify-content:space-between;align-items:center">
            <span style="color:#374151;font-size:14px">К оплате:</span>
            <span style="color:#059669;font-weight:800;font-size:18px">{price:.0f} ₽</span>
        </div>
        """, unsafe_allow_html=True)

        card = st.text_input("Номер карты", placeholder="0000 0000 0000 0000", max_chars=19)
        c1e, c2e = st.columns(2)
        expiry = c1e.text_input("Срок", placeholder="MM/YY", max_chars=5)
        cvv    = c2e.text_input("CVV", placeholder="•••", max_chars=3, type="password")

        if st.button("Оплатить", type="primary", use_container_width=True):
            if not card or not expiry or not cvv:
                st.error("Заполните данные карты")
            else:
                with st.spinner("Обработка платежа..."):
                    time.sleep(1)
                r = api("post", "/billing/topup", token=token, json={"amount": amount})
                if r and r.status_code == 200:
                    d = r.json()
                    msg = f"+{d['credits_added']} кредитов зачислено"
                    if d.get("bonus"):
                        msg += f" (включая {d['bonus']} бонусных — скидка {d['discount']}%)"
                    st.success(msg)
                    st.rerun()
                elif r:
                    st.error(r.json().get("detail", "Ошибка"))

        st.divider()
        st.subheader("Активировать промокод")
        code = st.text_input("Промокод")
        if st.button("Применить"):
            r = api("post", "/promo/activate", token=token, json={"code": code})
            if r and r.status_code == 200:
                d = r.json()
                st.success(d.get("message", "Промокод активирован"))
                st.rerun()
            elif r:
                st.error(r.json().get("detail", "Ошибка"))

    with col2:
        st.subheader("История транзакций")
        txn_r = api("get", "/billing/transactions", token=token)
        if txn_r and txn_r.status_code == 200:
            txns = txn_r.json()
            if txns:
                TYPE_MAP = {"credit": ("Пополнение", "#059669", "#d1fae5"),
                            "debit":  ("Списание",   "#dc2626", "#fee2e2"),
                            "refund": ("Возврат",    "#2563eb", "#dbeafe")}
                for t in txns[:20]:
                    label, color, bg = TYPE_MAP.get(t["type"], (t["type"], "#6b7280", "#f3f4f6"))
                    sign = "+" if t["type"] in ("credit","refund") else "-"
                    st.markdown(f"""
                    <div style="background:white;border-radius:10px;padding:12px 16px;
                                margin-bottom:8px;border:1px solid #e5e7eb;
                                display:flex;align-items:center;justify-content:space-between">
                        <div style="display:flex;align-items:center;gap:12px">
                            <span style="background:{bg};color:{color};padding:3px 10px;
                                         border-radius:20px;font-size:12px;font-weight:600">{label}</span>
                            <span style="color:#6b7280;font-size:13px">{t['description']}</span>
                        </div>
                        <div style="display:flex;flex-direction:column;align-items:flex-end">
                            <span style="color:{color};font-weight:700;font-size:15px">{sign}{t['amount']} кр.</span>
                            <span style="color:#9ca3af;font-size:11px">{t['created_at'][:19].replace('T',' ')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Нет транзакций")


# ── страница: аналитика (admin) ───────────────────────────
def page_analytics():
    st.title("Аналитика")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Пользователей",    db("SELECT COUNT(*) n FROM users")["n"].iloc[0] if not db("SELECT COUNT(*) n FROM users").empty else 0)
    c2.metric("Всего запросов",   db("SELECT COUNT(*) n FROM prediction_tasks")["n"].iloc[0] if not db("SELECT COUNT(*) n FROM prediction_tasks").empty else 0)
    c3.metric("Успешных",         db("SELECT COUNT(*) n FROM prediction_tasks WHERE status='done'")["n"].iloc[0] if not db("SELECT COUNT(*) n FROM prediction_tasks WHERE status='done'").empty else 0)
    c4.metric("Кредитов списано", db("SELECT COALESCE(SUM(amount),0) n FROM transactions WHERE type='debit'")["n"].iloc[0] if not db("SELECT COALESCE(SUM(amount),0) n FROM transactions WHERE type='debit'").empty else 0)

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Запросы по дням")
        daily = db("SELECT DATE(created_at) as date, COUNT(*) as count, status FROM prediction_tasks GROUP BY DATE(created_at), status ORDER BY date")
        if not daily.empty:
            fig = px.bar(daily, x="date", y="count", color="status",
                         color_discrete_map={"done":"#2ecc71","failed":"#e74c3c","pending":"#f39c12","running":"#3498db"},
                         labels={"date":"Дата","count":"Запросы","status":"Статус"})
            fig.update_layout(margin=dict(t=10,b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных")

    with col_r:
        st.subheader("Решения модели")
        res = db("SELECT result->>'label' as label, COUNT(*) as count FROM prediction_tasks WHERE status='done' AND result IS NOT NULL GROUP BY result->>'label'")
        if not res.empty:
            fig2 = px.pie(res, names="label", values="count",
                          color="label", color_discrete_map={"Approved":"#2ecc71","Rejected":"#e74c3c"})
            fig2.update_layout(margin=dict(t=10,b=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Нет данных")

    st.subheader("Последние предсказания")
    recent = db("""
        SELECT pt.id, u.email, pt.status,
               pt.result->>'label' AS решение,
               pt.result->>'probability' AS вероятность,
               pt.credits_cost AS кредитов,
               pt.created_at AS время
        FROM prediction_tasks pt JOIN users u ON u.id = pt.user_id
        ORDER BY pt.created_at DESC LIMIT 30
    """)
    if not recent.empty:
        st.dataframe(recent, use_container_width=True, hide_index=True)


# ── страница: модели (admin) ─────────────────────────────
def page_models():
    st.title("Управление моделями")
    token = st.session_state.token

    col_upload, col_list = st.columns([1, 1.5])

    with col_upload:
        st.subheader("Загрузить модель")
        name = st.text_input("Название")
        desc = st.text_input("Описание (необязательно)")
        f    = st.file_uploader("Файл .joblib", type=["joblib"])
        if st.button("Загрузить", type="primary", use_container_width=True):
            if not name or not f:
                st.error("Заполните название и выберите файл")
            else:
                r = api("post", "/models/upload", token=token,
                        files={"file": (f.name, f, "application/octet-stream")},
                        data={"name": name, "description": desc})
                if r and r.status_code == 201:
                    st.success(f"Модель «{name}» загружена")
                    st.rerun()
                elif r:
                    st.error(r.json().get("detail", "Ошибка"))

    with col_list:
        st.subheader("Активные модели")
        r = api("get", "/models/", token=token)
        if r and r.status_code == 200:
            models = r.json()
            if models:
                for m in models:
                    with st.container(border=True):
                        mc1, mc2 = st.columns([3, 1])
                        mc1.markdown(f"**{m['name']}**")
                        mc1.caption(m.get("description") or "Без описания")
                        if mc2.button("Удалить", key=f"del_model_{m['id']}"):
                            api("delete", f"/models/{m['id']}", token=token)
                            st.rerun()
            else:
                st.info("Нет загруженных моделей")


# ── страница: промокоды (admin) ───────────────────────────
def page_promos():
    st.title("Управление промокодами")
    token = st.session_state.token

    col_create, col_list = st.columns([1, 1.5])

    with col_create:
        st.subheader("Создать промокод")
        code         = st.text_input("Код")
        credits      = st.number_input("Кредиты", 0, 100000, 50)
        discount     = st.number_input("Скидка на топап (%)", 0, 100, 0)
        max_act      = st.number_input("Макс. активаций", 1, 10000, 10)
        expires      = st.date_input("Действует до")

        if st.button("Создать", type="primary", use_container_width=True):
            r = api("post", "/admin/promo", token=token, json={
                "code": code, "credits_amount": credits,
                "discount_percent": discount, "max_activations": max_act,
                "expires_at": f"{expires}T23:59:59",
            })
            if r and r.status_code == 200:
                st.success(f"Промокод «{code}» создан")
                st.rerun()
            elif r:
                st.error(r.json().get("detail", "Ошибка"))

    with col_list:
        st.subheader("Все промокоды")
        r = api("get", "/admin/promo", token=token)
        if r and r.status_code == 200:
            promos = r.json()
            if promos:
                for p in promos:
                    with st.container(border=True):
                        pc1, pc2, pc3 = st.columns([2, 2, 1])
                        pc1.markdown(f"**{p['code']}**")
                        pc2.caption(f"+{p['credits_amount']} кр. | скидка {p['discount_percent']}% | {p['current_activations']}/{p['max_activations']} активаций")
                        status = "Активен" if p["is_active"] else "Выключен"
                        pc3.caption(status)
                        if p["is_active"] and pc3.button("Удалить", key=f"del_{p['id']}"):
                            api("delete", f"/admin/promo/{p['id']}", token=token)
                            st.rerun()
            else:
                st.info("Нет промокодов")


# ── страница: пользователи (admin) ───────────────────────
def page_users():
    st.title("Пользователи")
    top = db("""
        SELECT u.email, u.role, u.credits_balance AS баланс,
               COUNT(pt.id) AS предсказаний,
               COALESCE(SUM(t.amount), 0) AS потрачено
        FROM users u
        LEFT JOIN prediction_tasks pt ON pt.user_id = u.id
        LEFT JOIN transactions t ON t.user_id = u.id AND t.type = 'debit'
        GROUP BY u.id, u.email, u.role, u.credits_balance
        ORDER BY потрачено DESC
    """)
    if not top.empty:
        st.dataframe(top, use_container_width=True, hide_index=True)
    else:
        st.info("Нет пользователей")


# ── роутинг ───────────────────────────────────────────────
restore_session()

if "token" not in st.session_state:
    if st.session_state.get("show_auth"):
        page_auth()
    else:
        page_landing()
else:
    page = sidebar()
    st.query_params["page"] = page
    if page == "Профиль":
        page_profile()
    elif page == "Предсказание":
        page_prediction()
    elif page == "Мои предсказания":
        page_my_predictions()
    elif page == "Биллинг":
        page_billing()
    elif page == "Аналитика":
        page_analytics()
    elif page == "Модели":
        page_models()
    elif page == "Промокоды":
        page_promos()
    elif page == "Пользователи":
        page_users()
