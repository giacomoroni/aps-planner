st.write("VERSIONE APS 2.0 - Google Sheets")

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px

st.write("VERSIONE APS 2.0 - Google Sheets")
st.title("APS Planner Web App")

# 🔗 LINK GOOGLE SHEETS (già trasformato)
file_url = "https://docs.google.com/spreadsheets/d/1wD-kjvBqUwgEov4lCdx5QedwuhtUsJPveHqfGZkECao/export?format=xlsx"

try:
    ordini = pd.read_excel(file_url, sheet_name="Ordini")
    param = pd.read_excel(file_url, sheet_name="Parametri")
except:
    st.error("Errore nel caricamento dati da Google Sheets")
    st.stop()

# ✅ PULIZIA COLONNE
ordini.columns = ordini.columns.str.strip()

# ✅ SELEZIONE SOLO COLONNE UTILI (ignoriamo le altre)
colonne_utili = [
    "CO",
    "Cliente",
    "Cod. Articolo",
    "Linea",
    "Data consegna",
    "Qta",
    "Famiglia prodotto",
    "Tempo ciclo"
]

ordini = ordini[colonne_utili]

# ✅ PARAMETRI
operatori = int(param[param.Parametro == "Operatori"].Valore.values[0])
ore = int(param[param.Parametro == "Ore_giornaliere"].Valore.values[0])
start = pd.to_datetime(param[param.Parametro == "Data_inizio"].Valore.values[0])

capacita = operatori * ore

# ✅ PREPARAZIONE DATI
ordini["Data consegna"] = pd.to_datetime(ordini["Data consegna"])
ordini["Ore_rimanenti"] = ordini["Qta"] * ordini["Tempo ciclo"]

# ✅ PRIORITÀ AUTOMATICA
oggi = start

ordini["giorni_urgenza"] = (ordini["Data consegna"] - oggi).dt.days

ordini["score_priorita"] = (
    ordini["giorni_urgenza"] * 0.7 +
    ordini["Ore_rimanenti"] * 0.3
)

ordini["Priorita"] = ordini["score_priorita"]

# ✅ ORDINAMENTO APS
ordini = ordini.sort_values("Priorita")

# ✅ PIANIFICAZIONE
piano = []
giorno = start

while ordini["Ore_rimanenti"].sum() > 0:
    cap = capacita

    for i, o in ordini.iterrows():
        if o["Ore_rimanenti"] <= 0:
            continue

        use = min(o["Ore_rimanenti"], cap)

        piano.append([
            o["CO"],
            o["Cliente"],
            o["Cod. Articolo"],
            o["Linea"],
            o["Famiglia prodotto"],
            giorno,
            use,
            o["Data consegna"]
        ])

        ordini.loc[i, "Ore_rimanenti"] -= use
        cap -= use

        if cap <= 0:
            break

    giorno += timedelta(days=1)

# ✅ OUTPUT
df = pd.DataFrame(piano, columns=[
    "CO",
    "Cliente",
    "Cod_Articolo",
    "Linea",
    "Famiglia_prodotto",
    "Giorno",
    "Ore",
    "Data_consegna"
])

df["Ritardo_giorni"] = (df["Giorno"] - df["Data_consegna"]).dt.days

# ================= VISUAL =================

st.success("✅ Dati caricati automaticamente da Google Sheets")

# 📋 Piano
st.subheader("📋 Piano Produzione")
st.dataframe(df)

# 📊 Carico giornaliero
st.subheader("📊 Carico Giornaliero")
st.line_chart(df.groupby("Giorno")["Ore"].sum())

# 🏭 Carico per linea
st.subheader("🏭 Carico per Linea")
st.bar_chart(df.groupby("Linea")["Ore"].sum())

# 📦 Carico per famiglia
st.subheader("📦 Carico per Famiglia Prodotto")
st.bar_chart(df.groupby("Famiglia_prodotto")["Ore"].sum())

# 🚨 Ritardi
st.subheader("🚨 Ordini in Ritardo")
st.dataframe(df[df["Ritardo_giorni"] > 0])

# 📅 GANTT INTERATTIVO
st.subheader("📅 Gantt Produzione")

df["Fine"] = df["Giorno"] + pd.to_timedelta(df["Ore"] / capacita, unit="D")

fig = px.timeline(
    df,
    x_start="Giorno",
    x_end="Fine",
    y="Linea",
    color="CO",
    hover_data=["Cliente", "Cod_Articolo", "Famiglia_prodotto"]
)

fig.update_yaxes(autorange="reversed")

st.plotly_chart(fig, use_container_width=True)

# 🔄 Bottone refresh
if st.button("🔄 Aggiorna dati"):
    st.rerun()
