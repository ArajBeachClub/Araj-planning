#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 27 17:48:43 2026

@author: hibalaawissi
"""

import streamlit as st
import pandas as pd
import os
import shutil
import requests
from datetime import date, timedelta, datetime
import urllib.parse
import urllib.request

FILE_PRENOTAZIONI = 'prenotazioni.csv'
FILE_CLIENTI = 'clienti.csv'

# ==========================================
# 👤 TEAM E OPERATORI
# ==========================================
OPERATORI_SPIAGGIA = ["Hiba Laawissi", "Rachele Filippin", "Federica Nebuloni", "Matilde Montis", "Eduardo Bustamante", "Alberto Bertolotti"]
OPZIONI_INCASSO = ["Da saldare", "Ospite (Gratis)"] + OPERATORI_SPIAGGIA

MAPPA_NOMI_RAPIDI = {
    "Hiba": "Hiba Laawissi",
    "Rachele": "Rachele Filippin",
    "Federica": "Federica Nebuloni",
    "Eduardo": "Eduardo Bustamante",
    "Matilde": "Matilde Montis",
    "Alberto": "Alberto Bertolotti"
}

# ==========================================
# 🤖 CONFIGURAZIONE BOT TELEGRAM E BACKUP
# ==========================================
TELEGRAM_TOKEN = "8804050943:AAHvXVmSnEUPlvV6mj33JGGQHfhosnqcC2U"
TELEGRAM_CHAT_ID = "8663794616"  

def controllo_backup_automatico():
    try:
        # Calcolo ora italiana (estate = UTC+2)
        ora_italia = datetime.utcnow() + timedelta(hours=2)
        oggi_str = ora_italia.strftime('%d-%m-%Y')
        
        # Scatta solo se sono passate le 20:00
        if ora_italia.hour >= 20:
            ha_gia_fatto = False
            if os.path.exists("ultimo_backup.txt"):
                with open("ultimo_backup.txt", "r") as f:
                    if f.read().strip() == oggi_str:
                        ha_gia_fatto = True
            
            if not ha_gia_fatto and os.path.exists(FILE_PRENOTAZIONI):
                # 1. Salva direttamente nel server (cartella invisibile)
                if not os.path.exists("backups_automatici"):
                    os.makedirs("backups_automatici")
                
                file_destinazione = f"backups_automatici/Backup_Spiaggia_{oggi_str}.csv"
                # Creiamo il file forzando il formato data corretto per il backup
                df_bkp = pd.read_csv(FILE_PRENOTAZIONI)
                df_bkp['Data'] = pd.to_datetime(df_bkp['Data']).dt.strftime('%d-%m-%Y')
                df_bkp.to_csv(file_destinazione, index=False, sep=';')
                
                # 2. Invia copia sicurezza fisica su Telegram
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
                with open(file_destinazione, 'rb') as f:
                    files = {'document': (f"Backup_Spiaggia_{oggi_str}.csv", f, "text/csv")}
                    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f"✅ BACKUP AUTOMATICO ESEGUITO\nData: {oggi_str}\nOra: {ora_italia.strftime('%H:%M')}"}
                    requests.post(url, files=files, data=data, timeout=10)
                
                # 3. Registra che per oggi abbiamo salvato
                with open("ultimo_backup.txt", "w") as f:
                    f.write(oggi_str)
                    
                return True
    except Exception:
        pass
    return False

def invia_notifica_telegram(messaggio):
    messaggio_codificato = urllib.parse.quote(messaggio)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={messaggio_codificato}"
    try:
        urllib.request.urlopen(url)
        return True
    except Exception:
        return False

# ==========================================
# ⚙️ FUNZIONI DI PULIZIA E RICERCA INTELLIGENTE
# ==========================================

def normalizza_tel(t):
    if not t or pd.isna(t): return ""
    t = str(t).strip().replace(" ", "").replace("+", "")
    if t.startswith("39") and len(t) > 9:
        t = t[2:]
    return t

# ==========================================
# ⚙️ CONFIGURAZIONE TARIFFE E STAGIONI
# ==========================================

CAPIENZA_FILE = {
    "Prima Fila": 17,
    "Seconda Fila": 16,
    "Terza Fila": 9,
    "Quarta Fila": 8,
    "Quinta Fila": 8,
    "Sesta Fila (Altre)": 8,
    "Spiaggia Libera / Esterna": 5
}

STAGIONI_DATE = {
    "Media": [(date(2026, 5, 30), date(2026, 6, 19))],
    "Alta A": [(date(2026, 6, 20), date(2026, 7, 3))],
    "Alta B": [(date(2026, 7, 4), date(2026, 7, 17)), (date(2026, 9, 1), date(2026, 9, 27))],
    "Altissima": [(date(2026, 7, 18), date(2026, 7, 31)), (date(2026, 8, 24), date(2026, 8, 31))],
    "Peak Season": [(date(2026, 8, 1), date(2026, 8, 23))]
}

GIORNI_FESTIVI = [date(2026, 6, 2), date(2026, 8, 15)]

TARIFFE = {
    "Media": {
        "Prima Fila": {"Feriale": [30, 7], "Festivo": [33, 9]},
        "Seconda Fila": {"Feriale": [28, 6], "Festivo": [31, 8]},
        "Terza Fila": {"Feriale": [28, 6], "Festivo": [31, 8]},
        "Quarta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]},
        "Quinta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]},
        "Sesta Fila (Altre)": {"Feriale": [26, 4], "Festivo": [27, 5]},
        "Spiaggia Libera / Esterna": {"Feriale": [24, 0], "Festivo": [30, 0]}
    },
    "Alta A": {
        "Prima Fila": {"Feriale": [38, 8], "Festivo": [40, 10]},
        "Seconda Fila": {"Feriale": [36, 7], "Festivo": [38, 8]},
        "Terza Fila": {"Feriale": [36, 7], "Festivo": [38, 8]},
        "Quarta Fila": {"Feriale": [34, 6], "Festivo": [36, 7]},
        "Quinta Fila": {"Feriale": [34, 6], "Festivo": [36, 7]},
        "Sesta Fila (Altre)": {"Feriale": [32, 5], "Festivo": [34, 6]},
        "Spiaggia Libera / Esterna": {"Feriale": [0, 0], "Festivo": [0, 0]}
    },
    "Alta B": {
        "Prima Fila": {"Feriale": [40, 8], "Festivo": [42, 10]},
        "Seconda Fila": {"Feriale": [38, 7], "Festivo": [40, 8]},
        "Terza Fila": {"Feriale": [38, 7], "Festivo": [40, 8]},
        "Quarta Fila": {"Feriale": [36, 6], "Festivo": [38, 7]},
        "Quinta Fila": {"Feriale": [36, 6], "Festivo": [38, 7]},
        "Sesta Fila (Altre)": {"Feriale": [34, 5], "Festivo": [36, 6]},
        "Spiaggia Libera / Esterna": {"Feriale": [0, 0], "Festivo": [0, 0]}
    },
    "Altissima": {
        "Prima Fila": {"Feriale": [56, 10], "Festivo": [58, 12]},
        "Seconda Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Terza Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Quarta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Quinta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Sesta Fila (Altre)": {"Feriale": [42, 6], "Festivo": [44, 7]},
        "Spiaggia Libera / Esterna": {"Feriale": [0, 0], "Festivo": [0, 0]}
    },
    "Peak Season": { 
        "Prima Fila": {"Feriale": [74, 14], "Festivo": [74, 14]},
        "Seconda Fila": {"Feriale": [65, 10], "Festivo": [65, 10]},
        "Terza Fila": {"Feriale": [65, 10], "Festivo": [65, 10]},
        "Quarta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]},
        "Quinta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]},
        "Sesta Fila (Altre)": {"Feriale": [49, 8], "Festivo": [49, 8]},
        "Spiaggia Libera / Esterna": {"Feriale": [0, 0], "Festivo": [0, 0]}
    }
}

PREZZI_EXTRA = {
    "Lettino Singolo": 12,
    "Ombrellone Singolo Libera": 25,
    "Postazione Esterna": 45,
    "Telo Mare Extra": 5
}

MESI_ITA = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

STATI_MAP = {
    "In Attesa (Giallo)": "Attesa",
    "Confermato (Rosso)": "Confermato",
    "Presente in Spiaggia (Viola)": "Presente",
    "Pagato (Blu)": "Pagato",
    "Presente e Pagato (Verde Acqua)": "Pres_Pagato",
    "Liberato Solo Mattina (Rivendibile)": "Libero_Mat",
    "Liberato Solo Pomeriggio (Rivendibile)": "Libero_Pom",
    "Completamente Libero / Cancella (Verde)": "Libero"
}

CONFIGURAZIONE_COLONNE = {
    "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
    "Stato": st.column_config.SelectboxColumn("Stato", options=["Attesa", "Confermato", "Presente", "Pagato", "Pres_Pagato", "Libero_Mat", "Libero_Pom", "Libero"]),
    "Fila": st.column_config.SelectboxColumn("Fila", options=list(CAPIENZA_FILE.keys())),
    "Durata": st.column_config.SelectboxColumn("Durata", options=["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"]),
    "Prezzo_Giorno": st.column_config.NumberColumn("Prezzo (€)", step=1.0),
    "Sconto": st.column_config.NumberColumn("Sconto (€)", step=1.0),
    "Persone": st.column_config.NumberColumn("Persone", min_value=1, step=1),
    "Note": st.column_config.TextColumn("Note / Memo"),
    "Operatore": st.column_config
