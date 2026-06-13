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
# 🤖 BOT TELEGRAM E BACKUP IN TEMPO REALE
# ==========================================
TELEGRAM_TOKEN = "8804050943:AAHvXVmSnEUPlvV6mj33JGGQHfhosnqcC2U"
TELEGRAM_CHAT_ID = "8663794616"  

def backup_istantaneo_telegram(azione_eseguita):
    if os.path.exists(FILE_PRENOTAZIONI):
        try:
            ora_italia = datetime.utcnow() + timedelta(hours=2)
            ora_attuale = ora_italia.strftime('%H:%M:%S')
            data_oggi = ora_italia.strftime('%d-%m-%Y')
            file_destinazione = f"Backup_Temporaneo.csv"
            
            df_bkp = pd.read_csv(FILE_PRENOTAZIONI)
            df_bkp['Data'] = pd.to_datetime(df_bkp['Data'], errors='coerce').dt.strftime('%d-%m-%Y')
            df_bkp.to_csv(file_destinazione, index=False, sep=
