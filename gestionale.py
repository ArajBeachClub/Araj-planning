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

# ==========================================
# INIZIALIZZAZIONE MEMORIA
# ==========================================
if 'sb_dates' not in st.session_state: st.session_state['sb_dates'] = []
if 'sb_fila' not in st.session_state: st.session_state['sb_fila'] = "Prima Fila"
if 'sb_omb' not in st.session_state: st.session_state['sb_omb'] = 1
if 'reset_form' not in st.session_state: st.session_state['reset_form'] = 0

if 'wa_tipo' not in st.session_state: st.session_state['wa_tipo'] = "Privato"
if 'wa_nome' not in st.session_state: st.session_state['wa_nome'] = ""
if 'wa_tel' not in st.session_state: st.session_state['wa_tel'] = ""
if 'wa_email' not in st.session_state: st.session_state['wa_email'] = ""
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
# 🤖 BOT TELEGRAM (RIPRISTINATO E POTENZIATO)
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
# ⚙️ CONFIGURAZIONE STRUTTURA E TARIFFE 2026
# ==========================================
CAPIENZA_FILE = {
    "Prima Fila": 21,    # Aggiunti 4 ombrelloni
    "Seconda Fila": 21,  # Aggiunti 4 ombrelloni
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

# Configurazioni pulite per rimuovere lo sconto dalla visuale
CONFIGURAZIONE_COLONNE = {
    "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
    "Stato": st.column_config.SelectboxColumn("Stato", options=["Confermato", "Attesa", "Presente", "Pagato", "Pres_Pagato", "Libero_Mat", "Libero_Pom", "Libero"]),
    "Fila": st.column_config.SelectboxColumn("Fila", options=list(CAPIENZA_FILE.keys())),
    "Ombrellone": st.column_config.NumberColumn("Ombrellone", step=1),
    "Durata": st.column_config.SelectboxColumn("Durata", options=["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"]),
    "Prezzo_Giorno": st.column_config.NumberColumn("Prezzo (€)", step=1.0),
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
    return "Alta B"

def calcola_prezzo_automatico(data_sel, fila, persone, durata, extra_scelti):
    stagione = trova_stagione(data_sel)
    giorno_sett = data_sel.weekday()
    tipo_tariffa = "Festivo" if (giorno_sett >= 5 or data_sel in GIORNI_FESTIVI or (data_sel + timedelta(days=1)) in GIORNI_FESTIVI) else "Feriale"
    
    prezzo_base = TARIFFE[stagione][fila][tipo_tariffa][0]
    suppl_persona = TARIFFE[stagione][fila][tipo_tariffa][1]
    
    # NESSUNA MOLTIPLICAZIONE: solo sottrazione per le durate ridotte
    if durata == "Mezza Giornata (fino 13 / da 15.30)":
        prezzo_base -= 10.0
    elif durata == "Solo 1 Persona (Postazione Ridotta)":
        prezzo_base -= 5.0
        
    totale = prezzo_base
    if persone > 3:
        totale += suppl_persona
        
    # NESSUNA MOLTIPLICAZIONE: Somma pura e semplice
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
    colonne_base = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Sconto", "Hotel", "Persone", "Durata", "Extra", "Note", "Operatore", "Incassato_da"]
    if os.path.exists(FILE_PRENOTAZIONI):
        try:
            df = pd.read_csv(FILE_PRENOTAZIONI, dtype={'Telefono': str})
            for col in colonne_base:
                if col not in df.columns: df[col] = ""
                    
            df['Nome'] = df['Nome'].fillna("").apply(lambda x: "" if str(x).strip().lower() in ["none", "nan", ""] else str(x).strip())
            df['Hotel'] = df['Hotel'].fillna("").apply(lambda x: "" if str(x).strip().lower() in ["none", "nan", ""] else str(x).strip())
            df['Note'] = df['Note'].fillna("").apply(lambda x: "" if str(x).strip().lower() in ["none", "nan", ""] else str(x).strip())
            df['Extra'] = df['Extra'].fillna("").apply(lambda x: "" if str(x).strip().lower() in ["none", "nan", ""] else str(x).strip())
            
            df['Ombrellone'] = pd.to_numeric(df['Ombrellone'], errors='coerce').fillna(1).astype(int)
            df['Persone'] = pd.to_numeric(df['Persone'], errors='coerce').fillna(2).astype(int)
            df['Prezzo_Giorno'] = pd.to_numeric(df['Prezzo_Giorno'], errors='coerce').fillna(0.0)
            df['Sconto'] = pd.to_numeric(df['Sconto'], errors='coerce').fillna(0.0)
            return df
        except Exception: 
            pass
    return pd.DataFrame(columns=colonne_base)

def applica_azione_rapida(idx, widget_key):
    azione = st.session_state[widget_key]
    if azione != "⚡ Azione":
        df = carica_prenotazioni()
        if not df.empty and idx in df.index:
            if azione == "🔄 Libera e Subentra":
                df.loc[idx, 'Durata'] = "Mezza Giornata (fino 13 / da 15.30)"
                nota_prec = str(df.loc[idx, 'Note']) if pd.notna(df.loc[idx, 'Note']) else ""
                df.loc[idx, 'Note'] = f"Mattina (Subentrato). {nota_prec}".strip()
                df.loc[idx, 'Stato'] = "Libero_Mat"
                df.to_csv(FILE_PRENOTAZIONI, index=False)
                backup_istantaneo_telegram(f"Azione: Libera e Subentro su {idx}")
                st.success("Postazione liberata per il pomeriggio! Il prezzo del vecchio cliente è intatto.")
            elif azione == "📍 Presente":
                df.loc[idx, 'Stato'] = "Presente"
                df.to_csv(FILE_PRENOTAZIONI, index=False)
                backup_istantaneo_telegram(f"Azione: Segnato Presente su {idx}")
            elif azione.startswith("💰 "):
                nome_breve = azione.replace("💰 ", "")
                if nome_breve in MAPPA_NOMI_RAPIDI:
                    df.loc[idx, 'Incassato_da'] = MAPPA_NOMI_RAPIDI[nome_breve]
                    df.loc[idx, 'Stato'] = "Pres_Pagato"
                    df.to_csv(FILE_PRENOTAZIONI, index=False)
                    backup_istantaneo_telegram(f"Azione: Pagamento registrato su {idx} da {nome_breve}")
        st.session_state[widget_key] = "⚡ Azione"


st.set_page_config(page_title="Beach Pass Pro", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

operatore_attivo = st.selectbox("👤 Operatore Attivo (Le tue modifiche avranno questa firma):", OPERATORI_SPIAGGIA, key="sb_operatore")
st.divider()

# --- 🔍 MOTORE DI RICERCA (SALVA ISTANTANEO) ---
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
                # Ho rimosso 'Sconto' dalla visualizzazione per farti lavorare meglio
                colonne_ordine = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Hotel", "Stato", "Operatore", "Incassato_da", "Prezzo_Giorno", "Persone", "Durata", "Extra", "Note"]
                
                risultati_filtrati = risultati[colonne_ordine].copy()
                risultati_filtrati['Data'] = pd.to_datetime(risultati_filtrati['Data'], errors='coerce').dt.date
                risultati_filtrati = risultati_filtrati.dropna(subset=['Data'])
                
                st.info("💡 Fai le tue modifiche direttamente nelle celle (o cancella con il cestino) e poi clicca il pulsante qui sotto.")
                edited_search = st.data_editor(risultati_filtrati, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE)
                
                if st.button("💾 Salva Modifiche (Ricerca)", type="primary"):
                    edited_search['Data'] = pd.to_datetime(edited_search['Data'], errors='coerce')
                    edited_search = edited_search.dropna(subset=['Data'])
                    
                    for idx in edited_search.index:
                        row_new = edited_search.loc[idx]
                        if idx in risultati_filtrati.index:
                            row_old = risultati_filtrati.loc[idx]
                            old_fila, new_fila = str(row_old['Fila']), str(row_new['Fila'])
                            old_durata, new_durata = str(row_old['Durata']), str(row_new['Durata'])
                            old_persone, new_persone = int(row_old['Persone']), int(row_new['Persone'])
                            old_prezzo, new_prezzo = float(row_old['Prezzo_Giorno']), float(row_new['Prezzo_Giorno'])
                            
                            old_extra = "" if pd.isna(row_old['Extra']) else str(row_old['Extra']).strip()
                            new_extra = "" if pd.isna(row_new['Extra']) else str(row_new['Extra']).strip()
                            
                            if (old_durata != new_durata or old_persone != new_persone or old_extra != new_extra or old_fila != new_fila) and (old_prezzo == new_prezzo):
                                pz = calcola_prezzo_automatico(row_new['Data'].date(), new_fila, new_persone, new_durata, [new_extra] if new_extra else [])
                                edited_search.loc[idx, 'Prezzo_Giorno'] = float(pz)
                                edited_search.loc[idx, 'Extra'] = new_extra
                                
                        inc = str(edited_search.loc[idx, 'Incassato_da'])
                        sto = str(edited_search.loc[idx, 'Stato'])
                        
                        # Blocco Ospiti = €0.0
                        if inc == "Ospite (Gratis)": edited_search.loc[idx, 'Prezzo_Giorno'] = 0.0
                        if inc not in ["", "nan", "Da saldare"]:
                            if sto == "Presente": edited_search.loc[idx, 'Stato'] = "Pres_Pagato"
                            elif sto in ["Attesa", "Confermato"]: edited_search.loc[idx, 'Stato'] = "Pagato"

                    edited_search['Data'] = edited_search['Data'].dt.strftime('%Y-%m-%d')
                    df_pren_new = df_pren.drop(index=risultati_filtrati.index)
                    df_pren_new = pd.concat([df_pren_new, edited_search], ignore_index=True)
                    df_pren_new.to_csv(FILE_PRENOTAZIONI, index=False)
                    backup_istantaneo_telegram("Modifiche salvate da Ricerca Clienti")
                    st.success("✅ Modifiche salvate con successo nel database e inviate al Backup!")
                    st.rerun()
            else:
                st.warning(f"Nessuna prenotazione trovata per '{ricerca}'.")
        else:
            st.info("Nessuna prenotazione presente nel sistema al momento.")

# --- BARRA LATERALE E FORM PRENOTAZIONI ---
st.sidebar.header("📝 Gestione Prenotazioni")
date_selezionate = st.sidebar.date_input("Intervallo Date (Arrivo e Partenza)", key="sb_dates", format="DD/MM/YYYY")
input_fila = st.sidebar.selectbox("Fila", list(CAPIENZA_FILE.keys()), key="sb_fila")
max_ombrelloni_riga = CAPIENZA_FILE[input_fila]

if len(date_selezionate) > 0:
    data_inizio = date_selezionate[0]
    data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
    giorni_totali = (data_fine - data_inizio).days + 1
    date_range = [(data_inizio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali)]
    
    if not df_pren.empty:
        df_occupati = df_pren[(df_pren['Data'].isin(date_range)) & (df_pren['Fila'] == input_fila) & (df_pren['Stato'] != 'Libero')]
        ombrelloni_occupati = df_occupati['Ombrellone'].unique()
    else:
        ombrelloni_occupati = []
        
    ombrelloni_liberi = [i for i in range(1, max_ombrelloni_riga + 1) if i not in ombrelloni_occupati]
    if ombrelloni_liberi:
        st.sidebar.success(f"✅ Liberi intera giornata:\n {', '.join(map(str, ombrelloni_liberi))}")
    else:
        st.sidebar.error("❌ Tutto esaurito in questa fila!")

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
            
            # Blocco Ospiti = €0.0
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
        backup_istantaneo_telegram(f"Nuova Prenotazione inserita dalla barra laterale")
        st.session_state.wa_tipo, st.session_state.wa_nome, st.session_state.wa_tel, st.session_state.wa_dates, st.session_state.wa_fila = ("Hotel" if is_hotel_booking else "Privato"), (input_hotel if is_hotel_booking else nome_pulito), cifre_tel, date_selezionate, input_fila
        st.session_state['reset_form'] += 1
        st.rerun()

# --- MAPPA VISIVA GRID ---
data_visiva = st.date_input("📅 Mappa Visiva:", [], format="DD/MM/YYYY")
if len(data_visiva) > 0:
    data_inizio_vis = data_visiva[0]
    data_fine_vis = data_visiva[1] if len(data_visiva) > 1 else data_inizio_vis
    giorni_totali_vis = (data_fine_vis - data_inizio_vis).days + 1
    date_range_vis = [(data_inizio_vis + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali_vis)]
    df_range = df_pren[df_pren['Data'].isin(date_range_vis)] if not df_pren.empty else pd.DataFrame()

    if giorni_totali_vis == 1:
        st.radio("⚙️ Azione quadratino verde:", ["⚡ Salva Subito (Clienti in Spiaggia)", "⬅️ Precompila a Sinistra (Nuove Prenotazioni)"], horizontal=True, key="map_mode")
        modalita_attuale = st.session_state.get("map_mode", "⚡ Salva Subito")
        
        for nome_fila, max_posti in CAPIENZA_FILE.items():
            st.subheader(nome_fila)
            colonne_griglia = st.columns(max_posti) 
            for i in range(max_posti):
                numero_omb = i + 1
                record = df_range[(df_range['Ombrellone'] == numero_omb) & (df_range['Fila'] == nome_fila) & (df_range['Stato'] != 'Libero')]
                
                etichetta = ""
                if nome_fila == "Prima Fila": etichetta = "1ª Fila" if numero_omb <= 6 else "Fisicamente in 2ª Fila"
                elif nome_fila == "Seconda Fila": etichetta = "2ª Fila" if numero_omb <= 6 else "Fisicamente in 3ª Fila"
                elif nome_fila == "Terza Fila": etichetta = "3ª Fila" if numero_omb <= 6 else "Fisicamente in 4ª Fila"
                elif nome_fila == "Quarta Fila": etichetta = "4ª Fila" if numero_omb <= 6 else "Fisicamente in 5ª Fila"
                elif nome_fila == "Quinta Fila": etichetta = "5ª Fila" if numero_omb <= 4 else "Fisicamente in 6ª Fila"
                elif nome_fila == "Sesta Fila (Altre)": etichetta = "6ª Fila"
                else: etichetta = nome_fila
                
                if not record.empty:
                    ultimo_rec = record.iloc[-1]
                    stato = ultimo_rec['Stato']
                    
                    if stato == "Attesa": colore_box = "#ffc107"
                    elif stato == "Confermato": colore_box = "#dc3545"
                    elif stato == "Pagato": colore_box = "#007bff"
                    elif stato == "Presente": colore_box = "#6f42c1"
                    elif stato == "Pres_Pagato": colore_box = "#20c997" 
                    elif stato in ["Libero_Mat", "Libero_Pom"]: colore_box = "#17a2b8"
                    else: colore_box = "#6c757d"
                    
                    pers = ultimo_rec.get('Persone', 2)
                    pz = float(ultimo_rec.get('Prezzo_Giorno', 0.0))
                    nome_c = ultimo_rec.get('Nome', "")
                    hotel_c = str(ultimo_rec.get('Hotel', ""))
                    
                    operatore_val = str(ultimo_rec.get('Operatore', ""))
                    badge_op = f" ✍️ {operatore_val.split()[0][0].upper()}" if operatore_val and operatore_val.lower() != "nan" else ""
                    
                    inc_val = str(ultimo_rec.get('Incassato_da', ""))
                    badge_inc = f" 💰 {inc_val.split()[0]} |" if inc_val and inc_val not in ["nan", "Da", "Da saldare"] else ""
                    
                    extra_val = str(ultimo_rec.get('Extra', ""))
                    badge_ex = "➕" if extra_val and extra_val.lower() not in ['nan', 'none', ''] else ""
                    badge_dur = "🌗" if "Mezza" in str(ultimo_rec.get('Durata', "")) else ""
                    
                    str_hotel = f"<span style='font-size: 11px; color: #ffe8a1; display: block;'>🏨 {hotel_c}</span>" if hotel_c and hotel_c.lower() not in ['nan', 'none', ''] else ""
                    
                    box_html = f"""
                    <div style='background-color: {colore_box}; padding: 6px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px; border: 1px solid rgba(0,0,0,0.1);'>
                        <span style='font-size: 10px; font-weight: normal; color: rgba(255,255,255,0.8); display: block;'>{etichetta}</span>
                        <span style='font-size: 16px; font-weight: bold;'>{numero_omb}</span><br>
                        <hr style='margin: 3px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);'>
                        <span style='font-size: 11px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{nome_c}</span>
                        <span style='font-size: 10px; font-weight: normal; display: block;'>€{pz:.0f}{badge_inc} 👤 {pers}{badge_op} {badge_dur}{badge_ex}</span>
                        {str_hotel}
                    </div>
                    """
                    colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)
                    
                    widget_key = f"az_{ultimo_rec.name}"
                    colonne_griglia[i].selectbox("Azione", options=["⚡ Azione", "📍 Presente", "🔄 Libera e Subentra"] + [f"💰 {n}" for n in MAPPA_NOMI_RAPIDI.keys()], label_visibility="collapsed", key=widget_key, on_change=applica_azione_rapida, args=(ultimo_rec.name, widget_key))
                    
                    if stato in ["Libero_Mat", "Libero_Pom"]:
                        with colonne_griglia[i].popover("➕ Inserisci Subentro", use_container_width=True):
                            nome_sub = st.text_input("Nome Nuovo Cliente", key=f"sub_{nome_fila}_{numero_omb}")
                            if st.button("Salva Subentro", key=f"btn_sub_{nome_fila}_{numero_omb}"):
                                pz_full = calcola_prezzo_automatico(data_inizio_vis, nome_fila, 2, "Giornata Intera", [])
                                n_p = pd.DataFrame([{"Data": date_range_vis[0], "Fila": nome_fila, "Ombrellone": int(numero_omb), "Nome": nome_sub.strip(), "Stato": "Presente", "Prezzo_Giorno": pz_full, "Durata": "Mezza Giornata (fino 13 / da 15.30)", "Operatore": operatore_attivo, "Incassato_da": "Da saldare"}])
                                df_pren = pd.concat([df_pren, n_p], ignore_index=True)
                                df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                                backup_istantaneo_telegram(f"Subentro creato: {nome_sub}")
                                st.rerun()
                else:
                    box_html = f"""
                    <div style='background-color: #28a745; padding: 6px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px; border: 1px solid rgba(0,0,0,0.1);'>
                        <span style='font-size: 10px; font-weight: normal; color: rgba(255,255,255,0.8); display: block;'>{etichetta}</span>
                        <span style='font-size: 16px; font-weight: bold;'>{numero_omb}</span><br>
                        <hr style='margin: 3px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);'>
                        <span style='font-size: 11px; font-weight: normal; display: block;'>Libero</span>
                    </div>
                    """
                    colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)
                    
                    if "Salva" in modalita_attuale:
                        with colonne_griglia[i].popover("➕ Prenota", use_container_width=True):
                            n_key = f"nm_{nome_fila}_{numero_omb}_{data_inizio_vis}"
                            t_key = f"tl_{nome_fila}_{numero_omb}_{data_inizio_vis}"
                            nome_val = st.text_input("Nome e Cognome", key=n_key)
                            tel_val = st.text_input("Telefono (Solo per futuro)", key=t_key)
                            
                            if st.button("Conferma", key=f"sv_{nome_fila}_{numero_omb}_{data_inizio_vis}"):
                                nome_pulito = nome_val.replace(".", " ").strip()
                                is_future = data_inizio_vis > date.today()
                                if len(nome_pulito) == 0: st.error("🚨 Inserisci il nome!")
                                elif is_future and len(nome_pulito.split()) < 2: st.error("🚨 Inserisci NOME e COGNOME per il futuro!")
                                elif is_future and len("".join([c for c in tel_val if c.isdigit()])) < 9: st.error("🚨 Inserisci un TELEFONO reale!")
                                else:
                                    pz = calcola_prezzo_automatico(data_inizio_vis, nome_fila, 2, "Giornata Intera", [])
                                    nuova_p = pd.DataFrame([{"Data": date_range_vis[0], "Fila": nome_fila, "Ombrellone": int(numero_omb), "Nome": nome_pulito, "Telefono": tel_val, "Stato": "Confermato" if is_future else "Presente", "Prezzo_Giorno": pz, "Sconto": 0.0, "Hotel": "", "Persone": 2, "Durata": "Giornata Intera", "Extra": "", "Note": "", "Operatore": operatore_attivo, "Incassato_da": "Da saldare"}])
                                    df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
                                    df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                                    backup_istantaneo_telegram(f"Prenotazione rapida mappa: {nome_pulito}")
                                    st.rerun()
                    else:
                        if colonne_griglia[i].button("⬅️ Invia", key=f"snd_{nome_fila}_{numero_omb}", use_container_width=True):
                            st.session_state['sb_dates'] = (data_inizio_vis, data_inizio_vis)
                            st.session_state['sb_fila'] = nome_fila
                            st.session_state['sb_omb'] = int(numero_omb)
                            st.rerun()
    else:
        data_in_ita = data_inizio_vis.strftime("%d/%m")
        data_fin_ita = data_fine_vis.strftime("%d/%m")
        st.header(f"🗓️ Radar Disponibilità Continua ({data_in_ita} - {data_fin_ita})")
        for nome_fila, max_posti in CAPIENZA_FILE.items():
            st.subheader(nome_fila)
            colonne_griglia = st.columns(max_posti) 
            for i in range(max_posti):
                numero_omb = i + 1
                record = df_range[(df_range['Ombrellone'] == numero_omb) & (df_range['Fila'] == nome_fila) & (df_range['Stato'] != 'Libero')]
                if record.empty:
                    box_html = f"<div style='background-color: #28a745; padding: 8px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px;'><b>{numero_omb}</b><br><span style='font-size: 11px;'>Libero Sempre</span></div>"
                else:
                    giorni_occupati = len(record['Data'].unique())
                    box_html = f"<div style='background-color: #dc3545; padding: 8px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px;'><b>{numero_omb}</b><br><span style='font-size: 11px;'>Occupato {giorni_occupati}/{giorni_totali_vis}gg</span></div>"
                colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)

    # TABELLA MODIFICABILE ELENCO DETTAGLIATO
    st.divider()
    st.subheader("📋 Elenco Dettagliato (Modificabile)")
    if not df_range.empty:
        # Niente Sconto
        colonne_tabella = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Operatore", "Incassato_da", "Prezzo_Giorno", "Persone", "Durata", "Extra", "Note"]
        if 'Hotel' in df_range.columns: colonne_tabella.insert(4, "Hotel")
        
        df_range_edit = df_range[colonne_tabella].copy()
        df_range_edit['Data'] = pd.to_datetime(df_range_edit['Data'], errors='coerce').dt.date
        df_range_edit = df_range_edit.dropna(subset=['Data'])
        
        ordine_file = {k: i for i, k in enumerate(CAPIENZA_FILE.keys())}
        df_range_edit['Ord_Fila'] = df_range_edit['Fila'].map(ordine_file)
        df_range_edit = df_range_edit.sort_values(by=['Data', 'Ord_Fila', 'Ombrellone']).drop(columns=['Ord_Fila'])
        
        st.info("💡 Fai le tue modifiche direttamente nelle celle (o cancella con il cestino) e poi clicca il pulsante qui sotto.")
        edited_range = st.data_editor(df_range_edit, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE)
        
        if st.button("💾 Salva Modifiche e Ricalcola (Elenco Dettagliato)", type="primary"):
            edited_range['Data'] = pd.to_datetime(edited_range['Data'], errors='coerce')
            edited_range = edited_range.dropna(subset=['Data'])
            
            for idx in edited_range.index:
                row_new = edited_range.loc[idx]
                if idx in df_range_edit.index:
                    row_old = df_range_edit.loc[idx]
                    old_fila, new_fila = str(row_old['Fila']), str(row_new['Fila'])
                    old_durata, new_durata = str(row_old['Durata']), str(row_new['Durata'])
                    old_persone, new_persone = int(row_old['Persone']), int(row_new['Persone'])
                    old_prezzo, new_prezzo = float(row_old['Prezzo_Giorno']), float(row_new['Prezzo_Giorno'])
                    
                    old_ex_val = row_old['Extra']
                    new_extra = "" if pd.isna(row_new['Extra']) else str(row_new['Extra']).strip()
                    old_extra = "" if pd.isna(old_ex_val) else str(old_ex_val).strip()
                    
                    if (old_durata != new_durata or old_persone != new_persone or old_extra != new_extra or old_fila != new_fila) and (old_prezzo == new_prezzo):
                        nuovo_pz = calcola_prezzo_automatico(row_new['Data'].date(), new_fila, new_persone, new_durata, [new_extra] if new_extra else [])
                        edited_range.loc[idx, 'Prezzo_Giorno'] = float(nuovo_pz)
                        edited_range.loc[idx, 'Extra'] = new_extra
                        
                inc = str(edited_range.loc[idx, 'Incassato_da'])
                sto = str(edited_range.loc[idx, 'Stato'])
                
                # Blocco Ospiti = €0.0
                if inc == "Ospite (Gratis)": edited_range.loc[idx, 'Prezzo_Giorno'] = 0.0
                if inc not in ["", "nan", "Da saldare"]:
                    if sto == "Presente": edited_range.loc[idx, 'Stato'] = "Pres_Pagato"
                    elif sto in ["Attesa", "Confermato"]: edited_range.loc[idx, 'Stato'] = "Pagato"

            edited_range['Data'] = pd.to_datetime(edited_range['Data']).dt.strftime('%Y-%m-%d')
            df_pren_new = df_pren.drop(index=df_range_edit.index)
            df_pren_new = pd.concat([df_pren_new, edited_range], ignore_index=True)
            df_pren_new.to_csv(FILE_PRENOTAZIONI, index=False)
            backup_istantaneo_telegram("Modifiche salvate da Elenco Dettagliato")
            st.success("✅ Modifiche ed eliminazioni salvate con successo nel database e inviate al Backup!")
            st.rerun()
