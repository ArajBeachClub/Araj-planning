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
# 🤖 CONFIGURAZIONE BOT TELEGRAM E BACKUP
# ==========================================
TELEGRAM_TOKEN = "8804050943:AAHvXVmSnEUPlvV6mj33JGGQHfhosnqcC2U"
TELEGRAM_CHAT_ID = "8663794616"  

def controllo_backup_automatico():
    try:
        ora_italia = datetime.utcnow() + timedelta(hours=2)
        oggi_str = ora_italia.strftime('%d-%m-%Y')
        
        if ora_italia.hour >= 20:
            ha_gia_fatto = False
            if os.path.exists("ultimo_backup.txt"):
                with open("ultimo_backup.txt", "r") as f:
                    if f.read().strip() == oggi_str:
                        ha_gia_fatto = True
            
            if not ha_gia_fatto and os.path.exists(FILE_PRENOTAZIONI):
                if not os.path.exists("backups_automatici"):
                    os.makedirs("backups_automatici")
                
                file_destinazione = f"backups_automatici/Backup_Spiaggia_{oggi_str}.csv"
                
                try:
                    df_bkp = pd.read_csv(FILE_PRENOTAZIONI)
                    df_bkp['Data'] = pd.to_datetime(df_bkp['Data'], errors='coerce').dt.strftime('%d-%m-%Y')
                    df_bkp.to_csv(file_destinazione, index=False, sep=';')
                except Exception:
                    shutil.copy(FILE_PRENOTAZIONI, file_destinazione)
                
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
                boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
                
                body_top = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
                    f"{TELEGRAM_CHAT_ID}\r\n"
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="document"; filename="Backup_Spiaggia_{oggi_str}.csv"\r\n'
                    f"Content-Type: text/csv\r\n\r\n"
                ).encode('utf-8')
                
                with open(file_destinazione, 'rb') as f:
                    file_content = f.read()
                    
                body_bottom = f"\r\n--{boundary}--\r\n".encode('utf-8')
                
                payload = body_top + file_content + body_bottom
                
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
                urllib.request.urlopen(req, timeout=10)
                
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
    "Quarta Fila": 7,
    "Quinta Fila": 5,
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
    "Operatore": st.column_config.SelectboxColumn("Operatore", options=OPERATORI_SPIAGGIA),
    "Incassato_da": st.column_config.SelectboxColumn("Incassato da", options=OPZIONI_INCASSO)
}

def trova_stagione(data_sel):
    for stagione, intervalli in STAGIONI_DATE.items():
        for inizio, fine in intervalli:
            if inizio <= data_sel <= fine:
                return stagione
    return "Media"

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
        totale += PREZZI_EXTRA.get(ex, 0)
    return totale

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
            
            df["Hotel"] = df["Hotel"].fillna("")
            df["Persone"] = df["Persone"].fillna(2)
            df["Durata"] = df["Durata"].fillna("Giornata Intera")
            df["Extra"] = df["Extra"].fillna("")
            df["Nome"] = df["Nome"].fillna("")
            df["Note"] = df["Note"].fillna("")
            df["Operatore"] = df["Operatore"].fillna("")
            df["Incassato_da"] = df["Incassato_da"].fillna("Da saldare")
            df["Sconto"] = df["Sconto"].fillna(0.0)
            return df
        except Exception:
            pass
            
    return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Sconto", "Hotel", "Persone", "Durata", "Extra", "Note", "Operatore", "Incassato_da"])

# ==========================================
# ⚡ AZIONI RAPIDE DALLA MAPPA VISIVA
# ==========================================
def applica_azione_rapida(idx, widget_key):
    azione = st.session_state[widget_key]
    if azione != "⚡ Azione":
        df = carica_prenotazioni()
        if not df.empty and idx in df.index:
            if azione == "📍 Presente":
                df.loc[idx, 'Stato'] = "Presente"
            elif azione.startswith("💰 "):
                nome_breve = azione.replace("💰 ", "")
                if nome_breve in MAPPA_NOMI_RAPIDI:
                    df.loc[idx, 'Incassato_da'] = MAPPA_NOMI_RAPIDI[nome_breve]
                    df.loc[idx, 'Stato'] = "Pres_Pagato"
            df.to_csv(FILE_PRENOTAZIONI, index=False)
        st.session_state[widget_key] = "⚡ Azione"


st.set_page_config(page_title="Beach Pass Pro", layout="wide")

# ESEGUE IL CONTROLLO DEL BACKUP AUTOMATICO
controllo_backup_automatico()

st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

# --- 💼 SALDO CLIENTI ABITUALI (PAGAMENTO A FINE MESE/PERIODO) ---
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
        df_cliente = df_pren[mask_da_saldare]
        
        if not df_cliente.empty:
            totale_dovuto = df_cliente['Prezzo_Giorno'].sum()
            st.warning(f"💶 **Totale accumulato da saldare per {cliente_sel}: € {totale_dovuto:.2f}**")
            
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
                indici = df_cliente.index.tolist()
                
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
                st.success(f"Perfetto! Tutte le {len(indici)} postazioni di {cliente_sel} sono state saldate e aggiornate a 'Presente e Pagato'.")
                st.rerun()

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
                
                edited_df = st.data_editor(risultati_filtrati, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_ricerca")
                
                if st.button("💾 Salva Modifiche da Ricerca"):
                    df_pren_temp = df_pren.drop(risultati.index)
                    has_overlap = False
                    
                    for idx in edited_df.index:
                        inc = str(edited_df.loc[idx, 'Incassato_da'])
                        sto = str(edited_df.loc[idx, 'Stato'])
                        
                        if inc == "Ospite (Gratis)":
                            edited_df.loc[idx, 'Prezzo_Giorno'] = 0.0
                            
                        if inc not in ["", "nan", "Da saldare"]:
                            if sto == "Presente":
                                edited_df.loc[idx, 'Stato'] = "Pres_Pagato"
                            elif sto in ["Attesa", "Confermato"]:
                                edited_df.loc[idx, 'Stato'] = "Pagato"

                        # CONTROLLO ANTI-SOVRAPPOSIZIONE
                        stato_finale = edited_df.loc[idx, 'Stato']
                        d_str = pd.to_datetime(edited_df.loc[idx, 'Data']).strftime('%Y-%m-%d')
                        fila = edited_df.loc[idx, 'Fila']
                        omb = edited_df.loc[idx, 'Ombrellone']

                        if stato_finale != "Libero":
                            overlap = df_pren_temp[(df_pren_temp['Data'] == d_str) & 
                                                   (df_pren_temp['Fila'] == fila) & 
                                                   (df_pren_temp['Ombrellone'] == omb) &
                                                   (df_pren_temp['Stato'] != "Libero")]
                            if not overlap.empty:
                                nome_occ = overlap.iloc[0]['Nome']
                                st.error(f"🚨 ERRORE: Impossibile salvare! L'ombrellone {omb} in {fila} del {pd.to_datetime(d_str).strftime('%d/%m/%Y')} è già occupato da {nome_occ}.")
                                has_overlap = True
                                break

                    if not has_overlap:
                        df_pren = df_pren_temp
                        edited_df['Data'] = pd.to_datetime(edited_df['Data']).dt.strftime('%Y-%m-%d')
                        df_pren = pd.concat([df_pren, edited_df], ignore_index=True)
                        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                        st.success("✅ Modifiche salvate con successo nel database!")
                        st.rerun()
            else:
                st.warning(f"Nessuna prenotazione trovata per '{ricerca}'.")
        else:
            st.info("Nessuna prenotazione presente nel sistema al momento.")

st.divider()

# --- BARRA LATERALE ---
st.sidebar.header("📝 Gestione Prenotazioni")

input_operatore = st.sidebar.selectbox("👤 Chi sta registrando la prenotazione?", OPERATORI_SPIAGGIA)

st.sidebar.subheader("1. Scegli Date e Fila")
date_selezionate = st.sidebar.date_input("Intervallo Date (Arrivo e Partenza)", [], format="DD/MM/YYYY")
input_fila = st.sidebar.selectbox("Fila", list(CAPIENZA_FILE.keys()))
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
with st.sidebar.form("form_prenotazione"):
    col_q, col_omb = st.columns(2)
    with col_q:
        quantita_postazioni = st.selectbox("Quante postazioni vicine?", [1, 2, 3], index=0)
    
    max_start = max_ombrelloni_riga - quantita_postazioni + 1
    with col_omb:
        opzioni_ombrelloni = list(range(1, max(2, max_start + 1)))
        input_ombrellone = st.selectbox(f"N° Ombrellone Iniziale", opzioni_ombrelloni, index=0)
        
    st.markdown("---")
    
    input_nome = st.text_input("Nome Cliente (Obbligatorio)").strip()
    input_telefono = st.text_input("Telefono Cliente (Opzionale)").strip()
    input_hotel = st.text_input("Nome Hotel (Opzionale)").strip()
    
    st.markdown("---")
    col_p, col_d = st.columns(2)
    with col_p:
        input_persone = st.selectbox("Persone (PER OMBRELLONE)", [1, 2, 3, 4, 5, 6], index=1)
    with col_d:
        input_durata = st.selectbox("Durata", ["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"])
    
    input_extra = st.multiselect("🏖️ Risorse Aggiuntive Libere (per postazione)", list(PREZZI_EXTRA.keys()))
    input_note = st.text_input("📝 Note / Memo (es. Ospite, Omaggio, Cagnolino)").strip()
    
    st.markdown("---")
    input_stato = st.selectbox("Stato Postazione", list(STATI_MAP.keys()))
    input_incassato = st.selectbox("💰 Pagamento incassato da:", OPZIONI_INCASSO, help="Seleziona chi ha preso i soldi se il cliente ha già pagato")
    
    prezzo_consigliato_totale = 0.0
    if len(date_selezionate) > 0:
        prezzo_unitario = calcola_prezzo_automatico(date_selezionate[0], input_fila, input_persone, input_durata, input_extra)
        prezzo_consigliato_totale = prezzo_unitario * quantita_postazioni
        
    input_prezzo = st.number_input("Prezzo Giornaliero TOTALE (€)", min_value=0.0, value=float(prezzo_consigliato_totale), step=1.0)
    
    st.markdown("---")
    tipo_salvataggio = st.radio("Se la postazione risulta già occupata:", ["Blocca (Errore)", "Sostituisci (Cancella il vecchio)", "Subentro (Tieni il vecchio per l'incasso)"], help="Scegli Subentro per far pagare due clienti sullo stesso ombrellone nello stesso giorno")
    
    submit = st.form_submit_button("Applica Modifiche")

if submit:
    if len(date_selezionate) > 0 and input_nome:
        data_inizio = date_selezionate[0]
        data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
        giorni_totali = (data_fine - data_inizio).days + 1
        date_list_str = [(data_inizio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali)]
        ombrelloni_richiesti = [input_ombrellone + j for j in range(quantita_postazioni)]
        
        if not df_pren.empty:
            sovrapposizioni = df_pren[(df_pren['Data'].isin(date_list_str)) & (df_pren['Fila'] == input_fila) & (df_pren['Ombrellone'].isin(ombrelloni_richiesti))]
        else:
            sovrapposizioni = pd.DataFrame()
            
        stato_pulito = STATI_MAP[input_stato]
        
        if not sovrapposizioni.empty and tipo_salvataggio == "Blocca (Errore)" and stato_pulito != "Libero":
            st.sidebar.error("🚨 ERRORE: POSTAZIONE GIÀ OCCUPATA!")
            for _, row_conf in sovrapposizioni.drop_duplicates(subset=['Ombrellone', 'Nome']).iterrows():
                d = row_conf['Data']
                d_ita = f"{d[8:10]}/{d[5:7]}/{d[0:4]}" if len(d)==10 else d
                st.sidebar.warning(f"👉 Omb. {row_conf['Ombrellone']} prenotato da {row_conf['Nome']} ({d_ita})")
        else:
            if input_telefono:
                tel_norm = normalizza_tel(input_telefono)
                if not df_clienti.empty:
                    df_clienti['Tel_Norm'] = df_clienti['Telefono'].apply(normalizza_tel)
                    if tel_norm in df_clienti['Tel_Norm'].values:
                        idx = df_clienti[df_clienti['Tel_Norm'] == tel_norm].index
                        df_clienti.loc[idx, 'Nome'] = input_nome
                        df_clienti.loc[idx, 'Telefono'] = input_telefono
                    else:
                        nuovo_c = pd.DataFrame([{"Telefono": input_telefono, "Nome": input_nome}])
                        df_clienti = pd.concat([df_clienti, nuovo_c], ignore_index=True)
                    df_clienti = df_clienti.drop(columns=['Tel_Norm'], errors='ignore')
                else:
                    nuovo_c = pd.DataFrame([{"Telefono": input_telefono, "Nome": input_nome}])
                    df_clienti = pd.concat([df_clienti, nuovo_c], ignore_index=True)
                df_clienti.to_csv(FILE_CLIENTI, index=False)
                
            for i in range(giorni_totali):
                giorno_corrente_obj = data_inizio + timedelta(days=i)
                giorno_corrente_str = giorno_corrente_obj.strftime("%Y-%m-%d")
                prezzo_giorno_unitario = calcola_prezzo_automatico(giorno_corrente_obj, input_fila, input_persone, input_durata, input_extra)
                prezzo_finale_unitario = input_prezzo / quantita_postazioni if input_prezzo != prezzo_consigliato_totale else prezzo_giorno_unitario
                
                if input_incassato == "Ospite (Gratis)":
                    prezzo_finale_unitario = 0.0
                
                for j in range(quantita_postazioni):
                    omb_corrente = input_ombrellone + j
                    
                    if tipo_salvataggio == "Sostituisci (Cancella il vecchio)" and not df_pren.empty:
                        df_pren = df_pren[~((df_pren['Data'] == giorno_corrente_str) & (df_pren['Ombrellone'] == omb_corrente) & (df_pren['Fila'] == input_fila))]
                    
                    if stato_pulito != "Libero":
                        nuova_p = pd.DataFrame([{
                            "Data": giorno_corrente_str, "Fila": input_fila, "Ombrellone": omb_corrente,
                            "Nome": input_nome, "Telefono": input_telefono, "Stato": stato_pulito,
                            "Prezzo_Giorno": prezzo_finale_unitario, "Sconto": 0.0, "Hotel": str(input_hotel).strip(),
                            "Persone": input_persone, "Durata": input_durata, "Extra": ", ".join(input_extra), 
                            "Note": input_note, "Operatore": input_operatore, "Incassato_da": input_incassato
                        }])
                        if df_pren.empty:
                            df_pren = nuova_p
                        else:
                            df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
            df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
            st.sidebar.success("✅ Salvataggio completato!")
            st.rerun()
    else:
        st.sidebar.error("⚠️ Inserisci Data e NOME del Cliente.")

# --- 💾 SISTEMA SALVAVITA (BACKUP) ---
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Salvataggio Sicuro (Backup)")
st.sidebar.info("Scarica il database ogni sera per non perdere mai i dati in caso di riavvio del server!")

if not df_pren.empty:
    df_backup = df_pren.copy()
    df_backup['Data'] = pd.to_datetime(df_backup['Data'], errors='coerce').dt.strftime('%d-%m-%Y')
    csv_backup = df_backup.to_csv(index=False, sep=';').encode('utf-8')
    st.sidebar.download_button(
        label="⬇️ Scarica Database Prenotazioni",
        data=csv_backup,
        file_name=f"prenotazioni_{date.today().strftime('%d-%m-%Y')}.csv",
        mime="text/csv",
        type="primary"
    )

file_caricato = st.sidebar.file_uploader("⬆️ Ripristina un Backup precedente", type=["csv"])
if file_caricato is not None:
    if st.sidebar.button("⚠️ Conferma Ripristino Dati"):
        try:
            df_ripristino = pd.read_csv(file_caricato, sep=None, engine='python')
            df_ripristino['Data'] = pd.to_datetime(df_ripristino['Data'], format='%d-%m-%Y', errors='coerce').fillna(pd.to_datetime(df_ripristino['Data'], errors='coerce')).dt.strftime('%Y-%m-%d')
            df_ripristino.to_csv(FILE_PRENOTAZIONI, index=False)
            st.sidebar.success("✅ Ripristino completato! Ricarica la pagina.")
            st.rerun()
        except Exception:
            st.sidebar.error("❌ Formato file non valido.")

st.sidebar.markdown("---")

# --- AREA DEMO E NOTIFICHE ---
st.sidebar.subheader("💬 Invia Conferma (Gratis)")

operatore_msg = st.sidebar.selectbox("👤 Inviato da:", OPERATORI_SPIAGGIA)
tipo_cliente = st.sidebar.radio("Destinatario", ["Privato", "Hotel"], horizontal=True)

date_wa = st.sidebar.date_input("Date prenotazione (Arrivo e Partenza)", [], format="DD/MM/YYYY")
nome_wa = st.sidebar.text_input("Nome Cliente / Nome Hotel")
tel_wa = st.sidebar.text_input("Cellulare (Per WhatsApp)")
email_cliente = st.sidebar.text_input("Indirizzo Email")
lingua_scelta = st.sidebar.selectbox("Lingua Messaggio", ["Italiano", "English"])

if nome_wa and len(date_wa) > 0:
    data_inizio_ita = date_wa[0].strftime("%d/%m/%Y")
    if len(date_wa) > 1 and date_wa[0] != date_wa[1]:
        data_fine_ita = date_wa[1].strftime("%d/%m/%Y")
        stringa_date_ita = f"dal {data_inizio_ita} al {data_fine_ita}"
        stringa_date_eng = f"from {data_inizio_ita} to {data_fine_ita}"
    else:
        stringa_date_ita = f"per il giorno {data_inizio_ita}"
        stringa_date_eng = f"for {data_inizio_ita}"
        
    if tipo_cliente == "Privato":
        if lingua_scelta == "Italiano":
            testo_base = f"Gentile {nome_wa},\n\nLa sua prenotazione {stringa_date_ita} è stata registrata correttamente.\n\nLe ricordiamo di arrivare entro le ore 11:00. In caso di ritardo, la preghiamo di avvisare tempestivamente inviando un messaggio WhatsApp al numero +39 3391789319, indicando il nome di riferimento e le date della prenotazione.\n\nIn caso contrario, la prenotazione decadrà dal sistema e la postazione verrà liberata.\n\nGrazie e a presto!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto_email = "Conferma Prenotazione - Araj Beach Club"
        else:
            testo_base = f"Dear {nome_wa},\n\nYour reservation {stringa_date_eng} has been successfully recorded.\n\nWe remind you to arrive by 11:00 AM. In case of delay, please notify us by sending a WhatsApp message to +39 3391789319 indicating your reference name and the dates of your reservation.\n\nOtherwise, the reservation will be automatically cancelled and the spot released.\n\nThank you!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto_email = "Reservation Confirmation - Araj Beach Club"
    else:
        if lingua_scelta == "Italiano":
            testo_base = f"Gentile Staff di {nome_wa},\n\nConfermiamo con piacere la prenotazione {stringa_date_ita} per i vostri ospiti.\n\nVi preghiamo di comunicare eventuali ritardi tramite WhatsApp al numero +39 3391789319 per evitare la cancellazione automatica della postazione alle ore 11:00.\n\nGrazie per la preziosa collaborazione!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto_email = f"Conferma Prenotazione {stringa_date_ita} - Araj Beach Club"
        else:
            testo_base = f"Dear Staff at {nome_wa},\n\nWe are pleased to confirm the reservation {stringa_date_eng} for your guests.\n\nPlease notify us of any delays via WhatsApp at +39 3391789319 to avoid automatic cancellation of the spot at 11:00 AM.\n\nThank you for your cooperation!\n\n{operatore_msg}\nAraj Beach Club"
            oggetto_email = f"Reservation Confirmation {stringa_date_eng} - Araj Beach Club"

    testo_url = urllib.parse.quote(testo_base)
    oggetto_url = urllib.parse.quote(oggetto_email)
    destinatario_email = email_cliente if email_cliente else ""

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if tel_wa:
            tel_pulito = tel_wa.replace(" ", "").replace("+", "")
            if not tel_pulito.startswith("39") and len(tel_pulito) < 11:
                tel_pulito = "39" + tel_pulito
            url_whatsapp = f"https://wa.me/{tel_pulito}?text={testo_url}"
            st.link_button("💬 WhatsApp", url_whatsapp, use_container_width=True)
        else:
            st.caption("Manca il numero")
    with col2:
        url_email = f"mailto:{destinatario_email}?subject={oggetto_url}&body={testo_url}"
        st.link_button("📧 Email", url_email, use_container_width=True)
elif nome_wa and len(date_wa) == 0:
    st.sidebar.warning("⚠️ Seleziona le date per generare il messaggio.")

# --- MAPPA VISIVA E TABELLA INFERIORE INTERATTIVA ---
data_visiva = st.date_input("📅 Mappa Visiva: Seleziona SINGOLA DATA (per i clienti) o UN PERIODO (per cercare disponibilità fisse):", [], format="DD/MM/YYYY")

if len(data_visiva) == 0:
    st.info("👈 Seleziona una data per visualizzare la mappa della spiaggia.")
else:
    data_inizio_vis = data_visiva[0]
    data_fine_vis = data_visiva[1] if len(data_visiva) > 1 else data_inizio_vis
    giorni_totali_vis = (data_fine_vis - data_inizio_vis).days + 1
    date_range_vis = [(data_inizio_vis + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali_vis)]

    if not df_pren.empty:
        df_range = df_pren[df_pren['Data'].isin(date_range_vis)]
    else:
        df_range = pd.DataFrame()

    if giorni_totali_vis == 1:
        # VISTA SINGOLA DATA
        data_formattata_ita = f"{data_inizio_vis.day} {MESI_ITA[data_inizio_vis.month]} {data_inizio_vis.year}"
        st.header(f"📅 Planning del {data_formattata_ita}")
        
        st.markdown("""
        <div style="text-align: right; margin-bottom: 10px;">
            <button onclick="window.parent.print(); window.print();" style="background-color: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                🖨️ Stampa Planning (Quadratini)
            </button>
            <p style="font-size: 12px; color: gray; margin-top: 5px;">Se il tasto non funziona su iPhone, usa il tasto 'Condividi' del telefono ⬆️ e seleziona 'Stampa'.</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        def controlla_posto(numero_ombrellone, fila):
            if df_range.empty: return "#28a745", "Libero", "", "", "", None
            record = df_range[(df_range['Ombrellone'] == numero_ombrellone) & (df_range['Fila'] == fila)]
            if record.empty: return "#28a745", "Libero", "", "", "", None
            
            ultimo_record = record.iloc[-1]
            
            stato = ultimo_record['Stato']
            prezzo_g = ultimo_record['Prezzo_Giorno']
            pers = ultimo_record.get('Persone', 2)
            durata = ultimo_record.get('Durata', "")
            extra = ultimo_record.get('Extra', "")
            nome_c = ultimo_record.get('Nome', "")
            sconto_applicato = float(ultimo_record.get('Sconto', 0.0))
            
            operatore_val = str(ultimo_record.get('Operatore', ""))
            nome_op = operatore_val.split()[0] if operatore_val and operatore_val != "nan" else ""
            badge_operatore = f" ✍️ {nome_op}" if nome_op else ""
            
            incassato_val = str(ultimo_record.get('Incassato_da', ""))
            nome_incass = incassato_val.split()[0] if incassato_val and incassato_val not in ["nan", "Da", "Da saldare"] else ""
            badge_incassato = f" 💰 {nome_incass} |" if nome_incass else ""
            
            badge_sconto = " 📉" if sconto_applicato > 0 else ""
            badge_durata = "🌗" if "Mezza" in str(durata) else ""
            badge_extra = "➕" if extra else ""
            hotel_c = ultimo_record.get('Hotel', "")
            hotel_html = f"<span style='font-size: 11px; color: #ffe8a1; display: block;'>🏨 {hotel_c}</span>" if hotel_c and not pd.isna(hotel_c) else ""
            
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
            
            return colore_box, f"{nome_c}", dettagli, hotel_html, badge_rivendibile, ultimo_record.name

        for nome_fila, max_posti in CAPIENZA_FILE.items():
            st.subheader(nome_fila)
            colonne_griglia = st.columns(max_posti) 
            for i in range(max_posti):
                numero_omb = i + 1
                colore_box, titolo, sottotitolo, hotel_str, badge_rivend, row_idx = controlla_posto(numero_omb, nome_fila)
                
                # LOGICA ETICHETTE PERSONALIZZATE
                etichetta = ""
                if nome_fila == "Prima Fila":
                    if numero_omb in [15, 16]:
                        etichetta = "Fisicamente in 2ª Fila"
                    elif numero_omb == 17:
                        etichetta = "Fisicamente in 3ª Fila"
                    else:
                        etichetta = "1ª Fila"
                elif nome_fila == "Seconda Fila":
                    if numero_omb in [15, 16]:
                        etichetta = "Fisicamente in 3ª Fila"
                    else:
                        etichetta = "2ª Fila"
                elif nome_fila == "Terza Fila":
                    etichetta = "3ª Fila"
                else:
                    etichetta = nome_fila
                
                box_html = f"<div style='background-color: {colore_box}; padding: 6px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px; border: 1px solid rgba(0,0,0,0.1);'><span style='font-size: 10px; font-weight: normal; color: rgba(255,255,255,0.8); display: block;'>{etichetta}</span><span style='font-size: 16px; font-weight: bold;'>{numero_omb}</span><br><hr style='margin: 3px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);'>{badge_rivend}<span style='font-size: 11px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{titolo}</span><span style='font-size: 10px; font-weight: normal; display: block;'>{sottotitolo}</span>{hotel_str}</div>"
                
                colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)
                
                if row_idx is not None:
                    widget_key = f"azione_rapida_{row_idx}_{nome_fila}_{numero_omb}_{data_inizio_vis}"
                    if widget_key not in st.session_state:
                        st.session_state[widget_key] = "⚡ Azione"
                    
                    opzioni_rapide = ["⚡ Azione", "📍 Presente"] + [f"💰 {nome}" for nome in MAPPA_NOMI_RAPIDI.keys()]
                    
                    colonne_griglia[i].selectbox(
                        "Azione Rapida",
                        options=opzioni_rapide,
                        label_visibility="collapsed",
                        key=widget_key,
                        on_change=applica_azione_rapida,
                        args=(row_idx, widget_key)
                    )

    else:
        # VISTA PERIODO CONTINUO (RADAR DISPONIBILITÀ)
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
            st.info("💡 Fai doppio clic sulle celle per cambiare lo Stato, aggiornare l'Operatore, chi ha Incassato o le Note, poi clicca su Salva!")
        
        colonne_tabella = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Operatore", "Incassato_da", "Prezzo_Giorno", "Sconto", "Persone", "Durata", "Extra", "Note"]
        if 'Hotel' in df_range.columns: 
            colonne_tabella.insert(4, "Hotel")
        
        df_range_edit = df_range[colonne_tabella].copy()
        df_range_edit['Data'] = pd.to_datetime(df_range_edit['Data'], errors='coerce').dt.date
        
        # ORDINAMENTO LOGICO PER FILA E OMBRELLONE
        df_range_edit['Fila'] = pd.Categorical(df_range_edit['Fila'], categories=list(CAPIENZA_FILE.keys()), ordered=True)
        df_range_edit = df_range_edit.sort_values(by=['Data', 'Fila', 'Ombrellone'])
        df_range_edit['Fila'] = df_range_edit['Fila'].astype(str)
        
        edited_range = st.data_editor(df_range_edit, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_oggi")
        
        if st.button("💾 Salva Modifiche Tabella", type="primary"):
            df_pren_temp = df_pren.drop(df_range.index)
            has_overlap = False
            
            for idx in edited_range.index:
                inc = str(edited_range.loc[idx, 'Incassato_da'])
                sto = str(edited_range.loc[idx, 'Stato'])
                
                if inc == "Ospite (Gratis)":
                    edited_range.loc[idx, 'Prezzo_Giorno'] = 0.0
                    
                if inc not in ["", "nan", "Da saldare"]:
                    if sto == "Presente":
                        edited_range.loc[idx, 'Stato'] = "Pres_Pagato"
                    elif sto in ["Attesa", "Confermato"]:
                        edited_range.loc[idx, 'Stato'] = "Pagato"

                # CONTROLLO ANTI-SOVRAPPOSIZIONE
                stato_finale = edited_range.loc[idx, 'Stato']
                d_str = pd.to_datetime(edited_range.loc[idx, 'Data']).strftime('%Y-%m-%d')
                fila = edited_range.loc[idx, 'Fila']
                omb = edited_range.loc[idx, 'Ombrellone']

                if stato_finale != "Libero":
                    overlap = df_pren_temp[(df_pren_temp['Data'] == d_str) & 
                                           (df_pren_temp['Fila'] == fila) & 
                                           (df_pren_temp['Ombrellone'] == omb) &
                                           (df_pren_temp['Stato'] != "Libero")]
                    if not overlap.empty:
                        nome_occ = overlap.iloc[0]['Nome']
                        st.error(f"🚨 ERRORE: Impossibile salvare! L'ombrellone {omb} in {fila} del {pd.to_datetime(d_str).strftime('%d/%m/%Y')} è già occupato da {nome_occ}.")
                        has_overlap = True
                        break

            if not has_overlap:
                df_pren = df_pren_temp
                edited_range['Data'] = pd.to_datetime(edited_range['Data']).dt.strftime('%Y-%m-%d')
                df_pren = pd.concat([df_pren, edited_range], ignore_index=True)
                df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
                st.success("✅ Dati aggiornati (lo Stato si è aggiornato in automatico se necessario)!")
                st.rerun()
    else:
        st.info("Nessuna prenotazione registrata in questo periodo.")

    # --- 📊 REPORT DI FINE GIORNATA ---
    st.divider()
    st.header("📊 Report di Fine Giornata")
    st.info("Questo è il resoconto completo. I clienti in 'Subentro' si sommano automaticamente per calcolare l'incasso reale. Puoi stampare questa pagina premendo Ctrl+P (o Cmd+P su Mac).")

    if not df_range.empty:
        incasso_totale = df_range['Prezzo_Giorno'].sum()
        totale_persone = df_range['Persone'].sum()
        totale_sconti = df_range['Sconto'].sum()
        
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("💶 Incasso Netto Giornaliero", f"€ {incasso_totale:.2f}")
        col_r2.metric("📉 Sconti Applicati Oggi", f"€ {totale_sconti:.2f}")
        col_r3.metric("👥 Totale Persone Registrate", f"{totale_persone}")
        
        colonne_report = ["Data", "Fila", "Ombrellone", "Nome", "Stato", "Prezzo_Giorno", "Sconto", "Incassato_da", "Operatore", "Note"]
        df_export = df_range[colonne_report].copy()
        
        # ORDINAMENTO LOGICO PER FILA E OMBRELLONE
        df_export['Fila'] = pd.Categorical(df_export['Fila'], categories=list(CAPIENZA_FILE.keys()), ordered=True)
        df_export = df_export.sort_values(by=["Data", "Fila", "Ombrellone"])
        df_export['Fila'] = df_export['Fila'].astype(str)
        
        df_export['Data'] = pd.to_datetime(df_export['Data']).dt.strftime('%d/%m/%Y')
        st.dataframe(df_export, use_container_width=True)
        
        csv_report = df_export.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="⬇️ Scarica Report in Excel/CSV",
            data=csv_report,
            file_name=f"Report_Spiaggia_{data_inizio_vis.strftime('%d-%m-%Y')}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.warning("Nessuna prenotazione da calcolare per questo report.")
