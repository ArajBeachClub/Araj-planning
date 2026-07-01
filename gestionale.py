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

FILE_PRENOTAZIONI = 'prenotazioni.csv'
FILE_CLIENTI = 'clienti.csv'

# Setup
if 'map_error' not in st.session_state: st.session_state['map_error'] = ""

CAPIENZA_FILE = {"Prima Fila": 17, "Seconda Fila": 17, "Terza Fila": 12, "Quarta Fila": 10, "Quinta Fila": 7, "Sesta Fila (Altre)": 6}

def carica_prenotazioni():
    if not os.path.exists(FILE_PRENOTAZIONI): return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno"])
    return pd.read_csv(FILE_PRENOTAZIONI, dtype={'Telefono': str})

st.set_page_config(page_title="Beach Pass", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni")

# Selezione Data
data_visiva = st.date_input("📅 Mappa Visiva: Seleziona Data:", date.today(), format="DD/MM/YYYY")

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
            
            # Recupero stato
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
                    
                    # Salvataggio
                    nuova_p = pd.DataFrame([{"Data": data_str, "Fila": nome_fila, "Ombrellone": num, "Nome": nome, "Telefono": tel, "Stato": "Confermato", "Prezzo_Giorno": 0}])
                    df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
                    df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                    st.session_state['map_error'] = ""
                    st.rerun()
