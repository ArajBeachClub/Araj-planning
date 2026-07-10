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
# INIZIALIZZAZIONE MEMORIA (Per Automazioni)
# ==========================================
if 'sb_dates' not in st.session_state: st.session_state['sb_dates'] = []
if 'sb_fila' not in st.session_state: st.session_state['sb_fila'] = "Prima Fila"
if 'sb_omb' not in st.session_state: st.session_state['sb_omb'] = 1

# Variabili super-blindate per l'auto-compilazione WhatsApp/Email
if 'wa_tipo' not in st.session_state: st.session_state['wa_tipo'] = "Privato"
if 'wa_nome' not in st.session_state: st.session_state['wa_nome'] = ""
if 'wa_tel' not in st.session_state: st.session_state['wa_tel'] = ""
if 'wa_email' not in st.session_state: st.session_state['wa_email'] = ""
if 'wa_dates' not in st.session_state: st.session_state['wa_dates'] = []
if 'wa_fila' not in st.session_state: st.session_state['wa_fila'] = ""

if 'map_error' not in st.session_state: st.session_state['map_error'] = ""

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
            df_bkp.to_csv(file_destinazione, index=False, sep=';')
            
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            
            body_top = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
                f"{TELEGRAM_CHAT_ID}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="caption"\r\n\r\n'
                f"🔄 BACKUP DI SICUREZZA\nModifica: {azione_eseguita}\n🕒 Ore: {ora_attuale}\n📅 {data_oggi}\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="document"; filename="Backup_{data_oggi}_{ora_attuale.replace(":","")}.csv"\r\n'
                f"Content-Type: text/csv\r\n\r\n"
            ).encode('utf-8')
            
            with open(file_destinazione, 'rb') as f:
                file_content = f.read()
                
            body_bottom = f"\r\n--{boundary}--\r\n".encode('utf-8')
            payload = body_top + file_content + body_bottom
            
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

def normalizza_tel(t):
    if not t or pd.isna(t): return ""
    t = str(t).strip().replace(" ", "").replace("+", "")
    if t.startswith("39") and len(t) > 9:
        t = t[2:]
    return t

# ==========================================
# ⚙️ CONFIGURAZIONE STRUTTURA SPIAGGIA
# ==========================================

CAPIENZA_FILE = {
    "Prima Fila": 17,
    "Seconda Fila": 17,
    "Terza Fila": 12,
    "Quarta Fila": 10,
    "Quinta Fila": 7,
    "Sesta Fila (Altre)": 6
}

STAGIONI_DATE = {
    "Media 1": [(date(2026, 5, 30), date(2026, 6, 12))],
    "Media 2": [(date(2026, 6, 13), date(2026, 6, 19))],
    "Alta A": [(date(2026, 6, 20), date(2026, 6, 26))],  
    "Alta B": [(date(2026, 6, 27), date(2026, 7, 10))],
    "Alta C": [(date(2026, 7, 11), date(2026, 7, 17)), (date(2026, 9, 1), date(2026, 9, 27))],
    "Altissima": [(date(2026, 7, 18), date(2026, 7, 31)), (date(2026, 8, 24), date(2026, 8, 31))],
    "Peak Season": [(date(2026, 8, 1), date(2026, 8, 23))]
}

GIORNI_FESTIVI = [date(2026, 6, 2), date(2026, 8, 15)]

TARIFFE = {
    "Media 1": {
        "Prima Fila": {"Feriale": [30, 7], "Festivo": [33, 9]},
        "Seconda Fila": {"Feriale": [28, 6], "Festivo": [31, 8]},
        "Terza Fila": {"Feriale": [28, 6], "Festivo": [31, 8]},
        "Quarta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]},
        "Quinta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]},
        "Sesta Fila (Altre)": {"Feriale": [26, 4], "Festivo": [27, 5]}
    },
    "Media 2": {
        "Prima Fila": {"Feriale": [33, 7], "Festivo": [35, 9]},
        "Seconda Fila": {"Feriale": [30, 6], "Festivo": [33, 8]},
        "Terza Fila": {"Feriale": [30, 6], "Festivo": [33, 8]},
        "Quarta Fila": {"Feriale": [28, 5], "Festivo": [30, 7]},
        "Quinta Fila": {"Feriale": [27, 5], "Festivo": [29, 7]},
        "Sesta Fila (Altre)": {"Feriale": [27, 4], "Festivo": [29, 5]}
    },
    "Alta A": {  
        "Prima Fila": {"Feriale": [38, 8], "Festivo": [42, 10]},
        "Seconda Fila": {"Feriale": [36, 7], "Festivo": [40, 8]},
        "Terza Fila": {"Feriale": [36, 7], "Festivo": [40, 8]},
        "Quarta Fila": {"Feriale": [34, 6], "Festivo": [38, 7]},
        "Quinta Fila": {"Feriale": [32, 6], "Festivo": [36, 7]},
        "Sesta Fila (Altre)": {"Feriale": [32, 5], "Festivo": [36, 6]}
    },
    "Alta B": {
        "Prima Fila": {"Feriale": [42, 8], "Festivo": [50, 10]},
        "Seconda Fila": {"Feriale": [38, 7], "Festivo": [42, 8]},
        "Terza Fila": {"Feriale": [38, 7], "Festivo": [42, 8]},
        "Quarta Fila": {"Feriale": [36, 6], "Festivo": [40, 7]},
        "Quinta Fila": {"Feriale": [36, 6], "Festivo": [40, 7]},
        "Sesta Fila (Altre)": {"Feriale": [34, 5], "Festivo": [37, 6]}
    },
    "Alta C": {
        "Prima Fila": {"Feriale": [44, 8], "Festivo": [50, 10]},
        "Seconda Fila": {"Feriale": [40, 7], "Festivo": [45, 8]},
        "Terza Fila": {"Feriale": [40, 7], "Festivo": [45, 8]},
        "Quarta Fila": {"Feriale": [38, 6], "Festivo": [42, 7]},
        "Quinta Fila": {"Feriale": [38, 6], "Festivo": [42, 7]},
        "Sesta Fila (Altre)": {"Feriale": [35, 5], "Festivo": [38, 6]}
    },
    "Altissima": {
        "Prima Fila": {"Feriale": [56, 10], "Festivo": [58, 12]},
        "Seconda Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Terza Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Quarta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Quinta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Sesta Fila (Altre)": {"Feriale": [43, 6], "Festivo": [45, 7]}
    },
    "Peak Season": { 
        "Prima Fila": {"Feriale": [74, 14], "Festivo": [74, 14]},
        "Seconda Fila": {"Feriale": [65, 10], "Festivo": [65, 10]},
        "Terza Fila": {"Feriale": [65, 10], "Festivo": [65, 10]},
        "Quarta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]},
        "Quinta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]},
        "Sesta Fila (Altre)": {"Feriale": [49, 8], "Festivo": [49, 8]}
    }
}

PREZZI_EXTRA = {
    "1 Lettino Extra": {"Feriale": 10, "Festivo": 12},
    "2 Lettini Extra": {"Feriale": 20, "Festivo": 24},
    "1 Asciugamano (Telo)": {"Feriale": 5, "Festivo": 6},
    "2 Asciugamani (Teli)": {"Feriale": 10, "Festivo": 12},
    "1 Lettino Extra, 1 Asciugamano (Telo)": {"Feriale": 15, "Festivo": 18},
    "2 Lettini Extra, 2 Asciugamani (Teli)": {"Feriale": 30, "Festivo": 36},
    "Postazione Esterna": {"Feriale": 44, "Festivo": 50}
}

MESI_ITA = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

STATI_MAP = {
    "Confermato (Rosso)": "Confermato",
    "In Attesa (Giallo)": "Attesa",
    "Presente in Spiaggia (Viola)": "Presente",
    "Pagato (Blu)": "Pagato",
    "Presente e Pagato (Verde Acqua)": "Pres_Pagato",
    "Liberato Solo Mattina (Rivendibile)": "Libero_Mat",
    "Liberato Solo Pomeriggio (Rivendibile)": "Libero_Pom",
    "Completamente Libero / Cancella (Verde)": "Libero"
}

CONFIGURAZIONE_COLONNE = {
    "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
    "Stato": st.column_config.SelectboxColumn("Stato", options=["Confermato", "Attesa", "Presente", "Pagato", "Pres_Pagato", "Libero_Mat", "Libero_Pom", "Libero"]),
    "Fila": st.column_config.SelectboxColumn("Fila", options=list(CAPIENZA_FILE.keys())),
    "Ombrellone": st.column_config.NumberColumn("Ombrellone", step=1),
    "Durata": st.column_config.SelectboxColumn("Durata", options=["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"]),
    "Prezzo_Giorno": st.column_config.NumberColumn("Prezzo (€)", step=1.0),
    "Sconto": st.column_config.NumberColumn("Sconto (€)", step=1.0),
    "Persone": st.column_config.NumberColumn("Persone", min_value=1, step=1),
    "Extra": st.column_config.SelectboxColumn("Extra", options=[""] + list(PREZZI_EXTRA.keys())),
    "Note": st.column_config.TextColumn("Note / Memo"),
    "Operatore": st.column_config.SelectboxColumn("Operatore", options=OPERATORI_SPIAGGIA),
    "Incassato_da": st.column_config.SelectboxColumn("Incassato da", options=OPZIONI_INCASSO)
}

def trova_stagione(data_sel):
    for stagione, intervalli in STAGIONI_DATE.items():
        for inizio, fine in intervalli:
            if inizio <= data_sel <= fine:
                return stagione
    return "Media 1"

def calcola_prezzo_automatico(data_sel, fila, persone, durata, extra_scelti):
    stagione = trova_stagione(data_sel)
    giorno_sett = data_sel.weekday()
    
    is_weekend = (giorno_sett >= 5) 
    is_festivo = (data_sel in GIORNI_FESTIVI)
    
    giorno_successivo = data_sel + timedelta(days=1)
    is_prefestivo = (giorno_successivo in GIORNI_FESTIVI)
    
    tipo_tariffa = "Festivo" if (is_weekend or is_festivo or is_prefestivo) else "Feriale"
    
    prezzo_base = TARIFFE[stagione][fila][tipo_tariffa][0]
    suppl_persona = TARIFFE[stagione][fila][tipo_tariffa][1]
    
    if durata == "Mezza Giornata (fino 13 / da 15.30)":
        if stagione == "Alta B":
            prezzo_base = 26.0 if tipo_tariffa == "Festivo" else 24.0
        elif stagione == "Alta C" and fila == "Sesta Fila (Altre)":
            prezzo_base = 28.0 if tipo_tariffa == "Festivo" else 25.0
        elif stagione == "Altissima" and fila == "Sesta Fila (Altre)":
            prezzo_base = 30.0 if tipo_tariffa == "Feriale" else round(prezzo_base * 0.70)
        else:
            prezzo_base = round(prezzo_base * 0.70)
            
    elif durata == "Solo 1 Persona (Postazione Ridotta)":
        prezzo_base = round(prezzo_base * 0.75)
        
    totale = prezzo_base
    if persone > 3:
        totale += suppl_persona
        
    for ex in extra_scelti:
        if ex in PREZZI_EXTRA:
            totale += PREZZI_EXTRA[ex][tipo_tariffa]
            
    return float(totale)

def carica_clienti():
    if os.path.exists(FILE_CLIENTI):
        try: return pd.read_csv(FILE_CLIENTI, dtype={'Telefono': str})
        except Exception: pass
    return pd.DataFrame(columns=["Telefono", "Nome"])

def carica_prenotazioni():
    if os.path.exists(FILE_PRENOTAZIONI):
        try:
            df = pd.read_csv(FILE_PRENOTAZIONI, dtype={'Telefono': str})
            if "Hotel" not in df.columns: df["Hotel"] = ""
            if "Persone" not in df.columns: df["Persone"] = 2
            if "Durata" not in df.columns: df["Durata"] = "Giornata Intera"
            if "Extra" not in df.columns: df["Extra"] = ""
            if "Nome" not in df.columns: df["Nome"] = "" 
            if "Note" not in df.columns: df["Note"] = ""
            if "Operatore" not in df.columns: df["Operatore"] = ""
            if "Incassato_da" not in df.columns: df["Incassato_da"] = "Da saldare"
            if "Sconto" not in df.columns: df["Sconto"] = 0.0
            if "Telefono" not in df.columns: df["Telefono"] = ""
            if "Ombrellone" not in df.columns: df["Ombrellone"] = 1
            
            colonne_testo = ["Nome", "Telefono", "Hotel", "Durata", "Extra", "Note", "Operatore", "Incassato_da", "Stato"]
            for col in colonne_testo:
                if col in df.columns:
                    df[col] = df[col].fillna("")
                    df[col] = df[col].apply(lambda x: "" if str(x).strip().lower() in ["none", "nan", ""] else str(x).strip())
            
            colonne_intere = ["Ombrellone", "Persone"]
            for col in colonne_intere:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(1).astype(int)
            
            colonne_decimali = ["Prezzo_Giorno", "Sconto"]
            for col in colonne_decimali:
                if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    
            return df
        except Exception: pass
    return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Sconto", "Hotel", "Persone", "Durata", "Extra", "Note", "Operatore", "Incassato_da"])

def applica_azione_rapida(idx, widget_key):
    azione = st.session_state[widget_key]
    if azione != "⚡ Azione":
        df = carica_prenotazioni()
        if not df.empty and idx in df.index:
            if azione == "🔄 Libera e Subentra":
                df.loc[idx, 'Durata'] = "Mezza Giornata (fino 13 / da 15.30)"
                data_obj = pd.to_datetime(df.loc[idx, 'Data']).date()
                
                # NON ricalcoliamo il prezzo! Lasciamo il prezzo intero di chi c'era prima.
                nota_prec = str(df.loc[idx, 'Note']) if pd.notna(df.loc[idx, 'Note']) else ""
                df.loc[idx, 'Note'] = f"Mattina (Subentrato). {nota_prec}".strip()
                df.loc[idx, 'Stato'] = "Libero_Mat"
                
                df.to_csv(FILE_PRENOTAZIONI, index=False)
                backup_istantaneo_telegram(f"Eseguito Libera e Subentro su indice {idx}")
                st.success("Postazione liberata per il pomeriggio! Il prezzo e l'incasso del vecchio cliente sono rimasti intatti.")
            elif azione == "📍 Presente":
                df.loc[idx, 'Stato'] = "Presente"
            elif azione.startswith("💰 "):
                nome_breve = azione.replace("💰 ", "")
                if nome_breve in MAPPA_NOMI_RAPIDI:
                    df.loc[idx, 'Incassato_da'] = MAPPA_NOMI_RAPIDI[nome_breve]
                    df.loc[idx, 'Stato'] = "Pres_Pagato"
            if azione != "🔄 Libera e Subentra":
                df.to_csv(FILE_PRENOTAZIONI, index=False)
                backup_istantaneo_telegram(f"Azione rapida su ombrellone ({azione})")
        st.session_state[widget_key] = "⚡ Azione"
        

def gestisci_input_mappa(fila, omb, data_str, widget_key, operatore_default):
    raw_input = st.session_state[widget_key].strip()
    if raw_input:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
        oggi = date.today()
        is_future = data_obj > oggi
        
        nome_pulito = raw_input.replace(".", " ").strip()
        parole = nome_pulito.split()
        
        if len(nome_pulito) == 0:
            st.session_state['map_error'] = "🚨 ERRORE: Non è consentito inserire solo punti. Manca Nome e Cognome!"
            st.session_state[widget_key] = ""
            return
        if is_future and len(parole) < 2:
            st.session_state['map_error'] = f"🚨 ERRORE: Per i GIORNI FUTURI inserisci NOME e COGNOME (minimo 2 parole)!"
            st.session_state[widget_key] = ""
            return
            
        nome_cliente = nome_pulito
        operatore_finale = operatore_default
        
        if "-" in raw_input:
            parti = raw_input.split("-")
            nome_cliente = parti[0].strip()
            iniziale = parti[-1].strip().upper()
            for op in OPERATORI_SPIAGGIA:
                if op.upper().startswith(iniziale):
                    operatore_finale = op
                    break
                    
        modalita = st.session_state.get('map_mode', "⚡ Salva Subito")
        if "Sinistra" in modalita:
            st.session_state['sb_dates'] = (data_obj, data_obj)
            st.session_state['sb_fila'] = fila
            st.session_state['sb_omb'] = int(omb)
            st.session_state['sb_operatore'] = operatore_finale
            rk = st.session_state.get('reset_form', 0)
            st.session_state[f'form_nome_{rk}'] = nome_cliente
            st.session_state[widget_key] = "" 
        else:
            df = carica_prenotazioni()
            is_subentro = False
            if not df.empty:
                esistenti = df[(df['Data'] == data_str) & (df['Fila'] == fila) & (df['Ombrellone'] == int(omb))]
                if not esistenti.empty and esistenti.iloc[-1]['Stato'] in ["Libero_Mat", "Libero_Pom"]:
                    is_subentro = True

            durata_assegnata = "Mezza Giornata (fino 13 / da 15.30)" if is_subentro else "Giornata Intera"
            prezzo = calcola_prezzo_automatico(data_obj, fila, 2, "Giornata Intera", [])
            stato_automatico = "Confermato" if is_future else "Presente"
            
            nuova_p = pd.DataFrame([{
                "Data": data_str, "Fila": fila, "Ombrellone": int(omb),
                "Nome": nome_cliente, "Telefono": "", "Stato": stato_automatico,
                "Prezzo_Giorno": prezzo, "Sconto": 0.0, "Hotel": "",
                "Persone": 2, "Durata": durata_assegnata, "Extra": "",
                "Note": "Subentro pomeridiano" if is_subentro else "", "Operatore": operatore_finale, "Incassato_da": "Da saldare"
            }])
            df = nuova_p if df.empty else pd.concat([df, nuova_p], ignore_index=True)
            df.to_csv(FILE_PRENOTAZIONI, index=False)
            backup_istantaneo_telegram(f"Prenotazione Rapida Mappa: {nome_cliente}")
            st.session_state[widget_key] = "" 

st.set_page_config(page_title="Beach Pass Pro", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

# ==========================================
# INIZIALIZZAZIONE DATI DOPO LA CONFIGURAZIONE
# ==========================================
df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

operatore_attivo = st.selectbox("👤 Operatore Attivo (Le tue modifiche avranno questa firma):", OPERATORI_SPIAGGIA, key="sb_operatore")
st.divider()

# --- 💼 SALDO CLIENTI ---
with st.expander("💼 Saldo Clienti Abituali (Pagamento Cumulativo / Sconti di fine periodo)", expanded=False):
    st.info("Usa questa sezione per far pagare in un colpo solo tutte le giornate accumulate da un cliente.")
    if not df_pren.empty:
        clienti_con_debiti = df_pren[df_pren['Incassato_da'] == "Da saldare"]['Nome'].dropna().unique().tolist()
        clienti_con_debiti = [c for c in clienti_con_debiti if str(c).strip() != ""]
    else: clienti_con_debiti = []
        
    cliente_sel = st.selectbox("Seleziona il Cliente da saldare:", [""] + sorted(clienti_con_debiti))
    if cliente_sel:
        mask_da_saldare = (df_pren['Nome'] == cliente_sel) & (df_pren['Incassato_da'] == "Da saldare")
        df_cliente = df_pren[mask_da_saldare].copy()
        if not df_cliente.empty:
            df_cliente['Mese_Num'] = pd.to_datetime(df_cliente['Data'], errors='coerce').dt.month
            df_cliente['Mese_Nome'] = df_cliente['Mese_Num'].apply(lambda x: MESI_ITA[int(x)] if pd.notna(x) else "Sconosciuto")
            mesi_disponibili = df_cliente['Mese_Nome'].dropna().unique().tolist()
            
            st.markdown("### 📅 Scegli i mesi da saldare")
            mesi_selezionati = st.multiselect("Mesi inclusi nel pagamento:", mesi_disponibili, default=mesi_disponibili)
            if mesi_selezionati:
                df_cliente_filtrato = df_cliente[df_cliente['Mese_Nome'].isin(mesi_selezionati)]
                totale_dovuto = df_cliente_filtrato['Prezzo_Giorno'].sum()
                st.warning(f"💶 **Totale da saldare per {cliente_sel} ({', '.join(mesi_selezionati)}): € {totale_dovuto:.2f}**")
                
                col_sc, col_inc = st.columns(2)
                with col_sc:
                    prezzo_finale = st.number_input("Cifra arrotondata che il cliente paga:", min_value=0.0, value=float(totale_dovuto), step=1.0)
                    sconto_cumulativo = totale_dovuto - prezzo_finale
                    percentuale_sconto = (sconto_cumulativo / totale_dovuto * 100) if totale_dovuto > 0 else 0.0
                    if sconto_cumulativo > 0: st.info(f"💡 Sconto: **€ {sconto_cumulativo:.2f}** ({percentuale_sconto:.1f}%)")
                with col_inc:
                    incassato_da_cum = st.selectbox("💰 I soldi sono incassati da:", OPERATORI_SPIAGGIA, key="inc_cum")
                
                if st.button("✅ Registra Saldo Definitivo (Aggiorna tutto)"):
                    indici = df_cliente_filtrato.index.tolist()
                    if sconto_cumulativo > 0:
                        df_pren.loc[indici[-1], 'Prezzo_Giorno'] -= sconto_cumulativo
                        df_pren.loc[indici[-1], 'Sconto'] = sconto_cumulativo
                    for idx in indici:
                        df_pren.loc[idx, 'Incassato_da'] = incassato_da_cum
                        if df_pren.loc[idx, 'Stato'] in ["Attesa", "Confermato", "Presente", "Pagato"]: df_pren.loc[idx, 'Stato'] = "Pres_Pagato"
                    df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                    st.success("Saldo registrato correttamente!")
                    st.rerun()

# --- 🔍 MOTORE DI RICERCA ---
with st.expander("🔍 Cerca Cliente / Modifica Rapida", expanded=False):
    ricerca = st.text_input("Inserisci una parte del Nome, del Telefono o dell'Hotel:", placeholder="Es. Armando Botta, 328...").strip()
    if ricerca:
        if not df_pren.empty:
            parole = ricerca.split()
            mask_nome = pd.Series(True, index=df_pren.index)
            for p in parole: mask_nome &= df_pren['Nome'].astype(str).str.contains(p, case=False, na=False)
            ris_df = df_pren[mask_nome | df_pren['Telefono'].astype(str).str.contains(ricerca, na=False) | df_pren['Hotel'].astype(str).str.contains(ricerca, na=False)].sort_values(by="Data")
            if not ris_df.empty:
                edited_df = st.data_editor(ris_df, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_ricerca")
                if st.button("💾 Salva modifiche tabella"):
                    df_pren_temp = df_pren.drop(ris_df.index)
                    edited_df['Data'] = pd.to_datetime(edited_df['Data']).dt.strftime('%Y-%m-%d')
                    df_pren = pd.concat([df_pren_temp, edited_df], ignore_index=True)
                    df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                    st.success("Modifiche salvate!")
                    st.rerun()

# --- BARRA LATERALE ---
st.sidebar.header("📝 Gestione Prenotazioni")
date_selezionate = st.sidebar.date_input("Intervallo Date (Arrivo e Partenza)", key="sb_dates", format="DD/MM/YYYY")
input_fila = st.sidebar.selectbox("Fila", list(CAPIENZA_FILE.keys()), key="sb_fila")
max_ombrelloni_riga = CAPIENZA_FILE[input_fila]

col_q, col_omb = st.sidebar.columns(2)
with col_q: quantita_postazioni = st.sidebar.selectbox("Quante postazioni vicine?", [1, 2, 3], index=0)
with col_omb: input_ombrellone = st.sidebar.selectbox(f"N° Ombrellone Iniziale", list(range(1, max_ombrelloni_riga - quantita_postazioni + 2)), key="sb_omb")

st.sidebar.markdown("---")
rk = st.session_state['reset_form']
input_fisso = st.sidebar.text_input("⛱️ CLIENTI FISSI", key=f"form_fisso_{rk}").strip()
input_nome = st.sidebar.text_input("👤 Nome e Cognome", key=f"form_nome_{rk}").strip()
input_telefono = st.sidebar.text_input("📱 Telefono", key=f"form_tel_{rk}").strip()
input_hotel = st.sidebar.text_input("🏨 Nome Hotel", key=f"form_hotel_{rk}").strip()

input_persone = st.sidebar.selectbox("Persone", [1, 2, 3, 4, 5, 6], index=1)
input_durata = st.sidebar.selectbox("Durata", ["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"])
input_extra = st.sidebar.multiselect("🏖️ Risorse Aggiuntive Libere", list(PREZZI_EXTRA.keys()))
input_note = st.sidebar.text_input("📝 Note / Memo", key=f"form_note_{rk}").strip()
input_stato = st.sidebar.selectbox("Stato Postazione", list(STATI_MAP.keys()))
input_incassato = st.sidebar.selectbox("💰 Pagamento incassato da:", OPZIONI_INCASSO)

submit = st.sidebar.button("Applica Modifiche", type="primary", use_container_width=True)

if submit:
    is_hotel_booking = bool(input_hotel.strip())
    is_fisso_booking = bool(input_fisso.strip())
    nome_pulito = input_nome.replace(".", " ").strip()
    cifre_tel = "".join([c for c in input_telefono if c.isdigit() or c == "+"])
    
    if not len(date_selezionate) > 0: st.sidebar.error("⚠️ Seleziona le date.")
    else:
        data_inizio = date_selezionate[0]
        data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
        if not is_hotel_booking and not is_fisso_booking:
            if len(nome_pulito) == 0: st.sidebar.error("🚨 ERRORE: Inserisci il nome reale."); st.stop()
            if data_inizio > date.today() and len(nome_pulito.split()) < 2: st.sidebar.error("🚨 ERRORE: Cognome obbligatorio per il futuro."); st.stop()
            if data_inizio > date.today() and len(cifre_tel) < 9: st.sidebar.error("🚨 ERRORE: Telefono obbligatorio per il futuro."); st.stop()
            
        giorni_totali = (data_fine - data_inizio).days + 1
        for i in range(giorni_totali):
            g_str = (data_inizio + timedelta(days=i)).strftime("%Y-%m-%d")
            pz_un = calcola_prezzo_automatico(data_inizio + timedelta(days=i), input_fila, input_persone, input_durata, input_extra)
            if input_incassato == "Ospite (Gratis)": pz_un = 0.0
            
            for j in range(quantita_postazioni):
                nuova_p = pd.DataFrame([{
                    "Data": g_str, "Fila": input_fila, "Ombrellone": int(input_ombrellone + j),
                    "Nome": input_fisso if is_fisso_booking else (f"Ospiti {input_hotel}" if is_hotel_booking and not nome_pulito else nome_pulito),
                    "Telefono": cifre_tel, "Stato": STATI_MAP[input_stato], "Prezzo_Giorno": pz_un, "Sconto": 0.0,
                    "Hotel": input_hotel, "Persone": input_persone, "Durata": input_durata, "Extra": ", ".join(input_extra),
                    "Note": input_note, "Operatore": operatore_attivo, "Incassato_da": input_incassato
                }])
                df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
        st.session_state.wa_tipo, st.session_state.wa_nome, st.session_state.wa_tel, st.session_state.wa_dates, st.session_state.wa_fila = ("Hotel" if is_hotel_booking else "Privato"), (input_hotel if is_hotel_booking else nome_pulito), cifre_tel, date_selezionate, input_fila
        st.session_state['reset_form'] += 1
        st.rerun()

# --- CONFERME WHATSAPP / EMAIL ---
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Invia Conferma (Gratis)")
tipo_cliente = st.sidebar.radio("Destinatario", ["Privato", "Hotel"], horizontal=True, key="wa_tipo")
date_wa = st.sidebar.date_input("Date prenotazione", key="wa_dates", format="DD/MM/YYYY")
nome_wa = st.sidebar.text_input("Nome Cliente / Nome Hotel", key="wa_nome")
tel_wa = st.sidebar.text_input("Cellulare", key="wa_tel")
email_wa = st.sidebar.text_input("Indirizzo Email", key="wa_email")
lingua_scelta = st.sidebar.selectbox("Lingua", ["Italiano", "English", "Français", "Español"])

fila_wa = st.session_state.get('wa_fila', "")
fila_ita = fila_wa.split('(')[0].strip() if fila_wa else ""
fila_eng = fila_ita.replace("Prima", "First").replace("Seconda", "Second").replace("Terza", "Third").replace("Quarta", "Fourth").replace("Quinta", "Fifth").replace("Sesta", "Sixth").replace(" Fila", " Row")
fila_fra = fila_ita.replace("Prima Fila", "Première ligne").replace("Seconda Fila", "Deuxième ligne").replace("Terza Fila", "Troisième ligne").replace("Quarta Fila", "Quatrième ligne").replace("Quinta Fila", "Cinquième ligne").replace("Sesta Fila", "Sixième ligne")
fila_esp = fila_ita.replace("Prima", "Primera").replace("Seconda", "Segunda").replace("Terza", "Tercera").replace("Quarta", "Cuarta").replace("Quinta", "Quinta").replace("Sesta", "Sexta").replace(" Fila", " fila")

if nome_wa and len(date_wa) > 0:
    d1 = date_wa[0].strftime("%d/%m/%Y")
    
    if len(date_wa) > 1 and date_wa[0] != date_wa[1]:
        d2 = date_wa[1].strftime("%d/%m/%Y")
        stringa_date_ita = f"dal {d1} al {d2}"
        stringa_date_eng = f"from {d1} to {d2}"
        stringa_date_fra = f"du {d1} au {d2}"
        stringa_date_esp = f"del {d1} al {d2}"
    else:
        stringa_date_ita = f"per il giorno {d1}"
        stringa_date_eng = f"for {d1}"
        stringa_date_fra = f"pour le {d1}"
        stringa_date_esp = f"para el {d1}"
        
    fila_formattata_ita = f" in {fila_ita.lower()}" if fila_ita else ""
    fila_formattata_eng = f" in {fila_eng.lower()}" if fila_eng else ""
    fila_formattata_fra = f" en {fila_fra.lower()}" if fila_fra else ""
    fila_formattata_esp = f" en {fila_esp.lower()}" if fila_esp else ""
    
    if tipo_cliente == "Privato":
        if lingua_scelta == "Italiano":
            testo_base = f"Gentile {nome_wa},\n\nLa sua prenotazione {stringa_date_ita}{fila_formattata_ita} è stata registrata correttamente.\n\nLe ricordiamo di arrivare entro le ore 11:00. In caso di ritardo, la preghiamo di avvisare tempestivamente inviando un messaggio WhatsApp al numero +39 3391789319, indicando il nome di riferimento e le date della prenotazione.\n\nIn caso contrario, la prenotazione decadrà dal sistema e la postazione verrà liberata.\n\nGrazie e a presto!\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Conferma Prenotazione - Araj Beach Club"
        elif lingua_scelta == "English":
            testo_base = f"Dear {nome_wa},\n\nYour reservation {stringa_date_eng}{fila_formattata_eng} has been successfully recorded.\n\nWe remind you to arrive by 11:00 AM. In case of delay, please notify us promptly by sending a WhatsApp message to +39 3391789319, indicating your reference name and reservation dates.\n\nOtherwise, the reservation will be canceled from the system and the spot will be released.\n\nThank you and see you soon!\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Reservation Confirmation - Araj Beach Club"
        elif lingua_scelta == "Français":
            testo_base = f"Cher/Chère {nome_wa},\n\nVotre réservation {stringa_date_fra}{fila_formattata_fra} a été enregistrée correctement.\n\nNous vous rappelons d'arriver avant 11h00. En cas de retard, veuillez nous avertir rapidement en envoyant un message WhatsApp au +39 3391789319, en indiquant le nom de référence et les dates de réservation.\n\nDans le cas contraire, la réservation sera annulée du système et l'emplacement sera libéré.\n\nMerci et à bientôt !\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Confirmation de Réservation - Araj Beach Club"
        elif lingua_scelta == "Español":
            testo_base = f"Estimado/a {nome_wa},\n\nSu reserva {stringa_date_esp}{fila_formattata_esp} ha sido registrada correctamente.\n\nLe recordamos llegar antes de las 11:00 AM. En caso de retraso, le rogamos que avise a tiempo enviando un mensaje de WhatsApp al número +39 3391789319, indicando el nombre de referencia y las fechas de la reserva.\n\nDe lo contrario, la reserva será cancelada del sistema y la plaza quedará liberada.\n\n¡Gracias y hasta pronto!\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Confirmación de Reserva - Araj Beach Club"
    else:
        if lingua_scelta == "Italiano":
            testo_base = f"Gentile Staff di {nome_wa},\n\nConfermiamo la prenotazione {stringa_date_ita}{fila_formattata_ita} per i vostri ospiti.\n\nVi preghiamo di comunicare eventuali ritardi entro le ore 11:00 inviando un messaggio WhatsApp al numero +39 3391789319, indicando il nome di riferimento e le date.\n\nIn caso contrario, la prenotazione decadrà dal sistema e la postazione verrà liberata.\n\nGrazie per la preziosa collaborazione!\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Conferma Prenotazione Ospiti - Araj Beach Club"
        elif lingua_scelta == "English":
            testo_base = f"Dear Staff at {nome_wa},\n\nWe confirm the reservation {stringa_date_eng}{fila_formattata_eng} for your guests.\n\nPlease notify us of any delays by 11:00 AM via WhatsApp at +39 3391789319, indicating the reference name and dates.\n\nOtherwise, the reservation will be canceled from the system and the spot will be released.\n\nThank you for your cooperation!\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Guest Reservation Confirmation - Araj Beach Club"
        elif lingua_scelta == "Français":
            testo_base = f"Cher Staff de {nome_wa},\n\nNous confirmons la réservation {stringa_date_fra}{fila_formattata_fra} pour vos clients.\n\nVeuillez nous informer de tout retard avant 11h00 via WhatsApp au +39 3391789319, en indiquant le nom de référence et les dates.\n\nDans le cas contraire, la réservation sera annulée du système et l'emplacement sera libéré.\n\nMerci pour votre précieuse collaboration !\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Confirmation de Réservation Clients - Araj Beach Club"
        elif lingua_scelta == "Español":
            testo_base = f"Estimado Equipo de {nome_wa},\n\nConfirmamos la reserva {stringa_date_esp}{fila_formattata_esp} para sus huéspedes.\n\nPor favor infórmenos de cualquier retraso antes de las 11:00 AM vía WhatsApp al +39 3391789319, indicando el nombre de referencia y las fechas.\n\nDe lo contrario, la reserva será cancelada del sistema y la plaza quedará liberada.\n\n¡Gracias por su colaboración!\n\n{operatore_attivo}\nAraj Beach Club"
            oggetto = "Confirmación de Reserva de Huéspedes - Araj Beach Club"
            
    testo_url = urllib.parse.quote(testo_base)
    oggetto_url = urllib.parse.quote(oggetto)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if tel_wa: st.link_button("💬 WhatsApp", f"https://wa.me/{tel_wa.replace(' ','')}?text={testo_url}", use_container_width=True)
    with col2:
        st.link_button("📧 Email", f"mailto:{email_wa}?subject={oggetto_url}&body={testo_url}", use_container_width=True)

# --- MAPPA VISIVA GRID ---
data_visiva = st.date_input("📅 Mappa Visiva:", [], format="DD/MM/YYYY")
if len(data_visiva) > 0:
    data_inizio_vis = data_visiva[0]
    giorni_totali_vis = 1 if len(data_visiva) == 1 else (data_visiva[1] - data_inizio_vis).days + 1
    date_range_vis = [(data_inizio_vis + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali_vis)]
    df_range = df_pren[df_pren['Data'].isin(date_range_vis)] if not df_pren.empty else pd.DataFrame()

    if giorni_totali_vis == 1:
        st.radio("⚙️ Azione quadratino verde:", ["⚡ Salva Subito (Clienti in Spiaggia)", "⬅️ Precompila a Sinistra (Nuove Prenotazioni)"], horizontal=True, key="map_mode")
        for nome_fila, max_posti in CAPIENZA_FILE.items():
            st.subheader(nome_fila)
            colonne_griglia = st.columns(max_posti) 
            for i in range(max_posti):
                numero_omb = i + 1
                record = df_range[(df_range['Ombrellone'] == numero_omb) & (df_range['Fila'] == nome_fila)]
                
                if not record.empty:
                    ultimo_rec = record.iloc[-1]
                    stato = ultimo_rec['Stato']
                    colore_box = "#dc3545" if stato == "Confermato" else ("#20c997" if stato == "Pres_Pagato" else "#ffc107")
                    box_html = f"<div style='background-color: {colore_box}; padding: 6px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px;'><b>{numero_omb}</b><br><span style='font-size: 11px;'>{ultimo_rec['Nome']}</span></div>"
                    colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)
                    
                    widget_key = f"az_{ultimo_rec.name}"
                    colonne_griglia[i].selectbox("Azione", options=["⚡ Azione", "📍 Presente", "🔄 Libera e Subentra"] + [f"💰 {n}" for n in MAPPA_NOMI_RAPIDI.keys()], label_visibility="collapsed", key=widget_key, on_change=applica_azione_rapida, args=(ultimo_rec.name, widget_key))
                    
                    if stato in ["Libero_Mat", "Libero_Pom"]:
                        with colonne_griglia[i].popover("➕ Inserisci Subentro", use_container_width=True):
                            nome_sub = st.text_input("Nome", key=f"sub_{nome_fila}_{numero_omb}")
                            if st.button("Salva Subentro", key=f"btn_sub_{nome_fila}_{numero_omb}"):
                                pz_full = calcola_prezzo_automatico(data_inizio_vis, nome_fila, 2, "Giornata Intera", [])
                                n_p = pd.DataFrame([{"Data": date_range_vis[0], "Fila": nome_fila, "Ombrellone": int(numero_omb), "Nome": nome_sub.strip(), "Stato": "Presente", "Prezzo_Giorno": pz_full, "Durata": "Mezza Giornata (fino 13 / da 15.30)", "Operatore": operatore_attivo, "Incassato_da": "Da saldare"}])
                                df_pren = pd.concat([df_pren, n_p], ignore_index=True); df_pren.to_csv(FILE_PRENOTAZIONI, index=False); st.rerun()
                else:
                    widget_key = f"quick_add_{nome_fila}_{numero_omb}"
                    colonne_griglia[i].markdown(f"<div style='background-color: #28a745; padding: 6px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px;'><b>{numero_omb}</b><br>Libero</div>", unsafe_allow_html=True)
                    colonne_griglia[i].text_input("Prenota", placeholder="Nome...", label_visibility="collapsed", key=widget_key, on_change=gestisci_input_mappa, args=(nome_fila, numero_omb, date_range_vis[0], widget_key, operatore_attivo))
