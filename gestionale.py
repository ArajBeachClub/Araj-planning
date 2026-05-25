#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 24 14:09:54 2026

@author: hibalaawissi
"""

import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta

FILE_PRENOTAZIONI = 'prenotazioni.csv'
FILE_CLIENTI = 'clienti.csv'

# ==========================================
# ⚙️ CONFIGURAZIONE TARIFFE, STAGIONI E FILE
# ==========================================

CAPIENZA_FILE = {
    "Prima Fila": 14,
    "Seconda Fila": 14,
    "Terza Fila": 9,
    "Quarta Fila": 8,
    "Quinta Fila": 8,
    "Sesta Fila (Altre)": 8,
    "Spiaggia Libera / Esterna": 20
}

STAGIONI_DATE = {
    "Alta A": [(date(2026, 6, 20), date(2026, 7, 3))],
    "Alta B": [(date(2026, 7, 4), date(2026, 7, 17)), (date(2026, 9, 1), date(2026, 9, 27))],
    "Altissima": [(date(2026, 7, 18), date(2026, 7, 31)), (date(2026, 8, 24), date(2026, 8, 31))],
    "Peak Season": [(date(2026, 8, 1), date(2026, 8, 23))]
}

GIORNI_FESTIVI = [date(2026, 6, 2), date(2026, 8, 15)]

TARIFFE = {
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

def trova_stagione(data_sel):
    for stagione, intervalli in STAGIONI_DATE.items():
        for inizio, fine in intervalli:
            if inizio <= data_sel <= fine:
                return stagione
    return "Alta A"

def calcola_prezzo_automatico(data_sel, fila, persone, durata, extra_scelti):
    stagione = trova_stagione(data_sel)
    giorno_sett = data_sel.weekday()
    
    is_weekend = (giorno_sett >= 5) 
    is_festivo = (data_sel in GIORNI_FESTIVI)
    tipo_tariffa = "Festivo" if (is_weekend or is_festivo) else "Feriale"
    
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

# ==========================================

def carica_clienti():
    if os.path.exists(FILE_CLIENTI):
        return pd.read_csv(FILE_CLIENTI, dtype={'Telefono': str})
    return pd.DataFrame(columns=["Telefono", "Nome"])

def carica_prenotazioni():
    if os.path.exists(FILE_PRENOTAZIONI):
        df = pd.read_csv(FILE_PRENOTAZIONI, dtype={'Telefono': str})
        
        if "Hotel" not in df.columns: df["Hotel"] = ""
        if "Persone" not in df.columns: df["Persone"] = 2
        if "Durata" not in df.columns: df["Durata"] = "Giornata Intera"
        if "Extra" not in df.columns: df["Extra"] = ""
        if "Nome" not in df.columns: df["Nome"] = "" 
        
        df["Hotel"] = df["Hotel"].fillna("")
        df["Persone"] = df["Persone"].fillna(2)
        df["Durata"] = df["Durata"].fillna("Giornata Intera")
        df["Extra"] = df["Extra"].fillna("")
        df["Nome"] = df["Nome"].fillna("")
        return df
    return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Hotel", "Persone", "Durata", "Extra"])

st.set_page_config(page_title="Beach Pass Pro", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

# --- 🔍 MOTORE DI RICERCA ---
with st.expander("🔍 Cerca Cliente / Verifica Prenotazione", expanded=False):
    ricerca = st.text_input("Inserisci una parte del Nome, del Telefono o dell'Hotel:", placeholder="Es. Mario, 340123..., Miramare").strip()
    if ricerca:
        if not df_pren.empty:
            mask_nome = df_pren['Nome'].astype(str).str.contains(ricerca, case=False, na=False)
            mask_tel = df_pren['Telefono'].astype(str).str.contains(ricerca, case=False, na=False)
            mask_hotel = df_pren['Hotel'].astype(str).str.contains(ricerca, case=False, na=False)
            
            risultati = df_pren[mask_nome | mask_tel | mask_hotel].sort_values(by="Data")
            
            if not risultati.empty:
                st.success(f"Trovate {len(risultati)} prenotazioni per '{ricerca}':")
                colonne_mostrate = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Hotel", "Stato", "Prezzo_Giorno"]
                st.dataframe(risultati[colonne_mostrate], use_container_width=True)
            else:
                st.warning(f"Nessuna prenotazione trovata per '{ricerca}'.")
        else:
            st.info("Nessuna prenotazione presente nel sistema al momento.")

st.divider()

# --- BARRA LATERALE: INSERIMENTO E MODIFICA ---
st.sidebar.header("📝 Gestione Prenotazioni")

# 1. VERIFICA DISPONIBILITÀ (Spostato fuori dal form per renderlo in tempo reale)
st.sidebar.subheader("1. Scegli Date e Fila")
date_selezionate = st.sidebar.date_input("Intervallo Date (Arrivo e Partenza)", [], format="DD/MM/YYYY")
input_fila = st.sidebar.selectbox("Fila", list(CAPIENZA_FILE.keys()))
max_ombrelloni_riga = CAPIENZA_FILE[input_fila]

# Logica di calcolo degli ombrelloni liberi
ombrelloni_liberi = []
if len(date_selezionate) > 0:
    data_inizio = date_selezionate[0]
    data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
    giorni_totali = (data_fine - data_inizio).days + 1
    
    # Genera l'elenco di tutti i giorni selezionati
    date_range = [(data_inizio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali)]
    
    # Controlla quali ombrelloni sono occupati in QUELLA fila per ALMENO UN GIORNO in quel range
    df_occupati = df_pren[(df_pren['Data'].isin(date_range)) & (df_pren['Fila'] == input_fila)]
    ombrelloni_occupati = df_occupati['Ombrellone'].unique()
    
    # Crea la lista dei liberi
    ombrelloni_liberi = [i for i in range(1, max_ombrelloni_riga + 1) if i not in ombrelloni_occupati]
    
    if ombrelloni_liberi:
        st.sidebar.success(f"✅ Liberi in queste date:\n {', '.join(map(str, ombrelloni_liberi))}")
    else:
        st.sidebar.error("❌ Tutto esaurito in questa fila per le date scelte!")

# 2. MODULO DI INSERIMENTO DATI
st.sidebar.subheader("2. Completa Prenotazione")
with st.sidebar.form("form_prenotazione"):
    col_q, col_omb = st.columns(2)
    with col_q:
        quantita_postazioni = st.number_input("Quante postazioni vicine?", min_value=1, max_value=3, value=1)
    
    max_start = max_ombrelloni_riga - quantita_postazioni + 1
    with col_omb:
        # L'operatore guarda il riquadro verde sopra e scrive qui il numero
        input_ombrellone = st.number_input(f"N° Ombrellone Iniziale", min_value=1, max_value=max_start, value=1, step=1)
        
    st.markdown("---")
    
    input_telefono = st.text_input("Telefono Cliente (Opzionale)").strip()
    
    nome_automatico = ""
    if input_telefono and not df_clienti.empty:
        cliente_esistente = df_clienti[df_clienti['Telefono'] == input_telefono]
        if not cliente_esistente.empty:
            nome_automatico = cliente_esistente.iloc[0]['Nome']
            st.sidebar.info(f"👤 Trovato in anagrafica: {nome_automatico}")
            
    input_nome = st.text_input("Nome Cliente (Obbligatorio)", value=nome_automatico).strip()
    input_hotel = st.text_input("Nome Hotel (Opzionale)")
    
    st.markdown("---")
    col_p, col_d = st.columns(2)
    with col_p:
        input_persone = st.number_input("Persone (PER OMBRELLONE)", min_value=1, max_value=4, value=2)
    with col_d:
        input_durata = st.selectbox("Durata", ["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"])
    
    if input_persone == 4:
        st.warning("⚠️ 4 Persone ad ombrellone: Scatta il supplemento!")
        
    input_extra = st.multiselect("🏖️ Risorse Aggiuntive Libere (per postazione)", list(PREZZI_EXTRA.keys()))
    
    st.markdown("---")
    input_stato = st.selectbox(
        "Stato Postazione", 
        ["In Attesa (Giallo)", "Confermato (Rosso)", "Pagato (Blu)", "Libero/No-Show (Verde)"]
    )
    
    prezzo_consigliato_totale = 0.0
    if len(date_selezionate) > 0:
        prezzo_unitario = calcola_prezzo_automatico(date_selezionate[0], input_fila, input_persone, input_durata, input_extra)
        prezzo_consigliato_totale = prezzo_unitario * quantita_postazioni
        
    input_prezzo = st.number_input("Prezzo Giornaliero TOTALE (€)", min_value=0.0, value=float(prezzo_consigliato_totale), step=1.0)
    
    submit = st.form_submit_button("Applica Modifiche")

# --- LOGICA DI SALVATAGGIO ---
if submit:
    if len(date_selezionate) > 0 and input_nome:
        data_inizio = date_selezionate[0]
        data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
        
        if input_telefono:
            if input_telefono in df_clienti['Telefono'].values:
                df_clienti.loc[df_clienti['Telefono'] == input_telefono, 'Nome'] = input_nome
            else:
                nuovo_c = pd.DataFrame([{"Telefono": input_telefono, "Nome": input_nome}])
                df_clienti = pd.concat([df_clienti, nuovo_c], ignore_index=True)
            df_clienti.to_csv(FILE_CLIENTI, index=False)
            
        giorni_totali = (data_fine - data_inizio).days + 1
        for i in range(giorni_totali):
            giorno_corrente_obj = data_inizio + timedelta(days=i)
            giorno_corrente_str = giorno_corrente_obj.strftime("%Y-%m-%d")
            
            prezzo_giorno_unitario = calcola_prezzo_automatico(giorno_corrente_obj, input_fila, input_persone, input_durata, input_extra)
            
            if input_prezzo != prezzo_consigliato_totale:
                prezzo_finale_unitario = input_prezzo / quantita_postazioni
            else:
                prezzo_finale_unitario = prezzo_giorno_unitario
            
            for j in range(quantita_postazioni):
                omb_corrente = input_ombrellone + j
                
                df_pren = df_pren[~((df_pren['Data'] == giorno_corrente_str) & (df_pren['Ombrellone'] == omb_corrente) & (df_pren['Fila'] == input_fila))]
                
                if "Libero" not in input_stato:
                    stato_pulito = input_stato.split(" ")[0]
                    if stato_pulito == "In":
                        stato_pulito = "Attesa"
                        
                    nuova_p = pd.DataFrame([{
                        "Data": giorno_corrente_str,
                        "Fila": input_fila,
                        "Ombrellone": omb_corrente,
                        "Nome": input_nome,
                        "Telefono": input_telefono,
                        "Stato": stato_pulito,
                        "Prezzo_Giorno": prezzo_finale_unitario,
                        "Hotel": str(input_hotel).strip(),
                        "Persone": input_persone,
                        "Durata": input_durata,
                        "Extra": ", ".join(input_extra)
                    }])
                    df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
                
        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
        st.sidebar.success(f"✅ Salvataggio completato!")
        st.rerun()
    else:
        st.sidebar.error("⚠️ Inserisci Data e NOME del Cliente.")

# --- MAPPA VISIVA ---
data_visiva = st.date_input("Seleziona data del planning:", date.today(), format="DD/MM/YYYY")
data_visiva_str = data_visiva.strftime("%Y-%m-%d")

df_oggi = df_pren[df_pren['Data'] == data_visiva_str]

data_formattata_ita = f"{data_visiva.day} {MESI_ITA[data_visiva.month]} {data_visiva.year}"
st.header(f"📅 Planning del {data_formattata_ita}")
st.divider()

def controlla_posto(numero_ombrellone, fila):
    if df_oggi.empty:
        return "#28a745", "Libero", "", ""
    record = df_oggi[(df_oggi['Ombrellone'] == numero_ombrellone) & (df_oggi['Fila'] == fila)]
    if record.empty:
        return "#28a745", "Libero", "", ""
        
    stato = record.iloc[0]['Stato']
    prezzo_g = record.iloc[0]['Prezzo_Giorno']
    pers = record.iloc[0].get('Persone', 2)
    durata = record.iloc[0].get('Durata', "")
    extra = record.iloc[0].get('Extra', "")
    
    nome_c = record.iloc[0].get('Nome', "")
    telefono_c = record.iloc[0].get('Telefono', "")
    if not nome_c and telefono_c and not df_clienti.empty:
        cerca_cliente = df_clienti[df_clienti['Telefono'] == telefono_c]
        if not cerca_cliente.empty:
            nome_c = cerca_cliente.iloc[0]['Nome']
    
    badge_durata = "🌗" if "Mezza" in str(durata) else ""
    badge_extra = "➕" if extra else ""
    
    hotel_c = record.iloc[0].get('Hotel', "")
    hotel_c = "" if pd.isna(hotel_c) else hotel_c
    hotel_html = f"<span style='font-size: 11px; color: #ffe8a1; display: block;'>🏨 {hotel_c}</span>" if hotel_c else ""
    
    dettagli = f"€{prezzo_g:.0f} | 👤 {pers} {badge_durata}{badge_extra}"
    
    if stato == "Attesa":
        return "#ffc107", f"{nome_c}", dettagli, hotel_html
    elif stato == "Confermato":
        return "#dc3545", f"{nome_c}", dettagli, hotel_html
    elif stato == "Pagato":
        return "#007bff", f"{nome_c}", dettagli, hotel_html
    return "#28a745", "Libero", "", ""

for nome_fila, max_posti in CAPIENZA_FILE.items():
    st.subheader(nome_fila)
    colonne_griglia = st.columns(max_posti) 
    for i in range(max_posti):
        numero_omb = i + 1
        colore_box, titolo, sottotitolo, hotel_str = controlla_posto(numero_omb, nome_fila)
        
        box_html = f"""
        <div style="background-color: {colore_box}; padding: 8px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px; border: 1px solid rgba(0,0,0,0.1);">
            <span style="font-size: 14px; font-weight: bold;">{numero_omb}</span><br>
            <hr style="margin: 3px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);">
            <span style="font-size: 11px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{titolo}</span>
            <span style="font-size: 10px; font-weight: normal; display: block;">{sottotitolo}</span>
            {hotel_str}
        </div>
        """
        colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)

st.divider()

st.subheader("📋 Elenco Dettagliato")
if not df_oggi.empty:
    colonne_tabella = ["Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Persone", "Durata", "Extra"]
    if 'Hotel' in df_oggi.columns:
        colonne_tabella.insert(4, "Hotel")
    st.dataframe(df_oggi[colonne_tabella], use_container_width=True)
else:
    st.info("Nessuna prenotazione registrata per la data di oggi.")