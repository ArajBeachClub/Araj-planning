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
import urllib.parse
import urllib.request

FILE_PRENOTAZIONI = 'prenotazioni.csv'
FILE_CLIENTI = 'clienti.csv'

# ==========================================
# 🤖 CONFIGURAZIONE BOT TELEGRAM (GRATIS)
# ==========================================
TELEGRAM_TOKEN = "8804050943:AAHvXVmSnEUPlvV6mj33JGGQHfhosnqcC2U"
TELEGRAM_CHAT_ID = "8663794616"  

def invia_notifica_telegram(messaggio):
    messaggio_codificato = urllib.parse.quote(messaggio)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={messaggio_codificato}"
    try:
        urllib.request.urlopen(url)
        return True
    except Exception:
        return False

# ==========================================
# ⚙️ CONFIGURAZIONE TARIFFE E STAGIONI
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

STATI_MAP = {
    "In Attesa (Giallo)": "Attesa",
    "Confermato (Rosso)": "Confermato",
    "Pagato (Blu)": "Pagato",
    "Liberato Solo Mattina (Rivendibile)": "Libero_Mat",
    "Liberato Solo Pomeriggio (Rivendibile)": "Libero_Pom",
    "Completamente Libero / Cancella (Verde)": "Libero"
}

CONFIGURAZIONE_COLONNE = {
    "Stato": st.column_config.SelectboxColumn("Stato", options=["Attesa", "Confermato", "Pagato", "Libero_Mat", "Libero_Pom", "Libero"]),
    "Fila": st.column_config.SelectboxColumn("Fila", options=list(CAPIENZA_FILE.keys())),
    "Durata": st.column_config.SelectboxColumn("Durata", options=["Giornata Intera", "Mezza Giornata (fino 13 / da 15.30)", "Solo 1 Persona (Postazione Ridotta)"]),
    "Prezzo_Giorno": st.column_config.NumberColumn("Prezzo (€)", step=1.0),
    "Persone": st.column_config.NumberColumn("Persone", min_value=1, step=1),
    "Note": st.column_config.TextColumn("Note / Memo")
}

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
        if "Note" not in df.columns: df["Note"] = ""
        
        df["Hotel"] = df["Hotel"].fillna("")
        df["Persone"] = df["Persone"].fillna(2)
        df["Durata"] = df["Durata"].fillna("Giornata Intera")
        df["Extra"] = df["Extra"].fillna("")
        df["Nome"] = df["Nome"].fillna("")
        df["Note"] = df["Note"].fillna("")
        return df
    return pd.DataFrame(columns=["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Hotel", "Persone", "Durata", "Extra", "Note"])

st.set_page_config(page_title="Beach Pass Pro", layout="wide")
st.title("🏖️ Beach Pass - Planning Ombrelloni Pro")

df_clienti = carica_clienti()
df_pren = carica_prenotazioni()

# --- 🔍 MOTORE DI RICERCA CON MODIFICA RAPIDA COMPLETA ---
with st.expander("🔍 Cerca Cliente / Modifica Rapida", expanded=False):
    ricerca = st.text_input("Inserisci una parte del Nome, del Telefono o dell'Hotel:", placeholder="Es. Mario, 340123..., Miramare").strip()
    if ricerca:
        if not df_pren.empty:
            mask_nome = df_pren['Nome'].astype(str).str.contains(ricerca, case=False, na=False)
            mask_tel = df_pren['Telefono'].astype(str).str.contains(ricerca, case=False, na=False)
            mask_hotel = df_pren['Hotel'].astype(str).str.contains(ricerca, case=False, na=False)
            
            risultati = df_pren[mask_nome | mask_tel | mask_hotel].sort_values(by="Data")
            
            if not risultati.empty:
                st.success(f"Trovate {len(risultati)} prenotazioni. Fai doppio clic sulle celle per modificarle (Stato, Prezzo, Data, Extra, Note)!")
                
                colonne_ordine = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Hotel", "Stato", "Prezzo_Giorno", "Persone", "Durata", "Extra", "Note"]
                risultati_filtrati = risultati[colonne_ordine]
                
                edited_df = st.data_editor(risultati_filtrati, num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_ricerca")
                
                if st.button("💾 Salva Modifiche da Ricerca"):
                    df_pren = df_pren.drop(risultati.index)
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
    df_occupati = df_pren[(df_pren['Data'].isin(date_range)) & (df_pren['Fila'] == input_fila)]
    ombrelloni_occupati = df_occupati['Ombrellone'].unique()
    ombrelloni_liberi = [i for i in range(1, max_ombrelloni_riga + 1) if i not in ombrelloni_occupati]
    
    if ombrelloni_liberi:
        st.sidebar.success(f"✅ Liberi intera giornata:\n {', '.join(map(str, ombrelloni_liberi))}")
    else:
        st.sidebar.error("❌ Tutto esaurito in questa fila!")

st.sidebar.subheader("2. Completa Prenotazione")
with st.sidebar.form("form_prenotazione"):
    col_q, col_omb = st.columns(2)
    with col_q:
        quantita_postazioni = st.number_input("Quante postazioni vicine?", min_value=1, max_value=3, value=1)
    max_start = max_ombrelloni_riga - quantita_postazioni + 1
    with col_omb:
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
    
    input_extra = st.multiselect("🏖️ Risorse Aggiuntive Libere (per postazione)", list(PREZZI_EXTRA.keys()))
    input_note = st.text_input("📝 Note / Memo (es. Ospite, Omaggio, Cagnolino)").strip()
    
    st.markdown("---")
    input_stato = st.selectbox("Stato Postazione", list(STATI_MAP.keys()))
    
    prezzo_consigliato_totale = 0.0
    if len(date_selezionate) > 0:
        prezzo_unitario = calcola_prezzo_automatico(date_selezionate[0], input_fila, input_persone, input_durata, input_extra)
        prezzo_consigliato_totale = prezzo_unitario * quantita_postazioni
        
    input_prezzo = st.number_input("Prezzo Giornaliero TOTALE (€)", min_value=0.0, value=float(prezzo_consigliato_totale), step=1.0)
    st.markdown("---")
    forza_sovrascrittura = st.checkbox("⚠️ Consenti Sovrascrittura (Spunta per aggiornare o rimpiazzare)")
    submit = st.form_submit_button("Applica Modifiche")

if submit:
    if len(date_selezionate) > 0 and input_nome:
        data_inizio = date_selezionate[0]
        data_fine = date_selezionate[1] if len(date_selezionate) > 1 else data_inizio
        giorni_totali = (data_fine - data_inizio).days + 1
        date_list_str = [(data_inizio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(giorni_totali)]
        ombrelloni_richiesti = [input_ombrellone + j for j in range(quantita_postazioni)]
        
        sovrapposizioni = df_pren[(df_pren['Data'].isin(date_list_str)) & (df_pren['Fila'] == input_fila) & (df_pren['Ombrellone'].isin(ombrelloni_richiesti))]
        stato_pulito = STATI_MAP[input_stato]
        
        if not sovrapposizioni.empty and not forza_sovrascrittura and stato_pulito != "Libero":
            st.sidebar.error("🚨 ERRORE: POSTAZIONE GIÀ OCCUPATA!")
            for _, row_conf in sovrapposizioni.drop_duplicates(subset=['Ombrellone', 'Nome']).iterrows():
                d = row_conf['Data']
                d_ita = f"{d[8:10]}/{d[5:7]}/{d[0:4]}"
                st.sidebar.warning(f"👉 Omb. {row_conf['Ombrellone']} prenotato da {row_conf['Nome']} ({d_ita})")
        else:
            if input_telefono:
                if input_telefono in df_clienti['Telefono'].values:
                    df_clienti.loc[df_clienti['Telefono'] == input_telefono, 'Nome'] = input_nome
                else:
                    nuovo_c = pd.DataFrame([{"Telefono": input_telefono, "Nome": input_nome}])
                    df_clienti = pd.concat([df_clienti, nuovo_c], ignore_index=True)
                df_clienti.to_csv(FILE_CLIENTI, index=False)
                
            for i in range(giorni_totali):
                giorno_corrente_obj = data_inizio + timedelta(days=i)
                giorno_corrente_str = giorno_corrente_obj.strftime("%Y-%m-%d")
                prezzo_giorno_unitario = calcola_prezzo_automatico(giorno_corrente_obj, input_fila, input_persone, input_durata, input_extra)
                prezzo_finale_unitario = input_prezzo / quantita_postazioni if input_prezzo != prezzo_consigliato_totale else prezzo_giorno_unitario
                
                for j in range(quantita_postazioni):
                    omb_corrente = input_ombrellone + j
                    df_pren = df_pren[~((df_pren['Data'] == giorno_corrente_str) & (df_pren['Ombrellone'] == omb_corrente) & (df_pren['Fila'] == input_fila))]
                    
                    if stato_pulito != "Libero":
                        nuova_p = pd.DataFrame([{
                            "Data": giorno_corrente_str, "Fila": input_fila, "Ombrellone": omb_corrente,
                            "Nome": input_nome, "Telefono": input_telefono, "Stato": stato_pulito,
                            "Prezzo_Giorno": prezzo_finale_unitario, "Hotel": str(input_hotel).strip(),
                            "Persone": input_persone, "Durata": input_durata, "Extra": ", ".join(input_extra), "Note": input_note
                        }])
                        df_pren = pd.concat([df_pren, nuova_p], ignore_index=True)
            df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
            st.sidebar.success("✅ Salvataggio completato!")
            st.rerun()
    else:
        st.sidebar.error("⚠️ Inserisci Data e NOME del Cliente.")

st.sidebar.markdown("---")

# --- AREA DEMO (GRATIS) ---
st.sidebar.subheader("🤖 Simulazione Assistente AI")
st.sidebar.info("Clicca qui domani per far vedere la notifica in tempo reale su Telegram!")
if st.sidebar.button("📞 Simula Chiamata AI (Invia a Telegram)", type="primary"):
    testo_demo = "🚨 NUOVA PRENOTAZIONE DA AI 🚨\n\n👤 Nome: Alessandro Bianchi\n📱 Telefono: 340 123 4567\n📅 Date: 08 Agosto 2026\n🏖 Fila richiesta: Prima Fila\n👥 Persone: 2\n\n👉 Controlla il gestionale e registrala!"
    if invia_notifica_telegram(testo_demo):
        st.sidebar.success("Notifica inviata! Guarda il telefono.")
    else:
        st.sidebar.error("Errore nell'invio.")

st.sidebar.markdown("---")

# --- 💬 COMUNICAZIONI CLIENTE AVANZATE ---
st.sidebar.subheader("💬 Invia Conferma (Gratis)")

operatore = st.sidebar.selectbox("👤 Operatore", ["Hiba Laawissi", "Eduardo Bustamante", "Alberto Bertolotti"])
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
            testo_base = f"Gentile {nome_wa},\n\nLa sua prenotazione {stringa_date_ita} è stata registrata correttamente.\n\nLe ricordiamo di arrivare entro le ore 11:00. In caso di ritardo, la preghiamo di avvisare tempestivamente inviando un messaggio WhatsApp al numero +39 3391789319, indicando il nome di riferimento e le date della prenotazione.\n\nIn caso contrario, la prenotazione decadrà dal sistema e la postazione verrà liberata.\n\nGrazie e a presto!\n\n{operatore}\nAraj Beach Club"
            oggetto_email = "Conferma Prenotazione - Araj Beach Club"
        else:
            testo_base = f"Dear {nome_wa},\n\nYour reservation {stringa_date_eng} has been successfully recorded.\n\nWe remind you to arrive by 11:00 AM. In case of delay, please notify us by sending a WhatsApp message to +39 3391789319 indicating your reference name and the dates of your reservation.\n\nOtherwise, the reservation will be automatically cancelled and the spot released.\n\nThank you!\n\n{operatore}\nAraj Beach Club"
            oggetto_email = "Reservation Confirmation - Araj Beach Club"
    else:
        if lingua_scelta == "Italiano":
            testo_base = f"Gentile Staff di {nome_wa},\n\nConfermiamo con piacere la prenotazione {stringa_date_ita} per i vostri ospiti.\n\nVi preghiamo di comunicare eventuali ritardi tramite WhatsApp al numero +39 3391789319 per evitare la cancellazione automatica della postazione alle ore 11:00.\n\nGrazie per la preziosa collaborazione!\n\n{operatore}\nAraj Beach Club"
            oggetto_email = f"Conferma Prenotazione {stringa_date_ita} - Araj Beach Club"
        else:
            testo_base = f"Dear Staff at {nome_wa},\n\nWe are pleased to confirm the reservation {stringa_date_eng} for your guests.\n\nPlease notify us of any delays via WhatsApp at +39 3391789319 to avoid automatic cancellation of the spot at 11:00 AM.\n\nThank you for your cooperation!\n\n{operatore}\nAraj Beach Club"
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
else:
    st.sidebar.caption("Inserisci Nome e Date per preparare il messaggio.")

# --- MAPPA VISIVA E TABELLA INFERIORE INTERATTIVA ---
data_visiva = st.date_input("Seleziona data del planning:", date.today(), format="DD/MM/YYYY")
data_visiva_str = data_visiva.strftime("%Y-%m-%d")
df_oggi = df_pren[df_pren['Data'] == data_visiva_str]
data_formattata_ita = f"{data_visiva.day} {MESI_ITA[data_visiva.month]} {data_visiva.year}"
st.header(f"📅 Planning del {data_formattata_ita}")
st.divider()

def controlla_posto(numero_ombrellone, fila):
    if df_oggi.empty: return "#28a745", "Libero", "", "", ""
    record = df_oggi[(df_oggi['Ombrellone'] == numero_ombrellone) & (df_oggi['Fila'] == fila)]
    if record.empty: return "#28a745", "Libero", "", "", ""
    
    stato = record.iloc[0]['Stato']
    prezzo_g = record.iloc[0]['Prezzo_Giorno']
    pers = record.iloc[0].get('Persone', 2)
    durata = record.iloc[0].get('Durata', "")
    extra = record.iloc[0].get('Extra', "")
    nome_c = record.iloc[0].get('Nome', "")
    
    badge_durata = "🌗" if "Mezza" in str(durata) else ""
    badge_extra = "➕" if extra else ""
    hotel_c = record.iloc[0].get('Hotel', "")
    hotel_html = f"<span style='font-size: 11px; color: #ffe8a1; display: block;'>🏨 {hotel_c}</span>" if hotel_c and not pd.isna(hotel_c) else ""
    dettagli = f"€{prezzo_g:.0f} | 👤 {pers} {badge_durata}{badge_extra}"
    badge_rivendibile, colore_box = "", "#28a745"
    
    if stato == "Attesa": colore_box = "#ffc107"
    elif stato == "Confermato": colore_box = "#dc3545"
    elif stato == "Pagato": colore_box = "#007bff"
    elif stato == "Libero_Mat":
        colore_box = "#17a2b8"
        badge_rivendibile = "<span style='background:#fff; color:#17a2b8; padding:2px 4px; border-radius:4px; font-weight:bold; font-size:10px; display:inline-block; margin-bottom:4px;'>🌅 LIBERO MATTINA</span><br>"
    elif stato == "Libero_Pom":
        colore_box = "#17a2b8"
        badge_rivendibile = "<span style='background:#fff; color:#17a2b8; padding:2px 4px; border-radius:4px; font-weight:bold; font-size:10px; display:inline-block; margin-bottom:4px;'>🌇 LIBERO POMERIGG.</span><br>"
    return colore_box, f"{nome_c}", dettagli, hotel_html, badge_rivendibile

for nome_fila, max_posti in CAPIENZA_FILE.items():
    st.subheader(nome_fila)
    colonne_griglia = st.columns(max_posti) 
    for i in range(max_posti):
        numero_omb = i + 1
        colore_box, titolo, sottotitolo, hotel_str, badge_rivend = controlla_posto(numero_omb, nome_fila)
        box_html = f"<div style='background-color: {colore_box}; padding: 8px; border-radius: 6px; text-align: center; color: white; margin-bottom: 5px; min-height: 90px; border: 1px solid rgba(0,0,0,0.1);'><span style='font-size: 14px; font-weight: bold;'>{numero_omb}</span><br><hr style='margin: 3px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);'>{badge_rivend}<span style='font-size: 11px; font-weight: bold; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{titolo}</span><span style='font-size: 10px; font-weight: normal; display: block;'>{sottotitolo}</span>{hotel_str}</div>"
        colonne_griglia[i].markdown(box_html, unsafe_allow_html=True)

st.divider()

# --- ELENCO DETTAGLIATO MODIFICABILE ---
st.subheader("📋 Elenco Dettagliato (Modificabile)")
if not df_oggi.empty:
    st.info("💡 Fai doppio clic sulle celle per cambiare lo Stato (es. in Pagato), aggiornare il Prezzo, le Date o aggiungere Extra, poi clicca su Salva!")
    colonne_tabella = ["Data", "Fila", "Ombrellone", "Nome", "Telefono", "Stato", "Prezzo_Giorno", "Persone", "Durata", "Extra", "Note"]
    if 'Hotel' in df_oggi.columns: 
        colonne_tabella.insert(4, "Hotel")
    
    edited_oggi = st.data_editor(df_oggi[colonne_tabella], num_rows="dynamic", use_container_width=True, column_config=CONFIGURAZIONE_COLONNE, key="editor_oggi")
    
    if st.button("💾 Salva Modifiche Tabella", type="primary"):
        df_pren = df_pren.drop(df_oggi.index)
        df_pren = pd.concat([df_pren, edited_oggi], ignore_index=True)
        df_pren.to_csv(FILE_PRENOTAZIONI, index=False)
        st.success("✅ Dati della giornata aggiornati!")
        st.rerun()
else:
    st.info("Nessuna prenotazione registrata per la data di oggi.")