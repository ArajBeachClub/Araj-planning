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

# Inizializzazione
if 'sb_dates' not in st.session_state: st.session_state['sb_dates'] = []
if 'sb_fila' not in st.session_state: st.session_state['sb_fila'] = "Prima Fila"
if 'sb_omb' not in st.session_state: st.session_state['sb_omb'] = 1
if 'map_error' not in st.session_state: st.session_state['map_error'] = ""

OPERATORI_SPIAGGIA = ["Hiba Laawissi", "Rachele Filippin", "Federica Nebuloni", "Matilde Montis", "Eduardo Bustamante", "Alberto Bertolotti"]
OPZIONI_INCASSO = ["Da saldare", "Ospite (Gratis)"] + OPERATORI_SPIAGGIA
MAPPA_NOMI_RAPIDI = {"Hiba": "Hiba Laawissi", "Rachele": "Rachele Filippin", "Federica": "Federica Nebuloni", "Eduardo": "Eduardo Bustamante", "Matilde": "Matilde Montis", "Alberto": "Alberto Bertolotti"}

CAPIENZA_FILE = {"Prima Fila": 17, "Seconda Fila": 17, "Terza Fila": 12, "Quarta Fila": 10, "Quinta Fila": 7, "Sesta Fila (Altre)": 6}

STAGIONI_DATE = {
    "Media 1": [(date(2026, 5, 30), date(2026, 6, 12))],
    "Media 2": [(date(2026, 6, 13), date(2026, 6, 19))],
    "Alta A": [(date(2026, 6, 20), date(2026, 6, 26))],  
    "Alta B": [(date(2026, 6, 27), date(2026, 7, 17)), (date(2026, 9, 1), date(2026, 9, 27))],
    "Altissima": [(date(2026, 7, 18), date(2026, 7, 31)), (date(2026, 8, 24), date(2026, 8, 31))],
    "Peak Season": [(date(2026, 8, 1), date(2026, 8, 23))]
}

GIORNI_FESTIVI = [date(2026, 6, 2), date(2026, 8, 15)]

TARIFFE = {
    "Media 1": {"Prima Fila": {"Feriale": [30, 7], "Festivo": [33, 9]}, "Seconda Fila": {"Feriale": [28, 6], "Festivo": [31, 8]}, "Terza Fila": {"Feriale": [28, 6], "Festivo": [31, 8]}, "Quarta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]}, "Quinta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]}, "Sesta Fila (Altre)": {"Feriale": [26, 4], "Festivo": [27, 5]}},
    "Media 2": {"Prima Fila": {"Feriale": [33, 7], "Festivo": [35, 9]}, "Seconda Fila": {"Feriale": [30, 6], "Festivo": [33, 8]}, "Terza Fila": {"Feriale": [30, 6], "Festivo": [33, 8]}, "Quarta Fila": {"Feriale": [28, 5], "Festivo": [30, 7]}, "Quinta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]}, "Sesta Fila (Altre)": {"Feriale": [27, 4], "Festivo": [29, 5]}},
    "Alta A": {"Prima Fila": {"Feriale": [38, 8], "Festivo": [42, 10]}, "Seconda Fila": {"Feriale": [36, 7], "Festivo": [40, 8]}, "Terza Fila": {"Feriale": [36, 7], "Festivo": [40, 8]}, "Quarta Fila": {"Feriale": [34, 6], "Festivo": [38, 7]}, "Quinta Fila": {"Feriale": [32, 6], "Festivo": [36, 7]}, "Sesta Fila (Altre)": {"Feriale": [32, 5], "Festivo": [36, 6]}},
    "Alta B": {"Prima Fila": {"Feriale": [42, 8], "Festivo": [50, 10]}, "Seconda Fila": {"Feriale": [38, 7], "Festivo": [42, 8]}, "Terza Fila": {"Feriale": [38, 7], "Festivo": [42, 8]}, "Quarta Fila": {"Feriale": [36, 6], "Festivo": [40, 7]}, "Quinta Fila": {"Feriale": [36, 6], "Festivo": [40, 7]}, "Sesta Fila (Altre)": {"Feriale": [34, 5], "Festivo": [37, 6]}},
    "Altissima": {"Prima Fila": {"Feriale": [56, 10], "Festivo": [58, 12]}, "Seconda Fila": {"Feriale": [53, 8], "Festivo": [55, 10]}, "Terza Fila": {"Feriale": [53, 8], "Festivo": [55, 10]}, "Quarta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]}, "Quinta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]}, "Sesta Fila (Altre)": {"Feriale": [42, 6], "Festivo": [44, 7]}},
    "Peak Season": {"Prima Fila": {"Feriale": [74, 14], "Festivo": [74, 14]}, "Seconda Fila": {"Feriale": [65, 10], "Festivo": [65, 10]}, "Terza Fila": {"Feriale": [65, 10], "Festivo": [65, 10]}, "Quarta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]}, "Quinta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]}, "Sesta Fila (Altre)": {"Feriale": [49, 8], "Festivo": [49, 8]}}
}

PREZZI_EXTRA = {
    "1 Lettino Extra": {"Feriale": 8, "Festivo": 10}, "2 Lettini Extra": {"Feriale": 16, "Festivo": 20},
    "1 Asciugamano (Telo)": {"Feriale": 4, "Festivo": 5}, "2 Asciugamani (Teli)": {"Feriale": 8, "Festivo": 10},
    "1 Lettino Extra, 1 Asciugamano (Telo)": {"Feriale": 12, "Festivo": 15}, "2 Lettini Extra, 2 Asciugamani (Teli)": {"Feriale": 24, "Festivo": 30},
    "Postazione Esterna": {"Feriale": 32, "Festivo": 38}
}

MESI_ITA = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
STATI_MAP = {"Confermato (Rosso)": "Confermato", "In Attesa (Giallo)": "Attesa", "Presente in Spiaggia (Viola)": "Presente", "Pagato (Blu)": "Pagato", "Presente e Pagato (Verde Acqua)": "Pres_Pagato", "Liberato Solo Mattina (Rivendibile)": "Libero_Mat", "Liberato Solo Pomeriggio (Rivendibile)": "Libero_Pom", "Completamente Libero / Cancella (Verde)": "Libero"}

def trova_stagione(data_sel):
    for stagione, intervalli in STAGIONI_DATE.items():
        for inizio, fine in intervalli:
            if inizio <= data_sel <= fine: return stagione
    return "Media 1"

def calcola_prezzo_automatico(data_sel, fila, persone, durata, extra_scelti):
    stagione = trova_stagione(data_sel)
    giorno_sett = data_sel.weekday()
    tipo_tariffa = "Festivo" if (giorno_sett >= 5 or data_sel in GIORNI_FESTIVI or (data_sel + timedelta(days=1)) in GIORNI_FESTIVI) else "Feriale"
    prezzo_base = TARIFFE[stagione][fila][tipo_tariffa][0]
    if durata == "Mezza Giornata (fino 13 / da 15.30)": prezzo_base = prezzo_base * 0.70
    elif durata == "Solo 1 Persona (Postazione Ridotta)": prezzo_base = prezzo_base * 0.75
    totale = prezzo_base
    if persone > 3: totale += TARIFFE[stagione][fila][tipo_tariffa][1]
    for ex in extra_scelti:
        if ex in PREZZI_EXTRA: totale += PREZZI_EXTRA[ex][tipo_tariffa]
    return float(totale)

def carica_prenotazioni():
    if not os.path.exists(FILE_PRENOTAZIONI): return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Persone", "Durata", "Extra"])
    return pd.read_csv(FILE_PRENOTAZIONI, dtype={'Telefono': str})

st.set_page_config(page_title="Beach Pass Pro", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

# --- INTERFACCIA MAPPA E SALVATAGGIO ---
data_visiva = st.date_input("📅 Mappa Visiva:", [], format="DD/MM/YYYY")
if data_visiva:
    df_pren = carica_prenotazioni()
    data_str = data_visiva[0].strftime("%Y-%m-%d")
    st.header(f"Planning del {data_str}")
    
    if st.session_state['map_error']: st.error(st.session_state['map_error'])

    for nome_fila, max_posti in CAPIENZA_FILE.items():
        st.subheader(nome_fila)
        cols = st.columns(max_posti)
        for i in range(max_posti):
            num = i + 1
            widget_key = f"input_{nome_fila}_{num}"
            tel_key = f"tel_{nome_fila}_{num}"
            
            # Griglia di input raddoppiata
            cols[i].text_input("Nome", key=widget_key, placeholder="Nome Cognome")
            cols[i].text_input("Tel", key=tel_key, placeholder="333...")
            
            if cols[i].button("Prenota", key=f"btn_{nome_fila}_{num}"):
                nome = st.session_state[widget_key]
                tel = st.session_state[tel_key]
                
                # Validazione rigida
                parole = [p for p in nome.split() if p.replace(".","").strip() != ""]
                if len(parole) < 2:
                    st.session_state['map_error'] = "🚨 ERRORE: Inserisci Nome e Cognome (no punti)."
                    st.rerun()
                if not tel.isdigit() or len(tel) < 9:
                    st.session_state['map_error'] = "🚨 ERRORE: Telefono non valido."
                    st.rerun()
                
                # Salvataggio
                pz = calcola_prezzo_automatico(data_visiva[0], nome_fila, 2, "Giornata Intera", [])
                nuova_p = pd.DataFrame([{"Data": data_str, "Fila": nome_fila, "Ombrellone": num, "Nome": nome, "Telefono": tel, "Stato": "Confermato", "Prezzo_Giorno": pz, "Persone": 2, "Durata": "Giornata Intera", "Extra": ""}])
                df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
                df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                st.session_state['map_error'] = ""
                st.rerun()
