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

# Nomi dei file d'archivio (verranno creati da soli nella stessa cartella dello script)
FILE_PRENOTAZIONI = 'prenotazioni.csv'
FILE_CLIENTI = 'clienti.csv'

# --- FUNZIONI DI CARICAMENTO DATI ---
def carica_clienti():
    if os.path.exists(FILE_CLIENTI):
        return pd.read_csv(FILE_CLIENTI, dtype={'Telefono': str})
    return pd.DataFrame(columns=["Telefono", "Nome"])

def carica_prenotazioni():
    if os.path.exists(FILE_PRENOTAZIONI):
        return pd.read_csv(FILE_PRENOTAZIONI, dtype={'Telefono': str})
    return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Telefono", "Stato", "Prezzo_Giorno"])

# Configurazione iniziale della pagina web
st.set_page_config(page_title="Beach Pass", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni")

df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

# --- BARRA LATERALE: INSERIMENTO E MODIFICA ---
st.sidebar.header("📝 Gestione Prenotazioni")

with st.sidebar.form("form_prenotazione"):
    # Selezione intervallo date (Arrivo e Partenza)
    date_selezionate = st.date_input("Intervallo Date (Seleziona Arrivo e Partenza)", [])
    
    col1, col2 = st.columns(2)
    with col1:
        input_fila = st.selectbox("Fila", ["Prima Fila", "Seconda Fila"])
    with col2:
        input_ombrellone = st.number_input("N° Ombrellone (1-7)", min_value=1, max_value=7, step=1)
        
    st.markdown("---")
    input_telefono = st.text_input("Telefono Cliente (Anagrafica Unica)").strip()
    
    # Riconoscimento automatico del cliente abituale per evitare doppioni
    nome_automatico = ""
    if input_telefono and not df_clienti.empty:
        cliente_esistente = df_clienti[df_clienti['Telefono'] == input_telefono]
        if not cliente_esistente.empty:
            nome_automatico = cliente_esistente.iloc[0]['Nome']
            st.sidebar.info(f"👤 Cliente storico trovato: {nome_automatico}")
            
    input_nome = st.text_input("Nome Cliente (Inserisci o modifica)", value=nome_automatico)
    
    st.markdown("---")
    input_stato = st.selectbox(
        "Stato Postazione", 
        ["In Attesa (Giallo)", "Confermato (Rosso)", "Pagato (Blu)", "Libero/No-Show (Verde)"]
    )
    input_prezzo = st.number_input("Prezzo Giornaliero (€)", min_value=0.0, step=1.0)
    
    submit = st.form_submit_button("Applica Modifiche")

# --- LOGICA DI SALVATAGGIO (Suddivisione in singoli giorni) ---
if submit:
    if len(date_selezionate) > 0 and input_telefono:
        data_inizio = date_selezionate[0]
        data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
        
        # 1. Aggiornamento o inserimento nell'anagrafica unica clienti
        if input_nome:
            if input_telefono in df_clienti['Telefono'].values:
                df_clienti.loc[df_clienti['Telefono'] == input_telefono, 'Nome'] = input_nome
            else:
                nuovo_c = pd.DataFrame([{"Telefono": input_telefono, "Nome": input_nome}])
                df_clienti = pd.concat([df_clienti, nuovo_c], ignore_index=True)
            df_clienti.to_csv(FILE_CLIENTI, index=False)
            
        # 2. Elaborazione giorno per giorno (Ciclo sulle singole date)
        giorni_totali = (data_fine - data_inizio).days + 1
        
        for i in range(giorni_totali):
            giorno_corrente = (data_inizio + timedelta(days=i)).strftime("%Y-%m-%d")
            
            # Rimuove la vecchia riga specifica per quel giorno e quella postazione
            df_pren = df_pren[~((df_pren['Data'] == giorno_corrente) & (df_pren['Ombrellone'] == input_ombrellone) & (df_pren['Fila'] == input_fila))]
            
            # Se lo stato NON è impostato su Libero/No-Show, salva la prenotazione per quella giornata
            if "Libero" not in input_stato:
                stato_pulito = input_stato.split(" ")[0]
                if stato_pulito == "In":
                    stato_pulito = "Attesa"
                    
                nuova_p = pd.DataFrame([{
                    "Data": giorno_corrente,
                    "Fila": input_fila,
                    "Ombrellone": input_ombrellone,
                    "Telefono": input_telefono,
                    "Stato": stato_pulito,
                    "Prezzo_Giorno": input_prezzo
                }])
                df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
                
        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
        st.sidebar.success("✅ Modifica salvata correttamente!")
        st.rerun()
    else:
        st.sidebar.error("⚠️ Compila le date e il numero di telefono per procedere.")

# --- SCHERMATA PRINCIPALE: MAPPA DINAMICA COLORATA ---
data_visiva = st.date_input("Seleziona la data da visualizzare sul planning:", date.today())
data_visiva_str = data_visiva.strftime("%Y-%m-%d")

# Unione delle prenotazioni odierne con i nomi corretti tratti dall'anagrafica
df_oggi = df_pren[df_pren['Data'] == data_visiva_str]
if not df_oggi.empty and not df_clienti.empty:
    df_oggi = pd.merge(df_oggi, df_clienti, on="Telefono", how="left")

# Funzione per determinare colori e scritte per ogni ombrellone della griglia
def controlla_posto(numero_ombrellone, fila):
    if df_oggi.empty:
        return "#28a745", "Libero", ""
        
    record = df_oggi[(df_oggi['Ombrellone'] == numero_ombrellone) & (df_oggi['Fila'] == fila)]
    if record.empty:
        return "#28a745", "Libero", ""
        
    stato = record.iloc[0]['Stato']
    nome_c = record.iloc[0]['Nome']
    prezzo_g = record.iloc[0]['Prezzo_Giorno']
    
    if stato == "Attesa":
        return "#ffc107", f"{nome_c}", f"In Attesa - €{prezzo_g:.0f}"
    elif stato == "Confermato":
        return "#dc3545", f"{nome_c}", f"Confermato - €{prezzo_g:.0f}"
    elif stato == "Pagato":
        return "#007bff", f"{nome_c}", f"Pagato - €{prezzo_g:.0f}"
        
    return "#28a745", "Libero", ""

# Rendering grafico delle due file da 7 postazioni ciascuna
for nome_fila in ["Prima Fila", "Seconda Fila"]:
    st.subheader(nome_fila)
    colonne_griglia = st.columns(7) 
    
    for i in range(7):
        numero_omb = i + 1
        colore_box, titolo, sottotitolo = controlla_posto(numero_omb, nome_fila)
        
        # Struttura grafica HTML/CSS dei singoli riquadri degli ombrelloni
        box_html = f"""
        <div style="background-color: {colore_box}; padding: 12px; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; min-height: 105px; border: 1px solid rgba(0,0,0,0.1);">
            <span style="font-size: 15px;">Omb. {numero_omb}</span><br>
            <hr style="margin: 4px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);">
            <span style="font-size: 13px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{titolo}</span>
            <span style="font-size: 11px; font-weight: normal; opacity: 0.95;">{sottotitolo}</span>
        </div>
        """
        colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)

st.divider()

# Tabella analitica riassuntiva a fondo pagina
st.subheader("📋 Elenco Dettagliato del Giorno")
if not df_oggi.empty:
    st.dataframe(df_oggi[["Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno"]], use_container_width=True)
else:
    st.info("Nessuna prenotazione attiva registrata per questa data.")