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
    "Sesta Fila (Altre)": 8
}

# Date stagioni (Anno, Mese, Giorno)
STAGIONI_DATE = {
    "Alta A": [(date(2026, 6, 20), date(2026, 7, 3))],
    "Alta B": [(date(2026, 7, 4), date(2026, 7, 17)), (date(2026, 9, 1), date(2026, 9, 27))],
    "Altissima": [(date(2026, 7, 18), date(2026, 7, 31)), (date(2026, 8, 24), date(2026, 8, 31))],
    "Peak Season": [(date(2026, 8, 1), date(2026, 8, 23))]
}

GIORNI_FESTIVI = [date(2026, 6, 2), date(2026, 8, 15)]

# Formato: "Fila": {"Feriale": [Prezzo, Suppl. 4° pax], "Festivo": [Prezzo, Suppl. 4° pax]}
# Nota: La 2/3 e 4/5 sono accorpate nei listini, ma qui le separiamo per facilità di codice
TARIFFE = {
    "Alta A": {
        "Prima Fila": {"Feriale": [38, 8], "Festivo": [40, 10]},
        "Seconda Fila": {"Feriale": [36, 7], "Festivo": [38, 8]},
        "Terza Fila": {"Feriale": [36, 7], "Festivo": [38, 8]},
        "Quarta Fila": {"Feriale": [34, 6], "Festivo": [36, 7]},
        "Quinta Fila": {"Feriale": [34, 6], "Festivo": [36, 7]},
        "Sesta Fila (Altre)": {"Feriale": [32, 5], "Festivo": [34, 6]}
    },
    "Alta B": {
        "Prima Fila": {"Feriale": [40, 8], "Festivo": [42, 10]},
        "Seconda Fila": {"Feriale": [38, 7], "Festivo": [40, 8]},
        "Terza Fila": {"Feriale": [38, 7], "Festivo": [40, 8]},
        "Quarta Fila": {"Feriale": [36, 6], "Festivo": [38, 7]},
        "Quinta Fila": {"Feriale": [36, 6], "Festivo": [38, 7]},
        "Sesta Fila (Altre)": {"Feriale": [34, 5], "Festivo": [36, 6]}
    },
    "Altissima": {
        "Prima Fila": {"Feriale": [56, 10], "Festivo": [58, 12]},
        "Seconda Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Terza Fila": {"Feriale": [53, 8], "Festivo": [55, 10]},
        "Quarta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Quinta Fila": {"Feriale": [49, 7], "Festivo": [52, 8]},
        "Sesta Fila (Altre)": {"Feriale": [42, 6], "Festivo": [44, 7]}
    },
    "Peak Season": { # Peak non ha differenze fer/fes nei pdf, usiamo lo stesso per entrambi
        "Prima Fila": {"Feriale": [74, 14], "Festivo": [74, 14]},
        "Seconda Fila": {"Feriale": [65, 10], "Festivo": [65, 10]},
        "Terza Fila": {"Feriale": [65, 10], "Festivo": [65, 10]},
        "Quarta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]},
        "Quinta Fila": {"Feriale": [60, 9], "Festivo": [60, 9]},
        "Sesta Fila (Altre)": {"Feriale": [49, 8], "Festivo": [49, 8]}
    }
}

# Prezzi generici per risorse (puoi modificarli in base alla stagione reale)
PREZZI_EXTRA = {
    "Lettino Singolo": 12,
    "Ombrellone Singolo Libera": 25,
    "Postazione Esterna": 45,
    "Telo Mare Extra": 5
}

def trova_stagione(data_sel):
    for stagione, intervalli in STAGIONI_DATE.items():
        for inizio, fine in intervalli:
            if inizio <= data_sel <= fine:
                return stagione
    return "Alta A" # Default se fuori dalle date

def calcola_prezzo_automatico(data_sel, fila, persone, durata, extra_scelti):
    stagione = trova_stagione(data_sel)
    giorno_sett = data_sel.weekday()
    
    is_weekend = (giorno_sett >= 5) 
    is_festivo = (data_sel in GIORNI_FESTIVI)
    tipo_tariffa = "Festivo" if (is_weekend or is_festivo) else "Feriale"
    
    # 1. Prezzo Base (Postazione)
    prezzo_base = TARIFFE[stagione][fila][tipo_tariffa][0]
    suppl_persona = TARIFFE[stagione][fila][tipo_tariffa][1]
    
    # Modificatori durata
    if durata == "Mezza Giornata (fino 13 / da 15.30)":
        prezzo_base = prezzo_base * 0.70 # Circa il 30% in meno per la mezza giornata
    elif durata == "Solo 1 Persona (Postazione Ridotta)":
        prezzo_base = prezzo_base * 0.75 # Sconto per la postazione da 1 persona
        
    totale = prezzo_base
    
    # 2. Supplemento 4a persona
    if persone > 3:
        totale += suppl_persona
        
    # 3. Somma Risorse Extra
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
        colonne_necessarie = ["Hotel", "Persone", "Durata", "Extra"]
        for col in colonne_necessarie:
            if col not in df.columns:
                df[col] = ""
        df.fillna("", inplace=True)
        return df
    return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Telefono", "Stato", "Prezzo_Giorno", "Hotel", "Persone", "Durata", "Extra"])

st.set_page_config(page_title="Beach Pass Pro", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

# --- BARRA LATERALE: INSERIMENTO E MODIFICA ---
st.sidebar.header("📝 Gestione Prenotazioni")

with st.sidebar.form("form_prenotazione"):
    date_selezionate = st.date_input("Intervallo Date (Arrivo e Partenza)", [])
    
    # Selezione Dinamica della Fila e Capienza
    input_fila = st.selectbox("Fila", list(CAPIENZA_FILE.keys()))
    max_ombrelloni_riga = CAPIENZA_FILE[input_fila]
    
    input_ombrellone = st.number_input(f"N° Ombrellone (Max {max_ombrelloni_riga})", min_value=1, max_value=max_ombrelloni_riga, step=1)
        
    st.markdown("---")
    input_telefono = st.text_input("Telefono Cliente (Anagrafica Unica)").strip()
    
    nome_automatico = ""
    if input_telefono and not df_clienti.empty:
        cliente_esistente = df_clienti[df_clienti['Telefono'] == input_telefono]
        if not cliente_esistente.empty:
            nome_automatico = cliente_esistente.iloc[0]['Nome']
            st.sidebar.info(f"👤 Trovato: {nome_automatico}")
            
    input_nome = st.text_input("Nome Cliente", value=nome_automatico)
    input_hotel = st.text_input("Nome Hotel (Opzionale)")
    
    st.markdown("---")
    # Nuovo blocco Persone e Durata
    col_p, col_d = st.columns(2)
    with col_p:
        input_persone = st.number_input("Persone (Max 4)", min_value=1, max_value=4, value=2)
    with col_d:
        input_durata = st.selectbox("Durata", ["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"])
    
    if input_persone == 4:
        st.warning("⚠️ 4 Persone: Scatta il supplemento automatico!")
        
    # Risorse Aggiuntive
    input_extra = st.multiselect("🏖️ Risorse Aggiuntive Libere", list(PREZZI_EXTRA.keys()))
    
    st.markdown("---")
    input_stato = st.selectbox(
        "Stato Postazione", 
        ["In Attesa (Giallo)", "Confermato (Rosso)", "Pagato (Blu)", "Libero/No-Show (Verde)"]
    )
    
    prezzo_consigliato = 0.0
    if len(date_selezionate) > 0:
        prezzo_consigliato = calcola_prezzo_automatico(date_selezionate[0], input_fila, input_persone, input_durata, input_extra)
        
    input_prezzo = st.number_input("Prezzo Giornaliero (€)", min_value=0.0, value=float(prezzo_consigliato), step=1.0)
    
    submit = st.form_submit_button("Applica Modifiche")

# --- LOGICA DI SALVATAGGIO ---
if submit:
    if len(date_selezionate) > 0 and input_telefono:
        data_inizio = date_selezionate[0]
        data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
        
        if input_nome:
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
            
            prezzo_giorno_specifico = calcola_prezzo_automatico(giorno_corrente_obj, input_fila, input_persone, input_durata, input_extra)
            prezzo_finale = input_prezzo if input_prezzo != prezzo_consigliato else prezzo_giorno_specifico
            
            # Pulizia vecchie righe stesse coordinate
            df_pren = df_pren[~((df_pren['Data'] == giorno_corrente_str) & (df_pren['Ombrellone'] == input_ombrellone) & (df_pren['Fila'] == input_fila))]
            
            if "Libero" not in input_stato:
                stato_pulito = input_stato.split(" ")[0]
                if stato_pulito == "In":
                    stato_pulito = "Attesa"
                    
                nuova_p = pd.DataFrame([{
                    "Data": giorno_corrente_str,
                    "Fila": input_fila,
                    "Ombrellone": input_ombrellone,
                    "Telefono": input_telefono,
                    "Stato": stato_pulito,
                    "Prezzo_Giorno": prezzo_finale,
                    "Hotel": str(input_hotel).strip(),
                    "Persone": input_persone,
                    "Durata": input_durata,
                    "Extra": ", ".join(input_extra)
                }])
                df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
                
        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
        st.sidebar.success("✅ Salvato con successo!")
        st.rerun()
    else:
        st.sidebar.error("⚠️ Inserisci Data e Telefono.")

# --- MAPPA VISIVA ---
data_visiva = st.date_input("Seleziona data del planning:", date.today())
data_visiva_str = data_visiva.strftime("%Y-%m-%d")

df_oggi = df_pren[df_pren['Data'] == data_visiva_str]
if not df_oggi.empty and not df_clienti.empty:
    df_oggi = pd.merge(df_oggi, df_clienti, on="Telefono", how="left")

def controlla_posto(numero_ombrellone, fila):
    if df_oggi.empty:
        return "#28a745", "Libero", "", ""
    record = df_oggi[(df_oggi['Ombrellone'] == numero_ombrellone) & (df_oggi['Fila'] == fila)]
    if record.empty:
        return "#28a745", "Libero", "", ""
        
    stato = record.iloc[0]['Stato']
    nome_c = record.iloc[0]['Nome']
    prezzo_g = record.iloc[0]['Prezzo_Giorno']
    pers = record.iloc[0].get('Persone', 2)
    durata = record.iloc[0].get('Durata', "")
    extra = record.iloc[0].get('Extra', "")
    
    # Icone per mezza giornata o extra
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
    # Crea il numero esatto di colonne richieste (14, 9 o 8)
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
    st.info("Nessuna prenotazione registrata.")