
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.title("APS Planner Web App")

uploaded_file = st.file_uploader("Carica file Excel", type="xlsx")

if uploaded_file:
    ordini = pd.read_excel(uploaded_file, sheet_name="Ordini")
    param = pd.read_excel(uploaded_file, sheet_name="Parametri")

    operatori = int(param[param.Parametro=="Operatori"].Valore.values[0])
    ore = int(param[param.Parametro=="Ore_giornaliere"].Valore.values[0])
    start = pd.to_datetime(param[param.Parametro=="Data_inizio"].Valore.values[0])

    capacita = operatori * ore

    ordini["Due_date"] = pd.to_datetime(ordini["Due_date"])
    ordini["Ore_rimanenti"] = (ordini["Quantita"] * ordini["Tempo_ciclo_min"]) / 60
    ordini = ordini.sort_values(["Priorita","Due_date"])

    piano = []
    giorno = start

    while ordini["Ore_rimanenti"].sum() > 0:
        cap = capacita

        for i, o in ordini.iterrows():
            if o["Ore_rimanenti"] <= 0:
                continue

            use = min(o["Ore_rimanenti"], cap)

            piano.append([o["Ordine"], giorno, use, o["Due_date"]])
            ordini.loc[i, "Ore_rimanenti"] -= use
            cap -= use

            if cap <= 0:
                break

        giorno += timedelta(days=1)

    df = pd.DataFrame(piano, columns=["Ordine","Giorno","Ore","Due_date"])
    df["Ritardo"] = (df["Giorno"] - df["Due_date"]).dt.days

    st.dataframe(df)
    st.line_chart(df.groupby("Giorno")["Ore"].sum())
