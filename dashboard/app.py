import os
import time
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

API = os.getenv("API_URL", "http://api:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mluser:mlpassword@postgres:5432/mlservice")
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="ML Loan Service", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1a1a2e; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #e0e0e0 !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 4px; }
.stTabs [data-baseweb="tab"] { font-size: 15px; }
div[data-testid="metric-container"] {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px;
    border-left: 4px solid #4361ee;
}
</style>
""", unsafe_allow_html=True)


# ── helpers ──────────────────────────────────────────────
def api(method, path, token=None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = getattr(requests, method)(f"{API}{path}", headers=headers, timeout=10, **kwargs)
        return r
    except Exception as e:
        st.error(f"Нет связи с API: {e}")
        return None


def db(query):
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


# ── auth pages ────────────────────────────────────────────
def page_auth():
    col = st.columns([1, 1.2, 1])[1]
    with col:
        st.markdown("## ML Loan Service")
        st.markdown("Платформа предсказания кредитных заявок")
        st.divider()
        tab_login, tab_reg = st.tabs(["Войти", "Регистрация"])

        with tab_login:
            email = st.text_input("Email", key="li_email")
            pwd   = st.text_input("Пароль", type="password", key="li_pwd")
            if st.button("Войти", use_container_width=True):
                r = api("post", "/auth/login", data={"username": email, "password": pwd})
                if r and r.status_code == 200:
                    token = r.json()["access_token"]
                    me = api("get", "/users/me", token=token)
                    if me and me.status_code == 200:
                        u = me.json()
                        st.session_state.token = token
                        st.session_state.user  = u["email"]
                        st.session_state.role  = u["role"]
                        st.query_params["token"] = token
                        st.rerun()
                else:
                    st.error("Неверный email или пароль")

        with tab_reg:
            r_email = st.text_input("Email", key="reg_email")
            r_pwd   = st.text_input("Пароль (мин. 6 символов)", type="password", key="reg_pwd")
            if st.button("Зарегистрироваться", use_container_width=True):
                if not r_email or not r_pwd:
                    st.error("Заполните все поля")
                elif len(r_pwd) < 6:
                    st.error("Пароль должен быть минимум 6 символов")
                else:
                    r = api("post", "/auth/register", json={"email": r_email, "password": r_pwd})
                    if r and r.status_code == 201:
                        st.success("Аккаунт создан! Перейдите на вкладку «Войти»")
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
        st.markdown(f"### ML Loan Service")
        st.caption(f"Вы: {st.session_state.user}")
        bal = api("get", "/billing/balance", token=token)
        if bal and bal.status_code == 200:
            st.metric("Баланс", f"{bal.json()['credits_balance']} кр.")
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
        with st.container(border=True):
            st.markdown(f"**Email:** {u['email']}")
            st.markdown(f"**Роль:** {'Администратор' if u['role'] == 'admin' else 'Пользователь'}")
            st.markdown(f"**Дата регистрации:** {u['created_at'][:10]}")
            st.markdown(f"**Баланс:** {u['credits_balance']} кредитов")

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

        model_names = {m["name"]: m["id"] for m in models}
        selected = st.selectbox("Модель", list(model_names.keys()))
        model_id = model_names[selected]

        st.markdown("**Данные заёмщика**")
        c1, c2 = st.columns(2)
        with c1:
            age     = st.number_input("Возраст", 18, 100, 30)
            gender  = st.selectbox("Пол", ["male", "female"])
            edu     = st.selectbox("Образование", ["High School", "Associate", "Bachelor", "Master", "Doctorate"])
            income  = st.number_input("Доход (год, $)", 0, 10_000_000, 60000, step=1000)
            emp_exp = st.number_input("Опыт работы (лет)", 0, 50, 5)
            home    = st.selectbox("Жильё", ["RENT", "OWN", "MORTGAGE", "OTHER"])
        with c2:
            loan_amnt    = st.number_input("Сумма займа ($)", 0, 1_000_000, 10000, step=500)
            loan_intent  = st.selectbox("Цель займа", ["PERSONAL", "EDUCATION", "MEDICAL", "VENTURE", "HOMEIMPROVEMENT", "DEBTCONSOLIDATION"])
            loan_rate    = st.number_input("Процентная ставка (%)", 0.0, 50.0, 10.5)
            loan_pct_inc = st.number_input("Доля займа от дохода", 0.0, 1.0, 0.17, step=0.01)
            cred_hist    = st.number_input("История кредитов (лет)", 0, 50, 3)
            credit_score = st.number_input("Кредитный рейтинг", 300, 850, 650)
            prev_default = st.selectbox("Прошлые дефолты", ["No", "Yes"])

        if st.button("Отправить на оценку", use_container_width=True, type="primary"):
            payload = {
                "person_age": age, "person_gender": gender,
                "person_education": edu, "person_income": income,
                "person_emp_exp": emp_exp, "person_home_ownership": home,
                "loan_amnt": loan_amnt, "loan_intent": loan_intent,
                "loan_int_rate": loan_rate, "loan_percent_income": loan_pct_inc,
                "cb_person_cred_hist_length": cred_hist,
                "credit_score": credit_score,
                "previous_loan_defaults_on_file": prev_default,
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
            if res["approved"]:
                st.success("ОДОБРЕНО")
            else:
                st.error("ОТКАЗАНО")
            st.metric("Вероятность", f"{res['probability'] * 100:.1f}%")
            st.metric("Списано кредитов", last_result["credits_cost"])

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
            st.info("Заполните форму слева и нажмите «Отправить»")


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

    rows = []
    for t in data:
        res = t.get("result") or {}
        rows.append({
            "ID": t["id"],
            "Статус": t["status"],
            "Решение": res.get("label", "—"),
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
        st.metric("Текущий баланс", f"{balance} кредитов")
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

        st.caption(f"К оплате: **{price:.0f} ₽**")

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
                rows = [{
                    "Тип": t["type"],
                    "Сумма": t["amount"],
                    "Описание": t["description"],
                    "Время": t["created_at"][:19].replace("T", " "),
                } for t in txns]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
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
    page_auth()
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
