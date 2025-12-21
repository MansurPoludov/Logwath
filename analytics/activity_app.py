import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# ===============================
# 🔗 Подключение к PostgreSQL
# ===============================
DB_USER = "postgres"
DB_PASSWORD = quote_plus("Mpsl*1412@16&*")
DB_NAME = "logwatch_db"

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)

st.set_page_config(
    page_title="Activity Analytics",
    layout="wide"
)

st.title("📊 Аналитика активности сайта")

# ===============================
# 📥 Загрузка данных
# ===============================
query = """
SELECT
    id,
    action,
    ip,
    created_at
FROM logs_auditlog
ORDER BY created_at DESC
"""

df = pd.read_sql(query, engine)
# Приводим время из UTC в локальное (UTC+5)
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
df["created_at"] = df["created_at"].dt.tz_convert("Asia/Almaty")

if df.empty:
    st.warning("Нет данных для отображения")
    st.stop()

# ===============================
# 🔍 ФИЛЬТРЫ
# ===============================
st.subheader("🔎 Фильтрация")

col1, col2, col3 = st.columns(3)

with col1:
    action_filter = st.selectbox(
        "Тип действия",
        ["Все"] + sorted(df["action"].unique().tolist())
    )

with col2:
    date_from = st.date_input("Дата с", df["created_at"].min().date())

with col3:
    date_to = st.date_input("Дата по", df["created_at"].max().date())

if action_filter != "Все":
    df = df[df["action"] == action_filter]

df = df[
    (df["created_at"].dt.date >= date_from) &
    (df["created_at"].dt.date <= date_to)
]

# ===============================
# 📌 МЕТРИКИ
# ===============================
st.subheader("📌 Сводка")

m1, m2, m3 = st.columns(3)
m1.metric("Всего действий", len(df))
m2.metric("Уникальных IP", df["ip"].nunique())
m3.metric("Типов действий", df["action"].nunique())

# ===============================
# 📈 ГРАФИКИ
# ===============================
st.subheader("📈 Активность по времени")

# Активность по часам
activity_by_hour = df.groupby(df["created_at"].dt.hour).size()
st.line_chart(activity_by_hour)

# Активность по дням
st.subheader("📅 Активность по дням")
activity_by_day = df.groupby(df["created_at"].dt.date).size()
st.bar_chart(activity_by_day)

# Распределение действий по типу
st.subheader("🛠 Распределение действий по типу")
action_counts = df["action"].value_counts()
st.bar_chart(action_counts)

# Топ 10 IP по активности
st.subheader("🌐 Топ 10 IP по активности")
top_ips = df["ip"].value_counts().head(10)
st.bar_chart(top_ips)

# Активность по часам и типам действий (область)
st.subheader("⏱ Активность по часам и типам действий")
activity_hour_action = df.groupby([df["created_at"].dt.hour, "action"]).size().unstack(fill_value=0)
st.area_chart(activity_hour_action)

# ===============================
# 📋 ТАБЛИЦА
# ===============================
st.subheader("📋 Детализация")

st.dataframe(
    df.sort_values("created_at", ascending=False),
    use_container_width=True
)
