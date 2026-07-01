#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 27 17:48:43 2026

@author: hibalaawissi
"""

import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta, datetime
import urllib.parse
import urllib.request

FILE_PRENOTAZIONI = 'prenotazioni.csv'
FILE_CLIENTI = 'clienti.csv'

if 'sb_dates' not in st.session_state: st.session_state['sb_dates'] = []
if 'map_error' not in st.session_state: st.session_state['map_error'] = ""

OPERATORI_SPIAGGIA = ["Hiba Laawissi", "Rachele Filippin", "Federica Nebuloni", "Matilde Montis", "Eduardo Bustamante", "Alberto Bertolotti"]
CAPIENZA_FILE = {"Prima Fila": 17, "Seconda Fila": 17, "Terza Fila": 12, "Quarta Fila": 10, "Quinta Fila": 7, "Sesta Fila (Altre)": 6}

STAGIONI_DATE = {
    "Alta B": [(date(2026, 6, 27), date(2026, 7, 17)), (date(2026, 9, 1), date(2026, 9, 27))],
    "Altissima": [(date(2026, 7, 18), date(2026, 7, 31)), (date(2026, 8, 24), date(2026, 8, 31))],
    "Peak Season": [(date(2026, 8, 1), date(2026, 8, 23))]
}

GIORNI_FESTIVI = [date(2026, 6, 2), date(2026, 8, 15)]

TARIFFE = {
    "Alta B": {"Prima Fila": {"Feriale": [42, 8], "Festivo": [50, 10]}, "Seconda Fila": {"Feriale": [38, 7], "Festivo": [42, 8]}, "Terza Fila": {"Feriale": [38, 7], "Festivo": [42, 8]}, "Quarta Fila": {"Feriale": [36, 6], "Festivo": [40, 7]}, "Quinta Fila": {"Feriale": [36, 6], "Festivo": [40, 7]}, "Sesta Fila (Altre)": {"Feriale": [34, 5], "Festivo": [37, 6]}}
}

PREZZI_EXTRA = {"Postazione Esterna": {"Feriale": 32, "Festivo": 38}}

def calcola_prezzo_automatico(data_sel, fila, persone, durata, extra_scelti):
    giorno_sett = data_sel.weekday()
    tipo_tariffa = "Festivo" if (giorno_sett >= 5 or data_sel in GIORNI_FESTIVI) else "Feriale"
    prezzo_base = TARIFFE["Alta B"][fila][tipo_tariffa][0]
    return float(prezzo_base)

def carica_prenotazioni():
    if not os.path.exists(FILE_PRENOTAZIONI): return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno"])
    return pd.read_csv(FILE_PRENOTAZIONI, dtype={'Telefono': str})

st.set_page_config(page_title="Beach Pass Pro", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

operatore_attivo = st.selectbox("👤 Operatore Attivo:", OPERATORI_SPIAGGIA)
data_visiva = st.date_input("📅 Mappa Visiva:", date.today(), format="DD/MM/YYYY")

if data_visiva:
    df_pren = carica_prenotazioni()
    data_str = data_visiva.strftime("%Y-%m-%d")
    st.header(f"Planning del {data_str}")
    if st.session_state['map_error']: st.error(st.session_state['map_error'])

    for nome_fila, max_posti in CAPIENZA_FILE.items():
        st.subheader(nome_fila)
        cols = st.columns(max_posti)
        for i in range(max_posti):
            num = i + 1
            posto_occupato = df_pren[(df_pren['Data'] == data_str) & (df_pren['Fila'] == nome_fila) & (df_pren['Ombrellone'] == num)]
            
            if not posto_occupato.empty:
                cols[i].success(f"OCCUPATO: {posto_occupato.iloc[0]['Nome']}")
            else:
                widget_key = f"input_{nome_fila}_{num}"
                tel_key = f"tel_{nome_fila}_{num}"
                cols[i].text_input("Nome", key=widget_key, placeholder="Nome Cognome")
                cols[i].text_input("Tel", key=tel_key, placeholder="333...")
                if cols[i].button("Prenota", key=f"btn_{nome_fila}_{num}"):
                    nome = st.session_state[widget_key]
                    tel = st.session_state[tel_key]
                    parole = [p for p in nome.split() if p.replace(".","").strip() != ""]
                    if len(parole) < 2:
                        st.session_state['map_error'] = "🚨 ERRORE: Inserisci Nome e Cognome (no punti)."
                        st.rerun()
                    if not tel.isdigit() or len(tel) < 9:
                        st.session_state['map_error'] = "🚨 ERRORE: Telefono non valido."
                        st.rerun()
                    pz = calcola_prezzo_automatico(data_visiva, nome_fila, 2, "Giornata Intera", [])
                    nuova_p = pd.DataFrame([{"Data": data_str, "Fila": nome_fila, "Ombrellone": num, "Nome": nome, "Telefono": tel, "Stato": "Confermato", "Prezzo_Giorno": pz}])
                    df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
                    df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                    st.session_state['map_error'] = ""
                    st.rerun()
