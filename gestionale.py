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
            prezzo = calcola_prezzo_automatico(data_obj, fila, 2, durata_assegnata, [])
            stato_automatico = "Confermato" if is_future else "Presente"
            
            nuova_p = pd.DataFrame([{
                "Data": data_str, "Fila": fila, "Ombrellone": int(omb),
                "Nome": nome_cliente, "Telefono": "", "Stato": stato_automatico,
                "Prezzo_Giorno": prezzo, "Sconto": 0.0, "Hotel": "",
                "Persone": 2, "Durata": durata_assegnata, "Extra": "",
                "Note": "Subentro pomeridiano" if is_subentro else "", "Operatore": operatore_finale, "Incassato_da": "Da saldare"
            }])
            
            if df.empty:
                df = nuova_p
            else:
                df = pd.concat([df, nuova_p], ignore_index=True)
                
            df.to_csv(FILE_PRENOTAZIONI, index=False)
            backup_istantaneo_telegram(f"Prenotazione Rapida Mappa: {nome_cliente}")
            st.session_state[widget_key] = "" 


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

# --- 💼 SALDO ---
with st.expander("💼 Saldo Clienti Abituali (Pagamento Cumulativo / Sconti di fine periodo)", expanded=False):
    st.info("Usa questa sezione per far pagare in un colpo solo tutte le giornate accumulate da un cliente.")
    
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
                st.success(f"Trovate {len(risultati)} prenotazioni. Fai doppio clic sulle celle per modificarle!")
                colonne_ordine = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Hotel", "Stato", "Operatore", "Incassato_da", "Prezzo_Giorno", "Sconto", "Persone", "Durata", "Extra", "Note"]
                
                risultati_filtrati = risultati[colonne_ordine].copy()
                risultati_filtrati['Data'] = pd.to_datetime(risultati_filtrati['Data'], errors='coerce').dt.date
                risultati_filtrati = risultati_filtrati.dropna(subset=['Data'])
                
                edited_df = st.data_editor(risultati_filtrati, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_ricerca")
                
                if st.button("💾 Salva e Ricalcola Prezzi in Automatico", key="btn_save_ricerca"):
                    edited_df['Data'] = pd.to_datetime(edited_df['Data'], errors='coerce')
                    edited_df = edited_df.dropna(subset=['Data'])
                    
                    righe_cambiate = {}
                    for idx in edited_df.index:
                        if idx in risultati_filtrati.index:
                            vecchio_rec = risultati_filtrati.loc[idx]
                            nuovo_rec = edited_df.loc[idx]
                            if not vecchio_rec.equals(nuovo_rec):
                                righe_cambiate[idx] = nuovo_rec
                    
                    for idx, row_cambiata in righe_cambiate.items():
                        try:
                            old_fila = str(risultati_filtrati.loc[idx, 'Fila'])
                            new_fila = str(row_cambiata['Fila'])
                            old_durata = str(risultati_filtrati.loc[idx, 'Durata'])
                            new_durata = str(row_cambiata['Durata'])
                            old_persone = int(risultati_filtrati.loc[idx, 'Persone'])
                            new_persone = int(row_cambiata['Persone'])
                            
                            old_ex_val = risultati_filtrati.loc[idx, 'Extra']
                            new_ex_val = row_cambiata['Extra']
                            old_extra = "" if pd.isna(old_ex_val) or str(old_ex_val).lower() in ['nan', 'none'] else str(old_ex_val).strip()
                            new_extra = "" if pd.isna(new_ex_val) or str(new_ex_val).lower() in ['nan', 'none'] else str(new_ex_val).strip()
                            
                            old_prezzo = float(risultati_filtrati.loc[idx, 'Prezzo_Giorno'])
                            new_prezzo = float(row_cambiata['Prezzo_Giorno'])
                            
                            if (old_durata != new_durata or old_persone != new_persone or old_extra != new_extra or old_fila != new_fila) and (old_prezzo == new_prezzo):
                                data_obj = pd.to_datetime(row_cambiata['Data']).date()
                                extra_list = [new_extra] if new_extra else []
                                nuovo_pz = calcola_prezzo_automatico(data_obj, new_fila, new_persone, new_durata, extra_list)
                                
                                if str(row_cambiata['Incassato_da']) != "Ospite (Gratis)":
                                    edited_df.loc[idx, 'Prezzo_Giorno'] = float(nuovo_pz)
                                    edited_df.loc[idx, 'Extra'] = new_extra
                        except Exception:
                            pass
                    
                    df_pren_temp = df_pren.drop(risultati.index)
                    has_overlap = False
                    
                    for idx, row_cambiata in righe_cambiate.items():
                        inc = str(row_cambiata['Incassato_da'])
                        sto = str(row_cambiata['Stato'])
                        
                        if inc == "Ospite (Gratis)":
                            edited_df.loc[idx, 'Prezzo_Giorno'] = 0.0
                            
                        if inc not in ["", "nan", "Da saldare"]:
                            if sto == "Presente":
                                edited_df.loc[idx, 'Stato'] = "Pres_Pagato"
                            elif sto in ["Attesa", "Confermato"]:
                                edited_df.loc[idx, 'Stato'] = "Pagato"

                        stato_finale = edited_df.loc[idx, 'Stato']
                        d_str = pd.to_datetime(row_cambiata['Data']).strftime('%Y-%m-%d')
                        fila = row_cambiata['Fila']
                        omb = int(row_cambiata['Ombrellone'])

                        if stato_finale != "Libero":
                            overlap = df_pren_temp[(df_pren_temp['Data'] == d_str) & 
                                                   (df_pren_temp['Fila'] == fila) & 
                                                   (df_pren_temp['Ombrellone'] == omb) &
                                                   (df_pren_temp['Stato'] != "Libero")]
                            if not overlap.empty:
                                reale_conflitto = False
                                nome_occ = ""
                                durata_corrente = str(row_cambiata['Durata'])
                                for _, o_row in overlap.iterrows():
                                    st_es = str(o_row['Stato'])
                                    dur_es = str(o_row['Durata'])
                                    if st_es in ["Libero_Mat", "Libero_Pom"] or ("Mezza" in durata_corrente and "Mezza" in dur_es):
                                        continue
                                    else:
                                        reale_conflitto = True
                                        nome_occ = str(o_row['Nome'])
                                        break
                                
                                if reale_conflitto:
                                    st.error(f"🚨 ERRORE: Impossibile salvare! L'ombrellone {omb} in {fila} del {pd.to_datetime(d_str).strftime('%d/%m/%Y')} è già occupato da {nome_occ}.")
                                    has_overlap = True
                                    break

                    if not has_overlap:
                        df_pren = df_pren_temp
                        edited_df['Data'] = edited_df['Data'].dt.strftime('%Y-%m-%d')
                        df_pren = pd.concat([df_pren, edited_df], ignore_index=True)
                        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                        backup_istantaneo_telegram("Modifiche salvate da Ricerca")
                        st.success("✅ Modifiche salvate con successo nel database!")
                        st.rerun()
            else:
                st.warning(f"Nessuna prenotazione trovata per '{ricerca}'.")
        else:
            st.info("Nessuna prenotazione presente nel sistema al momento.")

st.divider()

# --- BARRA LATERALE ---
st.sidebar.header("📝 Gestione Prenotazioni")

st.sidebar.subheader("1. Scegli Date e Fila")
date_selezionate = st.sidebar.date_input("Intervallo Date (Arrivo e Partenza)", key="sb_dates", format="DD/MM/YYYY")
input_fila = st.sidebar.selectbox("Fila", list(CAPIENZA_FILE.keys()), key="sb_fila")
max_ombrelloni_riga = CAPIENZA_FILE[input_fila]

ombrelloni_liberi = []
if len(date_selezionate) > 0:
    data_inizio = date_selezionate[0]
    data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
    giorni_totali = (data_fine - data_inizio).days + 1
    date_range = [(data_inizio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali)]
    
    if not df_pren.empty:
        df_occupati = df_pren[(df_pren['Data'].isin(date_range)) & (df_pren['Fila'] == input_fila)]
        ombrelloni_occupati = df_occupati['Ombrellone'].unique()
    else:
        ombrelloni_occupati = []
        
    ombrelloni_liberi = [i for i in range(1, max_ombrelloni_riga + 1) if i not in ombrelloni_occupati]
    
    if ombrelloni_liberi:
        st.sidebar.success(f"✅ Liberi intera giornata:\n {', '.join(map(str, ombrelloni_liberi))}")
    else:
        st.sidebar.error("❌ Tutto esaurito in questa fila!")

st.sidebar.subheader("2. Completa Prenotazione")

col_q, col_omb = st.sidebar.columns(2)
with col_q:
    quantita_postazioni = st.sidebar.selectbox("Quante postazioni vicine?", [1, 2, 3], index=0)

max_start = max_ombrelloni_riga - quantita_postazioni + 1
with col_omb:
    opzioni_ombrelloni = list(range(1, max(2, max_start + 1)))
    if st.session_state['sb_omb'] not in opzioni_ombrelloni:
        st.session_state['sb_omb'] = opzioni_ombrelloni[0]
    input_ombrellone = st.sidebar.selectbox(f"N° Ombrellone Iniziale", opzioni_ombrelloni, key="sb_omb")
    
st.sidebar.markdown("---")

if 'reset_form' not in st.session_state:
    st.session_state['reset_form'] = 0
rk = st.session_state['reset_form']

input_fisso = st.sidebar.text_input("⛱️ CLIENTI FISSI (Solo nome, annulla obblighi)", key=f"form_fisso_{rk}").strip()
input_nome = st.sidebar.text_input("👤 Nome e Cognome (Obbligatori per futuri)", key=f"form_nome_{rk}").strip()
input_telefono = st.sidebar.text_input("📱 Telefono (Obbligatorio per futuri)", key=f"form_tel_{rk}").strip()
input_hotel = st.sidebar.text_input("🏨 Nome Hotel (Se lo scrivi, annulla obblighi)", key=f"form_hotel_{rk}").strip()

st.sidebar.markdown("---")
col_p, col_d = st.sidebar.columns(2)
with col_p:
    input_persone = st.sidebar.selectbox("Persone (PER OMBRELLONE)", [1, 2, 3, 4, 5, 6], index=1)
with col_d:
    input_durata = st.sidebar.selectbox("Durata", ["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"])

input_extra = st.sidebar.multiselect("🏖️ Risorse Aggiuntive Libere (per postazione)", list(PREZZI_EXTRA.keys()))
input_note = st.sidebar.text_input("📝 Note / Memo (es. Ospite, Omaggio, Cagnolino)", key=f"form_note_{rk}").strip()

st.sidebar.markdown("---")

input_stato = st.sidebar.selectbox("Stato Postazione", list(STATI_MAP.keys()))
input_incassato = st.sidebar.selectbox("💰 Pagamento incassato da:", OPZIONI_INCASSO, help="Seleziona chi ha preso i soldi se il cliente ha già pagato")

prezzo_consigliato_totale = 0.0
if len(date_selezionate) > 0:
    data_inizio_calc = date_selezionate[0]
    data_fine_calc = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio_calc
    giorni_totali_calc = (data_fine_calc - data_inizio_calc).days + 1
    
    for i_g in range(giorni_totali_calc):
        giorno_calc = data_inizio_calc + timedelta(days=i_g)
        pz_giorno = calcola_prezzo_automatico(giorno_calc, input_fila, input_persone, input_durata, input_extra)
        prezzo_consigliato_totale += (pz_giorno * quantita_postazioni)
    
input_prezzo = st.sidebar.number_input("Prezzo TOTALE (Tutti i giorni e postazioni) (€)", min_value=0.0, value=float(prezzo_consigliato_totale), step=1.0)

st.sidebar.markdown("---")
tipo_salvataggio = st.sidebar.radio("Se la postazione risulta già occupata:", ["Blocca (Errore)", "Sostituisci (Cancella il vecchio)", "Subentro (Tieni il vecchio per l'incasso)"])

submit = st.sidebar.button("Applica Modifiche", type="primary", use_container_width=True)

if submit:
    is_hotel_booking = bool(input_hotel.strip())
    is_fisso_booking = bool(input_fisso.strip())
    
    oggi = date.today()
    if not len(date_selezionate) > 0:
        st.sidebar.error("⚠️ Seleziona le date della prenotazione.")
    else:
        data_inizio = date_selezionate[0]
        data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
        is_future = data_inizio > oggi
        
        # ====================================================
        # NUOVA VALIDAZIONE RIGIDA: NOMI, COGNOMI, NO PUNTI, TELEFONO
        # ====================================================
        nome_pulito = input_nome.replace(".", " ").strip()
        parole_nome = nome_pulito.split()
        
        cifre_tel = "".join([c for c in input_telefono if c.isdigit() or c == "+"])
        solo_numeri = "".join([c for c in input_telefono if c.isdigit()])
        
        if not is_hotel_booking and not is_fisso_booking:
            if len(nome_pulito) == 0:
                st.sidebar.error("🚨 ERRORE: Manca il Nome o Cognome! (Non inserire solo punti)")
                st.stop()
            elif is_future and len(parole_nome) < 2:
                st.sidebar.error("🚨 ERRORE: Manca il NOME o il COGNOME! Obbligatori per le prenotazioni dei giorni futuri (nessun punto accettato).")
                st.stop()
            elif is_future and len(solo_numeri) < 9:
                st.sidebar.error("🚨 ERRORE: Il NUMERO DI TELEFONO è obbligatorio e deve essere valido (minimo 9 cifre, accetta prefissi) per i giorni futuri!")
                st.stop()
                
        nome_da_salvare = ""
        if is_fisso_booking:
            nome_da_salvare = input_fisso
            if nome_pulito:  
                nome_da_salvare += f" {nome_pulito}"
        elif is_hotel_booking and not nome_pulito:
            nome_da_salvare = f"Ospiti {input_hotel}"
        else:
            nome_da_salvare = nome_pulito
            
        giorni_totali = (data_fine - data_inizio).days + 1
        date_list_str = [(data_inizio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali)]
        ombrelloni_richiesti = [input_ombrellone + j for j in range(quantita_postazioni)]
        
        if not df_pren.empty:
            sovrapposizioni = df_pren[(df_pren['Data'].isin(date_list_str)) & (df_pren['Fila'] == input_fila) & (df_pren['Ombrellone'].isin(ombrelloni_richiesti))]
        else:
            sovrapposizioni = pd.DataFrame()
            
        stato_pulito = STATI_MAP[input_stato]
        
        conflitto_sidebar = False
        if not sovrapposizioni.empty and tipo_salvataggio == "Blocca (Errore)" and stato_pulito != "Libero":
            for _, row_conf in sovrapposizioni.iterrows():
                st_es = str(row_conf['Stato'])
                dur_es = str(row_conf['Durata'])
                if st_es in ["Libero_Mat", "Libero_Pom"] or ("Mezza" in input_durata and "Mezza" in dur_es) or st_es == "Libero":
                    continue
                else:
                    conflitto_sidebar = True
                    st.sidebar.error("🚨 ERRORE: POSTAZIONE GIÀ OCCUPATA PER L'INTERA GIORNATA!")
                    d_err = row_conf['Data']
                    d_ita = f"{d_err[8:10]}/{d_err[5:7]}/{d_err[0:4]}" if len(d_err)==10 else d_err
                    st.sidebar.warning(f"👉 Omb. {row_conf['Ombrellone']} prenotato da {row_conf['Nome']} ({d_ita})")
                    break

        if not conflitto_sidebar:
            if cifre_tel:
                tel_norm = normalizza_tel(cifre_tel)
                if not df_clienti.empty:
                    df_clienti['Tel_Norm'] = df_clienti['Telefono'].apply(normalizza_tel)
                    if tel_norm in df_clienti['Tel_Norm'].values:
                        idx = df_clienti[df_clienti['Tel_Norm'] == tel_norm].index
                        df_clienti.loc[idx, 'Nome'] = nome_da_salvare
                        df_clienti.loc[idx, 'Telefono'] = cifre_tel
                    else:
                        nuovo_c = pd.DataFrame([{"Telefono": cifre_tel, "Nome": nome_da_salvare}])
                        df_clienti = pd.concat([df_clienti, nuovo_c], ignore_index=True)
                    df_clienti = df_clienti.drop(columns=['Tel_Norm'], errors='ignore')
                else:
                    nuovo_c = pd.DataFrame([{"Telefono": cifre_tel, "Nome": nome_da_salvare}])
                    df_clienti = pd.concat([df_clienti, nuovo_c], ignore_index=True)
                df_clienti.to_csv(FILE_CLIENTI, index=False)
                
            for i in range(giorni_totali):
                giorno_corrente_obj = data_inizio + timedelta(days=i)
                giorno_corrente_str = giorno_corrente_obj.strftime("%Y-%m-%d")
                prezzo_giorno_unitario = calcola_prezzo_automatico(giorno_corrente_obj, input_fila, input_persone, input_durata, input_extra)
                
                if input_prezzo == prezzo_consigliato_totale:
                    prezzo_finale_unitario = prezzo_giorno_unitario
                else:
                    prezzo_finale_unitario = input_prezzo / (quantita_postazioni * giorni_totali)
                
                if input_incassato == "Ospite (Gratis)":
                    prezzo_finale_unitario = 0.0
                
                for j in range(quantita_postazioni):
                    omb_corrente = input_ombrellone + j
                    
                    if tipo_salvataggio == "Sostituisci (Cancella il vecchio)" and not df_pren.empty:
                        df_pren = df_pren[~((df_pren['Data'] == giorno_corrente_str) & (df_pren['Ombrellone'] == omb_corrente) & (df_pren['Fila'] == input_fila))]
                    
                    if stato_pulito != "Libero":
                        nuova_p = pd.DataFrame([{
                            "Data": giorno_corrente_str, "Fila": input_fila, "Ombrellone": int(omb_corrente),
                            "Nome": nome_da_salvare, "Telefono": cifre_tel, "Stato": stato_pulito,
                            "Prezzo_Giorno": prezzo_finale_unitario, "Sconto": 0.0, "Hotel": str(input_hotel).strip(),
                            "Persone": input_persone, "Durata": input_durata, "Extra": ", ".join(input_extra), 
                            "Note": input_note, "Operatore": operatore_attivo, "Incassato_da": input_incassato
                        }])
                        if df_pren.empty:
                            df_pren = nuova_p
                        else:
                            df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
            df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
            backup_istantaneo_telegram(f"Nuova Prenotazione dalla Barra Laterale: {nome_da_salvare}")
            
            # --- AUTO-COMPILAZIONE WHATSAPP/EMAIL BLINDATA ---
            st.session_state.wa_tipo = "Hotel" if is_hotel_booking else "Privato"
            st.session_state.wa_nome = input_hotel if is_hotel_booking else nome_da_salvare
            st.session_state.wa_tel = cifre_tel
            st.session_state.wa_dates = date_selezionate
            st.session_state.wa_fila = input_fila
            
            st.sidebar.success("✅ Salvataggio completato! I dati di conferma sono pronti in basso.")
            st.session_state['reset_form'] += 1
            st.rerun()

# --- AREA NOTIFICHE WHATSAPP E EMAIL ---
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Backup Locale")

if not df_pren.empty:
    df_backup = df_pren.copy()
    df_backup['Data'] = pd.to_datetime(df_backup['Data'], errors='coerce').dt.strftime('%d-%m-%Y')
    csv_backup = df_backup.to_csv(index=False, sep=';').encode('utf-8')
    st.sidebar.download_button(label="⬇️ Scarica su Telefono/PC", data=csv_backup, file_name=f"prenotazioni_{date.today().strftime('%d-%m-%Y')}.csv", mime="text/csv", type="primary")

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Invia Conferma (Gratis)")

operatore_msg = st.sidebar.selectbox("👤 Inviato da:", OPERATORI_SPIAGGIA, index=OPERATORI_SPIAGGIA.index(st.session_state.get('sb_operatore', OPERATORI_SPIAGGIA[0])))
tipo_cliente = st.sidebar.radio("Destinatario", ["Privato", "Hotel"], horizontal=True, key="wa_tipo")
date_wa = st.sidebar.date_input("Date prenotazione", key="wa_dates", format="DD/MM/YYYY")
nome_wa = st.sidebar.text_input("Nome Cliente / Nome Hotel", key="wa_nome")
tel_wa = st.sidebar.text_input("Cellulare (Per WhatsApp)", key="wa_tel")
email_wa = st.sidebar.text_input("Indirizzo Email", key="wa_email")
lingua_scelta = st.sidebar.selectbox("Lingua Messaggio", ["Italiano", "English", "Français", "Español"])

fila_wa = st.session_state.get('wa_fila', "")
fila_ita = fila_wa.split('(')[0].strip() if fila_wa else ""
fila_eng = fila_ita.replace("Prima", "First").replace("Seconda", "Second").replace("Terza", "Third").replace("Quarta", "Fourth").replace("Quinta", "Fifth").replace("Sesta", "Sixth").replace(" Fila", " Row")
fila_fra = fila_ita.replace("Prima Fila", "Première ligne").replace("Seconda Fila", "Deuxième ligne").replace("Terza Fila", "Troisième ligne").replace("Quarta Fila", "Quatrième ligne").replace("Quinta Fila", "Cinquième ligne").replace("Sesta Fila", "Sixième ligne")
fila_esp = fila_ita.replace("Prima", "Primera").replace("Seconda", "Segunda").replace("Terza", "Tercera").replace("Quarta", "Cuarta").replace("Quinta", "Quinta").replace("Sesta", "Sexta").replace(" Fila", " fila")

fila_formattata_ita = f" in {fila_ita.lower()}" if fila_ita else ""
fila_formattata_eng = f" in {fila_eng.lower()}" if fila_eng else ""
fila_formattata_fra = f" en {fila_fra.lower()}" if fila_fra else ""
fila_formattata_esp = f" en {fila_esp.lower()}" if fila_esp else ""

if nome_wa and len(date_wa) > 0:
    if len(date_wa) > 1 and date_wa[0] != date_wa[1]:
        d1 = date_wa[0].strftime("%d/%m/%Y")
        d2 = date_wa[1].strftime("%d/%m/%Y")
        stringa_date_ita = f"dal {d1} al {d2}"
        stringa_date_eng = f"from {d1} to {d2}"
        stringa_date_fra = f"du {d1} au {d2}"
        stringa_date_esp = f"del {d1} al {d2}"
    else:
        d1 = date_wa[0].strftime("%d/%m/%Y")
        stringa_date_ita = f"per il giorno {d1}"
        stringa_date_eng = f"for {d1}"
        stringa_date_fra = f"pour le {d1}"
        stringa_date_esp = f"para el {d1}"
        
    if tipo_cliente == "Privato":
        if lingua_scelta == "Italiano":
            testo_base = f"Gentile {nome_wa},\n\nLa sua prenotazione {stringa_date_ita}{fila_formattata_ita} è stata registrata correttamente.\n\nLe ricordiamo di arrivare entro le ore 11:00. In caso di ritardo, la preghiamo di avvisare tempestivamente inviando un messaggio WhatsApp al numero +39 3391789319, indicando il nome di riferimento e le date della prenotazione.\n\nIn caso contrario, la prenotazione decadrà dal sistema e la postazione verrà liberata.\n\nGrazie e a presto!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Conferma Prenotazione - Araj Beach Club"
        elif lingua_scelta == "English":
            testo_base = f"Dear {nome_wa},\n\nYour reservation {stringa_date_eng}{fila_formattata_eng} has been successfully recorded.\n\nWe remind you to arrive by 11:00 AM. In case of delay, please notify us promptly by sending a WhatsApp message to +39 3391789319, indicating your reference name and reservation dates.\n\nOtherwise, the reservation will be canceled from the system and the spot will be released.\n\nThank you and see you soon!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Reservation Confirmation - Araj Beach Club"
        elif lingua_scelta == "Français":
            testo_base = f"Cher/Chère {nome_wa},\n\nVotre réservation {stringa_date_fra}{fila_formattata_fra} a été enregistrée correctement.\n\nNous vous rappelons d'arriver avant 11h00. En cas de retard, veuillez nous avertir rapidement en envoyant un message WhatsApp au +39 3391789319, en indiquant le nom de référence et les dates de réservation.\n\nDans le cas contraire, la réservation sera annulée du système et l'emplacement sera libéré.\n\nMerci et à bientôt !\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Confirmation de Réservation - Araj Beach Club"
        elif lingua_scelta == "Español":
            testo_base = f"Estimado/a {nome_wa},\n\nSu reserva {stringa_date_esp}{fila_formattata_esp} ha sido registrada correctamente.\n\nLe recordamos llegar antes de las 11:00 AM. En caso de retraso, le rogamos que avise a tiempo enviando un mensaje de WhatsApp al número +39 3391789319, indicando el nombre de referencia y las fechas de la reserva.\n\nDe lo contrario, la reserva será cancelada del sistema y la plaza quedará liberada.\n\n¡Gracias y hasta pronto!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Confirmación de Reserva - Araj Beach Club"
    else:
        if lingua_scelta == "Italiano":
            testo_base = f"Gentile Staff di {nome_wa},\n\nConfermiamo la prenotazione {stringa_date_ita}{fila_formattata_ita} per i vostri ospiti.\n\nVi preghiamo di comunicare eventuali ritardi entro le ore 11:00 inviando un messaggio WhatsApp al numero +39 3391789319, indicando il nome di riferimento e le date.\n\nIn caso contrario, la prenotazione decadrà dal sistema e la postazione verrà liberata.\n\nGrazie per la preziosa collaborazione!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Conferma Prenotazione Ospiti - Araj Beach Club"
        elif lingua_scelta == "English":
            testo_base = f"Dear Staff at {nome_wa},\n\nWe confirm the reservation {stringa_date_eng}{fila_formattata_eng} for your guests.\n\nPlease notify us of any delays by 11:00 AM via WhatsApp at +39 3391789319, indicating the reference name and dates.\n\nOtherwise, the reservation will be canceled from the system and the spot will be released.\n\nThank you for your cooperation!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Guest Reservation Confirmation - Araj Beach Club"
        elif lingua_scelta == "Français":
            testo_base = f"Cher Staff de {nome_wa},\n\nNous confirmons la réservation {stringa_date_fra}{fila_formattata_fra} pour vos clients.\n\nVeuillez nous informer de tout retard avant 11h00 via WhatsApp au +39 3391789319, en indiquant le nom de référence et les dates.\n\nDans le cas contraire, la réservation sera annulée du système et l'emplacement sera libéré.\n\nMerci pour votre précieuse collaboration !\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Confirmation de Réservation Clients - Araj Beach Club"
        elif lingua_scelta == "Español":
            testo_base = f"Estimado Equipo de {nome_wa},\n\nConfirmamos la reserva {stringa_date_esp}{fila_formattata_esp} para sus huéspedes.\n\nPor favor infórmenos de cualquier retraso antes de las 11:00 AM vía WhatsApp al +39 3391789319, indicando el nombre de referencia y las fechas.\n\nDe lo contrario, la reserva será cancelada del sistema y la plaza quedará liberada.\n\n¡Gracias por su colaboración!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto = "Confirmación de Reserva de Huéspedes - Araj Beach Club"

    testo_url = urllib.parse.quote(testo_base)
    oggetto_url = urllib.parse.quote(oggetto)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if tel_wa:
            tel_pulito = tel_wa.replace(" ", "").replace("+", "")
            if not tel_pulito.startswith("39") and len(tel_pulito) < 11: tel_pulito = "39" + tel_pulito
            st.link_button("💬 WhatsApp", f"https://wa.me/{tel_pulito}?text={testo_url}", use_container_width=True)
    with col2:
        if email_wa:
            st.link_button("📧 Email", f"mailto:{email_wa}?subject={oggetto_url}&body={testo_url}", use_container_width=True)
        else:
            st.link_button("📧 Email (No Dest)", f"mailto:?subject={oggetto_url}&body={testo_url}", use_container_width=True)

# --- MAPPA VISIVA E TABELLA INTERATTIVA ---
data_visiva = st.date_input("📅 Mappa Visiva: Seleziona SINGOLA DATA (per i clienti) o UN PERIODO (per cercare disponibilità fisse):", [], format="DD/MM/YYYY")

if len(data_visiva) > 0:
    data_inizio_vis = data_visiva[0]
    data_fine_vis = data_visiva[1] if len(data_visiva) > 1 else data_inizio_vis
    giorni_totali_vis = (data_fine_vis - data_inizio_vis).days + 1
    date_range_vis = [(data_inizio_vis + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali_vis)]

    df_range = df_pren[df_pren['Data'].isin(date_range_vis)] if not df_pren.empty else pd.DataFrame()

    if giorni_totali_vis == 1:
        data_formattata_ita = f"{data_inizio_vis.day} {MESI_ITA[data_inizio_vis.month]} {data_inizio_vis.year}"
        if st.session_state.get('map_error'):
            st.error(st.session_state['map_error'])
            st.session_state['map_error'] = ""
            
        st.header(f"📅 Planning del {data_formattata_ita}")
        
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            st.radio("⚙️ Cosa succede quando scrivi in un quadratino verde?", ["⚡ Salva Subito (Clienti in Spiaggia)", "⬅️ Precompila a Sinistra (Nuove Prenotazioni)"], horizontal=True, key="map_mode")
            
        st.divider()

        def controlla_posto(numero_ombrellone, fila):
            if df_range.empty: return "#28a745", "Libero", "", "", "", None, "Libero"
            record = df_range[(df_range['Ombrellone'] == numero_ombrellone) & (df_range['Fila'] == fila)]
            if record.empty: return "#28a745", "Libero", "", "", "", None, "Libero"
            
            ultimo_record = record.iloc[-1]
            stato = ultimo_record['Stato']
            prezzo_g = ultimo_record['Prezzo_Giorno']
            pers = ultimo_record.get('Persone', 2)
            durata = ultimo_record.get('Durata', "")
            extra = ultimo_record.get('Extra', "")
            nome_c = ultimo_record.get('Nome', "")
            sconto_applicato = float(ultimo_record.get('Sconto', 0.0))
            
            operatore_val = str(ultimo_record.get('Operatore', ""))
            nome_op = operatore_val.split()[0] if operatore_val and str(operatore_val).lower() != "nan" else ""
            badge_operatore = f" ✍️ {nome_op[0].upper()}" if nome_op else ""
            
            incassato_val = str(ultimo_record.get('Incassato_da', ""))
            nome_incass = incassato_val.split()[0] if incassato_val and incassato_val not in ["nan", "Da", "Da saldare"] else ""
            badge_incassato = f" 💰 {nome_incass} |" if nome_incass else ""
            
            badge_sconto = " 📉" if sconto_applicato > 0 else ""
            badge_durata = "🌗" if "Mezza" in str(durata) else ""
            badge_extra = "➕" if extra and str(extra).lower() not in ['nan', 'none', ''] else ""
            
            hotel_c = ultimo_record.get('Hotel', "")
            hotel_html = f"<span style='font-size: 11px; color: #ffe8a1; display: block;'>🏨 {hotel_c}</span>" if hotel_c and str(hotel_c).lower() not in ['nan', 'none', ''] else ""
            
            dettagli = f"€{prezzo_g:.0f}{badge_incassato}{badge_sconto} 👤 {pers}{badge_operatore} {badge_durata}{badge_extra}"
            badge_rivendibile, colore_box = "", "#28a745"
            
            if stato == "Attesa": colore_box = "#ffc107"
            elif stato == "Confermato": colore_box = "#dc3545"
            elif stato == "Pagato": colore_box = "#007bff"
            elif stato == "Presente": colore_box = "#6f42c1"
            elif stato == "Pres_Pagato": colore_box = "#20c997" 
            elif stato == "Libero_Mat":
                colore_box = "#17a2b8"
                badge_rivendibile = "<span style='background:#fff; color:#17a2b8; padding:2px 4px; border-radius:4px; font-weight:bold; font-size:10px; display:inline-block; margin-bottom:4px;'>🌅 LIBERO MATTINA</span><br>"
            elif stato == "Libero_Pom":
                colore_box = "#17a2b8"
                badge_rivendibile = "<span style='background:#fff; color:#17a2b8; padding:2px 4px; border-radius:4px; font-weight:bold; font-size:10px; display:inline-block; margin-bottom:4px;'>🌇 LIBERO POMERIGG.</span><br>"
            
            return colore_box, f"{nome_c}", dettagli, hotel_html, badge_rivendibile, ultimo_record.name, stato

        modalita_attuale = st.session_state.get("map_mode", "⚡ Salva Subito")
        is_future_map = data_inizio_vis > date.today()

        for nome_fila, max_posti in CAPIENZA_FILE.items():
            st.subheader(nome_fila)
            colonne_griglia = st.columns(max_posti) 
            for i in range(max_posti):
                numero_omb = i + 1
                colore_box, titolo, sottotitolo, hotel_str, badge_rivend, row_idx, stato_omb = controlla_posto(numero_omb, nome_fila)
                
                etichetta = ""
                if nome_fila == "Prima Fila":
                    if numero_omb <= 6: etichetta = "1ª Fila"
                    else: etichetta = "Fisicamente in 2ª Fila"
                elif nome_fila == "Seconda Fila":
                    if numero_omb <= 6: etichetta = "2ª Fila"
                    else: etichetta = "Fisicamente in 3ª Fila"
                elif nome_fila == "Terza Fila":
                    if numero_omb <= 6: etichetta = "3ª Fila"
                    else: etichetta = "Fisicamente in 4ª Fila"
                elif nome_fila == "Quarta Fila":
                    if numero_omb <= 6: etichetta = "4ª Fila"
                    else: etichetta = "Fisicamente in 5ª Fila"
                elif nome_fila == "Quinta Fila":
                    if numero_omb <= 4: etichetta = "5ª Fila"
                    else: etichetta = "Fisicamente in 6ª Fila"
                elif nome_fila == "Sesta Fila (Altre)":
                    etichetta = "6ª Fila"
                else:
                    etichetta = nome_fila
                
                box_html = f"<div style='background-color: {colore_box}; padding: 6px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px; border: 1px solid rgba(0,0,0,0.1);'><span style='font-size: 10px; font-weight: normal; color: rgba(255,255,255,0.8); display: block;'>{etichetta}</span><span style='font-size: 16px; font-weight: bold;'>{numero_omb}</span><br><hr style='margin: 3px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);'>{badge_rivend}<span style='font-size: 11px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{titolo}</span><span style='font-size: 10px; font-weight: normal; display: block;'>{sottotitolo}</span>{hotel_str}</div>"
                colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)
                
                if row_idx is not None:
                    widget_key = f"azione_rapida_{row_idx}_{nome_fila}_{numero_omb}_{data_inizio_vis}"
                    if widget_key not in st.session_state: st.session_state[widget_key] = "⚡ Azione"
                    colonne_griglia[i].selectbox("Azione Rapida", options=["⚡ Azione", "📍 Presente", "🔄 Libera e Subentra"] + [f"💰 {nome}" for nome in MAPPA_NOMI_RAPIDI.keys()], label_visibility="collapsed", key=widget_key, on_change=applica_azione_rapida, args=(row_idx, widget_key))
                else:
                    if is_future_map and "Salva" in modalita_attuale:
                        with colonne_griglia[i].popover("➕ Prenota", use_container_width=True):
                            st.write(f"Ombrellone {numero_omb} - {nome_fila}")
                            n_key = f"nm_{nome_fila}_{numero_omb}_{data_inizio_vis}"
                            t_key = f"tl_{nome_fila}_{numero_omb}_{data_inizio_vis}"
                            
                            nome_val = st.text_input("Nome e Cognome", key=n_key, placeholder="Mario Rossi")
                            tel_val = st.text_input("Telefono obbligatorio", key=t_key, placeholder="+39...")
                            
                            if st.button("Conferma Registrazione", key=f"sv_{nome_fila}_{numero_omb}_{data_inizio_vis}"):
                                nome_pulito = nome_val.replace(".", " ").strip()
                                parole = nome_pulito.split()
                                cifre_tel = "".join([c for c in tel_val if c.isdigit() or c == "+"])
                                solo_numeri = "".join([c for c in tel_val if c.isdigit()])
                                
                                if len(nome_pulito) == 0 or len(parole) < 2:
                                    st.error("🚨 ERRORE: Manca il NOME o COGNOME! (I punti non sono accettati).")
                                elif len(solo_numeri) < 9:
                                    st.error("🚨 ERRORE: Inserisci un TELEFONO reale (minimo 9 cifre)!")
                                else:
                                    df_temp = carica_prenotazioni()
                                    pz = calcola_prezzo_automatico(data_inizio_vis, nome_fila, 2, "Giornata Intera", [])
                                    nuova_p = pd.DataFrame([{
                                        "Data": date_range_vis[0], "Fila": nome_fila, "Ombrellone": int(numero_omb),
                                        "Nome": nome_pulito, "Telefono": cifre_tel, "Stato": "Confermato",
                                        "Prezzo_Giorno": pz, "Sconto": 0.0, "Hotel": "",
                                        "Persone": 2, "Durata": "Giornata Intera", "Extra": "",
                                        "Note": "", "Operatore": operatore_attivo, "Incassato_da": "Da saldare"
                                    }])
                                    df_temp = pd.concat([df_temp, nuova_p], ignore_index=True)
                                    df_temp.to_csv(FILE_PRENOTAZIONI, index=False)
                                    backup_istantaneo_telegram(f"Prenotazione Mappa Futura: {nome_pulito}")
                                    st.rerun()
                    else:
                        widget_key = f"quick_add_{nome_fila}_{numero_omb}_{data_inizio_vis}"
                        if widget_key not in st.session_state: st.session_state[widget_key] = ""
                        colonne_griglia[i].text_input("Prenota", placeholder="✏️ Nome...", label_visibility="collapsed", key=widget_key, on_change=gestisci_input_mappa, args=(nome_fila, numero_omb, date_range_vis[0], widget_key, operatore_attivo))

    else:
        data_in_ita = data_inizio_vis.strftime("%d/%m")
        data_fin_ita = data_fine_vis.strftime("%d/%m")
        st.header(f"🗓️ Radar Disponibilità Continua ({data_in_ita} - {data_fin_ita})")
        st.info(f"💡 Visualizzazione per un periodo di **{giorni_totali_vis} giorni**. I posti **VERDI** sono liberi per tutto l'arco di tempo. I posti **ROSSI** sono occupati per almeno un giorno in questo periodo.")
        st.divider()

        def controlla_posto_periodo(numero_ombrellone, fila):
            if df_range.empty: return "#28a745", "LIBERO SEMPRE", "✅ Prenotabile fisso", ""
            record = df_range[(df_range['Ombrellone'] == numero_ombrellone) & (df_range['Fila'] == fila)]
            if record.empty:
                return "#28a745", "LIBERO SEMPRE", "✅ Prenotabile fisso", ""
            else:
                giorni_occupati = len(record['Data'].unique())
                return "#dc3545", "NON DISPONIBILE", f"Occupato {giorni_occupati}/{giorni_totali_vis} gg", ""

        for nome_fila, max_posti in CAPIENZA_FILE.items():
            st.subheader(nome_fila)
            colonne_griglia = st.columns(max_posti) 
            for i in range(max_posti):
                numero_omb = i + 1
                colore_box, titolo, sottotitolo, badge_rivend = controlla_posto_periodo(numero_omb, nome_fila)
                box_html = f"<div style='background-color: {colore_box}; padding: 8px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px; border: 1px solid rgba(0,0,0,0.1);'><span style='font-size: 14px; font-weight: bold;'>{numero_omb}</span><br><hr style='margin: 3px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);'><span style='font-size: 11px; font-weight: bold; display: block;'>{titolo}</span><span style='font-size: 10px; font-weight: normal; display: block;'>{sottotitolo}</span></div>"
                colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)

    # TABELLA MODIFICABILE 
    st.divider()
    st.subheader("📋 Elenco Dettagliato (Modificabile)")
    if not df_range.empty:
        if giorni_totali_vis > 1:
            st.warning("⚠️ Stai visualizzando e modificando i dati di PIÙ GIORNI contemporaneamente.")
        else:
            st.info("💡 Fai doppio clic sulle celle per modificare.\n\n✨ **MAGIA DEI PREZZI:** Se aggiungi Extra (Lettini/Teli) o cambi la Durata/Persone, NON SCRIVERE IL PREZZO A MANO! Scegli l'opzione dalla tendina e clicca il tasto rosso qui sotto: il computer farà il calcolo esatto al posto tuo nell'istante in cui salva!")
        
        colonne_tabella = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Operatore", "Incassato_da", "Prezzo_Giorno", "Sconto", "Persone", "Durata", "Extra", "Note"]
        if 'Hotel' in df_range.columns: 
            colonne_tabella.insert(4, "Hotel")
        
        df_range_edit = df_range[colonne_tabella].copy()
        
        df_range_edit['Data'] = pd.to_datetime(df_range_edit['Data'], errors='coerce').dt.date
        df_range_edit = df_range_edit.dropna(subset=['Data'])
        
        df_range_edit['Fila'] = pd.Categorical(df_range_edit['Fila'], categories=list(CAPIENZA_FILE.keys()), ordered=True)
        df_range_edit = df_range_edit.sort_values(by=['Data', 'Fila', 'Ombrellone'])
        df_range_edit['Fila'] = df_range_edit['Fila'].astype(str)
        
        edited_range = st.data_editor(edited_range if 'edited_range' in locals() else df_range_edit, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_oggi")
        
        if st.button("💾 Salva Modifiche e Ricalcola Prezzi in Automatico", type="primary", key="btn_salva_oggi"):
            edited_range['Data'] = pd.to_datetime(edited_range['Data'], errors='coerce')
            edited_range = edited_range.dropna(subset=['Data'])
            
            righe_cambiate_oggi = {}
            for idx in edited_range.index:
                if idx in df_range_edit.index:
                    if not df_range_edit.loc[idx].equals(edited_range.loc[idx]):
                        righe_cambiate_oggi[idx] = edited_range.loc[idx]
            
            for idx, row_cambiata in righe_cambiate_oggi.items():
                try:
                    old_fila = str(df_range_edit.loc[idx, 'Fila'])
                    new_fila = str(row_cambiata['Fila'])
                    old_durata = str(df_range_edit.loc[idx, 'Durata'])
                    new_durata = str(row_cambiata['Durata'])
                    old_persone = int(df_range_edit.loc[idx, 'Persone'])
                    new_persone = int(row_cambiata['Persone'])
                    
                    old_ex_val = df_range_edit.loc[idx, 'Extra']
                    new_ex_val = row_cambiata['Extra']
                    old_extra = "" if pd.isna(old_ex_val) or str(old_ex_val).lower() in ['nan', 'none'] else str(old_ex_val).strip()
                    new_extra = "" if pd.isna(new_ex_val) or str(new_ex_val).lower() in ['nan', 'none'] else str(new_ex_val).strip()
                    
                    old_prezzo = float(df_range_edit.loc[idx, 'Prezzo_Giorno'])
                    new_prezzo = float(row_cambiata['Prezzo_Giorno'])
                    
                    if (old_durata != new_durata or old_persone != new_persone or old_extra != new_extra or old_fila != new_fila) and (old_prezzo == new_prezzo):
                        data_obj = row_cambiata['Data'].date()
                        extra_list = [new_extra] if new_extra else []
                        nuovo_pz = calcola_prezzo_automatico(data_obj, new_fila, new_persone, new_durata, extra_list)
                        
                        if str(row_cambiata['Incassato_da']) != "Ospite (Gratis)":
                            edited_range.loc[idx, 'Prezzo_Giorno'] = float(nuovo_pz)
                            edited_range.loc[idx, 'Extra'] = new_extra
                except Exception:
                    pass
            
            df_pren_temp = df_pren.drop(df_range.index)
            has_overlap = False
            
            for idx, row_cambiata in righe_cambiate_oggi.items():
                inc = str(row_cambiata['Incassato_da'])
                sto = str(row_cambiata['Stato'])
                
                if inc == "Ospite (Gratis)":
                    edited_range.loc[idx, 'Prezzo_Giorno'] = 0.0
                    
                if inc not in ["", "nan", "Da saldare"]:
                    if sto == "Presente":
                        edited_range.loc[idx, 'Stato'] = "Pres_Pagato"
                    elif sto in ["Attesa", "Confermato"]:
                        edited_range.loc[idx, 'Stato'] = "Pagato"

                stato_finale = edited_range.loc[idx, 'Stato']
                d_str = pd.to_datetime(row_cambiata['Data']).strftime('%Y-%m-%d')
                fila = row_cambiata['Fila']
                omb = int(row_cambiata['Ombrellone'])

                if stato_finale != "Libero":
                    overlap = df_pren_temp[(df_pren_temp['Data'] == d_str) & 
                                           (df_pren_temp['Fila'] == fila) & 
                                           (df_pren_temp['Ombrellone'] == omb) &
                                           (df_pren_temp['Stato'] != "Libero")]
                    if not overlap.empty:
                        conflitto_reale = False
                        nome_occ = ""
                        durata_corrente = str(row_cambiata['Durata'])
                        for _, o_row in overlap.iterrows():
                            st_es = str(o_row['Stato'])
                            dur_es = str(o_row['Durata'])
                            if st_es in ["Libero_Mat", "Libero_Pom"] or ("Mezza" in durata_corrente and "Mezza" in dur_es):
                                continue
                            else:
                                conflitto_reale = True
                                nome_occ = str(o_row['Nome'])
                                break
                        
                        if conflitto_reale:
                            st.error(f"🚨 ERRORE: Impossibile salvare! L'ombrellone {omb} in {fila} del {pd.to_datetime(d_str).strftime('%d/%m/%Y')} è già occupato da {nome_occ}.")
                            has_overlap = True
                            break

            if not has_overlap:
                df_pren = df_pren_temp
                edited_range['Data'] = pd.to_datetime(edited_range['Data']).dt.strftime('%Y-%m-%d')
                df_pren = pd.concat([df_pren, edited_range], ignore_index=True)
                df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                backup_istantaneo_telegram("Modifiche salvate dalla tabella in basso")
                st.success("✅ Dati aggiornati! Guarda il nuovo prezzo in tabella.")
                st.rerun()
    else:
        st.info("Nessuna prenotazione registrata in questo periodo.")
