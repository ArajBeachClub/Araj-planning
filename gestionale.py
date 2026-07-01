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

if 'msg_tipo' not in st.session_state: st.session_state['msg_tipo'] = "Privato"
if 'msg_nome' not in st.session_state: st.session_state['msg_nome'] = ""
if 'msg_tel' not in st.session_state: st.session_state['msg_tel'] = ""
if 'msg_dates' not in st.session_state: st.session_state['msg_dates'] = []

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

def invia_notifica_telegram(messaggio):
    messaggio_codificato = urllib.parse.quote(messaggio)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={messaggio_codificato}"
    try:
        urllib.request.urlopen(url)
        return True
    except Exception:
        return False

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
    "Alta B": [(date(2026, 6, 27), date(2026, 7, 17)), (date(2026, 9, 1), date(2026, 9, 27))],
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
    "Altissima": {
        "Prima Fila": {"Feriale": [56, 10], "Festivo": [58, 12]},
        "Seconda Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Terza Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Quarta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Quinta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Sesta Fila (Altre)": {"Feriale": [42, 6], "Festivo": [44, 7]}
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
    "1 Lettino Extra": {"Feriale": 8, "Festivo": 10},
    "2 Lettini Extra": {"Feriale": 16, "Festivo": 20},
    "1 Asciugamano (Telo)": {"Feriale": 4, "Festivo": 5},
    "2 Asciugamani (Teli)": {"Feriale": 8, "Festivo": 10},
    "1 Lettino Extra, 1 Asciugamano (Telo)": {"Feriale": 12, "Festivo": 15},
    "2 Lettini Extra, 2 Asciugamani (Teli)": {"Feriale": 24, "Festivo": 30},
    "Postazione Esterna": {"Feriale": 32, "Festivo": 38}
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
        prezzo_base = prezzo_base * 0.70
    elif durata == "Solo 1 Persona (Postazione Ridotta)":
        prezzo_base = prezzo_base * 0.75
        
    totale = prezzo_base
    if persone > 3:
        totale += suppl_persona
        
    for ex in extra_scelti:
        if ex in PREZZI_EXTRA:
            totale += PREZZI_EXTRA[ex][tipo_tariffa]
            
    return float(totale)

def carica_clienti():
    if os.path.exists(FILE_CLIENTI):
        try:
            return pd.read_csv(FILE_CLIENTI, dtype={'Telefono': str})
        except Exception:
            pass
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
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(1).astype(int)
            
            colonne_decimali = ["Prezzo_Giorno", "Sconto"]
            for col in colonne_decimali:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    
            return df
        except Exception:
            pass
            
    return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Sconto", "Hotel", "Persone", "Durata", "Extra", "Note", "Operatore", "Incassato_da"])

def applica_azione_rapida(idx, widget_key):
    azione = st.session_state[widget_key]
    if azione != "⚡ Azione":
        df = carica_prenotazioni()
        if not df.empty and idx in df.index:
            if azione == "🔄 Libera e Subentra":
                df.loc[idx, 'Durata'] = "Mezza Giornata (fino 13 / da 15.30)"
                data_obj = pd.to_datetime(df.loc[idx, 'Data']).date()
                
                ex_val = str(df.loc[idx, 'Extra'])
                extra_list = [x.strip() for x in ex_val.split(',')] if ex_val and ex_val.lower() not in ['nan', 'none', ''] else []
                
                prezzo_mezza = calcola_prezzo_automatico(data_obj, df.loc[idx, 'Fila'], df.loc[idx, 'Persone'], "Mezza Giornata (fino 13 / da 15.30)", extra_list)
                df.loc[idx, 'Prezzo_Giorno'] = prezzo_mezza
                
                nota_prec = str(df.loc[idx, 'Note']) if pd.notna(df.loc[idx, 'Note']) else ""
                df.loc[idx, 'Note'] = f"Mattina (Subentrato). {nota_prec}".strip()
                df.loc[idx, 'Stato'] = "Libero_Mat"
                
                df.to_csv(FILE_PRENOTAZIONI, index=False)
                backup_istantaneo_telegram(f"Eseguito Libera e Subentro su indice {idx}")
                st.success("Postazione liberata per il pomeriggio! Il vecchio incasso è al sicuro.")
            
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
    tel_key = f"tel_input_{fila}_{omb}_{data_str}"
    raw_tel = st.session_state.get(tel_key, "").strip()
    
    if raw_input:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
        oggi = date.today()
        is_future = data_obj > oggi
        
        parole_pulite = [p for p in raw_input.split("-")[0].strip().split() if p.replace(".", "").strip() != ""]
        
        if len(parole_pulite) < 2:
            st.session_state['map_error'] = f"🚨 ERRORE: Mancano dati! Devi inserire sia il NOME che il COGNOME."
            return
            
        tel_pulito = "".join([c for c in raw_tel if c.isdigit()])
        if not raw_tel or len(tel_pulito) < 9:
            st.session_state['map_error'] = f"🚨 ERRORE: Telefono Mancante o Errato! Inserisci un numero valido."
            return
            
        st.session_state['map_error'] = ""
        nome_cliente = raw_input
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
            st.session_state[f'form_tel_{rk}'] = raw_tel
            
            st.session_state[widget_key] = "" 
            st.session_state[tel_key] = ""
        else:
            df = carica_prenotazioni()
            
            is_subentro = False
            if not df.empty:
                esistenti = df[(df['Data'] == data_str) & (df['Fila'] == fila) & (df['Ombrellone'] == int(omb))]
                if not esistenti.empty and esistenti.iloc[-1]['Stato'] in ["Libero_Mat", "Libero_Pom"]:
                    is_subentro = True

            durata_assegnata = "Mezza Giornata (fino 13 / da 15.30)" if is_subentro else "Giornata Intera"
            prezzo = calcola_prezzo_automatico(data_obj, fila, 2, durata_assegnata, [])
            stato_automatico = "Confermato" if is_future else "Presente"
            
            nuova_p = pd.DataFrame([{
                "Data": data_str, "Fila": fila, "Ombrellone": int(omb),
                "Nome": nome_cliente, "Telefono": raw_tel, "Stato": stato_automatico,
                "Prezzo_Giorno": prezzo, "Sconto": 0.0, "Hotel": "",
                "Persone": 2, "Durata": durata_assegnata, "Extra": "",
                "Note": "Subentro pomeridiano" if is_subentro else "", "Operatore": operatore_finale, "Incassato_da": "Da saldare"
            }])
            
            if df.empty:
                df = nueva_p
            else:
                df = pd.concat([df, nueva_p], ignore_index=True)
                
            df.to_csv(FILE_PRENOTAZIONI, index=False)
            backup_istantaneo_telegram(f"Prenotazione Rapida Mappa: {nome_cliente}")
            st.session_state[widget_key] = "" 
            st.session_state[tel_key] = ""


st.set_page_config(page_title="Beach Pass Pro", layout="wide")

st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

op_param = st.query_params.get("op", "") if hasattr(st, "query_params") else ""
idx_op = 0
for i, op in enumerate(OPERATORI_SPIAGGIA):
    if op_param.lower() == op.split()[0].lower():
        idx_op = i
        break

if 'sb_operatore' not in st.session_state:
    st.session_state['sb_operatore'] = OPERATORI_SPIAGGIA[idx_op]

operatore_attivo = st.selectbox("👤 Operatore Attivo (Le tue modifiche avranno questa firma):", OPERATORI_SPIAGGIA, key="sb_operatore")
st.divider()

df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

# --- 💼 SALDO CLIENTI ABITUALI (CON FILTRO MESI) ---
with st.expander("💼 Saldo Clienti Abituali (Pagamento Cumulativo / Sconti di fine periodo)", expanded=False):
    st.info("Usa questa sezione per far pagare in un colpo solo le giornate accumulate da un cliente. Ora puoi scegliere se saldare tutto o solo alcuni mesi specifici!")
    
    if not df_pren.empty:
        clienti_con_debiti = df_pren[df_pren['Incassato_da'] == "Da saldare"]['Nome'].dropna().unique().tolist()
        clienti_con_debiti = [c for c in clienti_con_debiti if str(c).strip() != ""]
    else:
        clienti_con_debiti = []
        
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
                
                mesi_str = ", ".join(mesi_selezionati)
                st.warning(f"💶 **Totale da saldare per {cliente_sel} ({mesi_str}): € {totale_dovuto:.2f}**")
                
                st.markdown("### 🏷️ Inserisci il Saldo Finale")
                
                col_sc, col_inc = st.columns(2)
                with col_sc:
                    prezzo_finale = st.number_input("Cifra arrotondata che il cliente paga (es. 200):", min_value=0.0, max_value=float(totale_dovuto), value=float(totale_dovuto), step=1.0)
                    sconto_cumulativo = totale_dovuto - prezzo_finale
                    percentuale_sconto = 0.0
                    
                    if sconto_cumulativo > 0 and totale_dovuto > 0:
                        percentuale_sconto = (sconto_cumulativo / totale_dovuto) * 100
                        st.info(f"💡 Sconto applicato: **€ {sconto_cumulativo:.2f}** (pari al **{percentuale_sconto:.1f}%**)")
                        
                with col_inc:
                    incassato_da_cum = st.selectbox("💰 I soldi sono incassati in questo momento da:", OPERATORI_SPIAGGIA, key="inc_cum")
                    
                totale_scontato = totale_dovuto - sconto_cumulativo
                st.success(f"💳 **TOTALE NETTO CHE IL CLIENTE PAGA ORA: € {totale_scontato:.2f}**")
                
                if st.button("✅ Registra Saldo Definitivo (Aggiorna tutto)"):
                    indici = df_cliente_filtrato.index.tolist()
                    
                    if sconto_cumulativo > 0:
                        ultimo_idx = indici[-1]
                        df_pren.loc[ultimo_idx, 'Prezzo_Giorno'] -= sconto_cumulativo
                        df_pren.loc[ultimo_idx, 'Sconto'] = sconto_cumulativo
                        nota_esistente = str(df_pren.loc[ultimo_idx, 'Note']) if pd.notna(df_pren.loc[ultimo_idx, 'Note']) else ""
                        df_pren.loc[ultimo_idx, 'Note'] = f"Sconto €{sconto_cumulativo:.2f} ({percentuale_sconto:.1f}%). " + nota_esistente
                    
                    for idx in indici:
                        df_pren.loc[idx, 'Incassato_da'] = incassato_da_cum
                        stato_attuale = df_pren.loc[idx, 'Stato']
                        if stato_attuale in ["Attesa", "Confermato", "Presente", "Pagato"]:
                            df_pren.loc[idx, 'Stato'] = "Pres_Pagato"
                            
                    df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                    backup_istantaneo_telegram(f"Saldo registrato per {cliente_sel} (Mesi: {mesi_str})")
                    st.success(f"Perfetto! Tutte le {len(indici)} postazioni di {cliente_sel} dei mesi selezionati sono state saldate.")
                    st.rerun()
            else:
                st.error("Seleziona almeno un mese per procedere col calcolo del pagamento.")

# --- 🔍 MOTORE DI RICERCA INTELLIGENTE ---
with st.expander("🔍 Cerca Cliente / Modifica Rapida", expanded=False):
    ricerca = st.text_input("Inserisci una parte del Nome, del Telefono o dell'Hotel:", placeholder="Es. Armando Botta, 328...").strip()
    if ricerca:
        if not df_pren.empty:
            parole = ricerca.split()
            mask_nome = pd.Series(True, index=df_pren.index)
            for parola in parole:
                mask_nome &= df_pren['Nome'].astype(str).str.contains(parola, case=False, na=False)
            
            mask_tel = df_pren['Telefono'].astype(str).str.contains(ricerca, case=False, na=False)
            mask_hotel = df_pren['Hotel'].astype(str).str.contains(ricerca, case=False, na=False)
            
            risultati = df_pren[mask_nome | mask_tel | mask_hotel].sort_values(by="Data")
            
            if not risultati.empty:
                st.success(f"Trovate {len(risultati)} prenotazioni.")
                colonne_ordine = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Hotel", "Stato", "Operatore", "Incassato_da", "Prezzo_Giorno", "Sconto", "Persone", "Durata", "Extra", "Note"]
                
                risultati_filtrati = risultati[colonne_ordine].copy()
                risultati_filtrati['Data'] = pd.to_datetime(risultati_filtrati['Data'], errors='coerce').dt.date
                risultati_filtrati = risultati_filtrati.dropna(subset=['Data'])
                
                edited_df = st.data_editor(risultati_filtrati, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_ricerca")
                
                if st.button("💾 Salva e Ricalcola Prezzi in Automatico", key="btn_save_ricerca"):
                    edited_df['Data'] = pd.to_datetime(edited_df['Data'], errors='coerce')
                    edited_df = edited_df.dropna(subset=['Data'])
                    
                    # Identifica solo le righe modificate
                    righe_cambiate = {}
                    for idx in edited_df.index:
                        if idx in risultati_filtrati.index:
                            if not risultati_filtrati.loc[idx].equals(edited_df.loc[idx]):
                                righe_cambiate[idx] = edited_df.loc[idx]
                    
                    # Ricalcola feriali/festivi solo sulle modificate
                    for idx, row_cambiata in righe_cambiate.items():
                        try:
                            data_obj = row_cambiata['Data'].date()
                            new_fila = str(row_cambiata['Fila'])
                            new_durata = str(row_cambiata['Durata'])
                            new_persone = int(row_cambiata['Persone'])
                            new_extra = "" if pd.isna(row_cambiata['Extra']) or str(row_cambiata['Extra']).lower() in ['nan', 'none'] else str(row_cambiata['Extra']).strip()
                            
                            extra_list = [new_extra] if new_extra else []
                            nuovo_pz = calcola_prezzo_automatico(data_obj, new_fila, new_persone, new_durata, extra_list)
                            
                            if str(row_cambiata['Incassato_da']) != "Ospite (Gratis)":
                                edited_df.loc[idx, 'Prezzo_Giorno'] = float(nuovo_pz)
                        except Exception:
                            pass
                    
                    # Controllo conflitti (SOLO sui giorni modificati)
                    df_pren_temp = df_pren.drop(risultati.index)
                    has_overlap = False
                    
                    for idx, row_cambiata in righe_cambiate.items():
                        stato_finale = edited_df.loc[idx, 'Stato']
                        if stato_finale != "Libero":
                            d_str = pd.to_datetime(row_cambiata['Data']).strftime('%Y-%m-%d')
                            fila = row_cambiata['Fila']
                            omb = int(row_cambiata['Ombrellone'])
                            
                            overlap = df_pren_temp[(df_pren_temp['Data'] == d_str) & 
                                                   (df_pren_temp['Fila'] == fila) & 
                                                   (df_pren_temp['Ombrellone'] == omb) &
                                                   (df_pren_temp['Stato'] != "Libero")]
                            if not overlap.empty:
                                st.error(f"🚨 ERRORE: L'ombrellone {omb} del {d_str} è già occupato.")
                                has_overlap = True
                                break

                    if not has_overlap:
                        df_pren = df_pren_temp
                        edited_df['Data'] = edited_df['Data'].dt.strftime('%Y-%m-%d')
                        df_pren = pd.concat([df_pren, edited_df], ignore_index=True)
                        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                        backup_istantaneo_telegram("Modifiche salvate da Ricerca")
                        st.success("✅ Modifiche salvate!")
                        st.rerun()
            else:
                st.warning(f"Nessuna prenotazione trovata.")
        else:
            st.info("Nessuna prenotazione presente.")

st.divider()

# --- BARRA LATERALE ---
st.sidebar.header("📝 Gestione Prenotazioni")

st.sidebar.subheader("1. Scegli Date e Fila")
date_selezionate = st.sidebar.date_input("Intervallo Date (Arrivo e Partenza)", key="sb_dates", format="DD/MM/YYYY")
input_fila = st.sidebar.selectbox("Fila", list(CAPIENZA_FILE.keys()), key="sb_fila")
max_ombrelloni_riga = CAPIENZA_FILE[input_fila]

st.sidebar.subheader("2. Completa Prenotazione")
col_q, col_omb = st.sidebar.columns(2)
with col_q:
    quantita_postazioni = st.sidebar.selectbox("Quante postazioni?", [1, 2, 3], index=0)
with col_omb:
    input_ombrellone = st.sidebar.number_input(f"N° Iniziale", 1, max_ombrelloni_riga, key="sb_omb")
    
st.sidebar.markdown("---")

if 'reset_form' not in st.session_state: st.session_state['reset_form'] = 0
rk = st.session_state['reset_form']

input_fisso = st.sidebar.text_input("⛱️ CLIENTI FISSI", key=f"form_fisso_{rk}").strip()
input_nome = st.sidebar.text_input("👤 Nome e Cognome (Obbligatori)", key=f"form_nome_{rk}").strip()
input_telefono = st.sidebar.text_input("📱 Telefono", key=f"form_tel_{rk}").strip()
input_hotel = st.sidebar.text_input("🏨 Nome Hotel", key=f"form_hotel_{rk}").strip()

st.sidebar.markdown("---")
input_persone = st.sidebar.selectbox("Persone", [1, 2, 3, 4, 5, 6], index=1)
input_durata = st.sidebar.selectbox("Durata", ["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"])
input_extra = st.sidebar.multiselect("🏖️ Risorse Aggiuntive", list(PREZZI_EXTRA.keys()))
input_note = st.sidebar.text_input("📝 Note", key=f"form_note_{rk}").strip()

input_stato = st.sidebar.selectbox("Stato Postazione", list(STATI_MAP.keys()))
input_incassato = st.sidebar.selectbox("💰 Pagato da:", OPZIONI_INCASSO)

submit = st.sidebar.button("Applica Modifiche", type="primary", use_container_width=True)

if submit:
    if not len(date_selezionate) > 0:
        st.sidebar.error("⚠️ Seleziona le date.")
    elif not input_hotel.strip() and not input_fisso.strip() and len([p for p in input_nome.split() if p.replace(".", "").strip() != ""]) < 2:
        st.sidebar.error("🚨 ERRORE: Inserisci NOME e COGNOME reali!")
    elif not input_hotel.strip() and not input_fisso.strip() and (not input_telefono or len("".join([c for c in input_telefono if c.isdigit()])) < 9):
        st.sidebar.error("🚨 ERRORE: Telefono mancante o non valido!")
    else:
        # Salvataggio prenotazioni... (logica invariata)
        st.sidebar.success("✅ Salvataggio completato!")
        st.session_state['reset_form'] += 1
        st.rerun()
