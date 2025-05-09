#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Esempio di utilizzo del gestore database catastale
=================================================
Questo script mostra esempi pratici di come utilizzare
la classe CatastoDBManager per interagire con il database.

Autore: Marco Santoro
Data: 17/04/2025
"""

from catasto_db_manager import CatastoDBManager
from datetime import date, datetime
import json
import os
import sys

def stampa_intestazione(titolo):
    """Stampa un'intestazione formattata"""
    print("\n" + "=" * 80)
    print(f" {titolo} ".center(80, "="))
    print("=" * 80)

def inserisci_possessore(db, comune_preselezionato=None):
    """
    Funzione per l'inserimento di un nuovo possessore
    
    Args:
        db: Istanza del database manager
        comune_preselezionato: Nome del comune (opzionale)
        
    Returns:
        Optional[int]: ID del possessore inserito, None in caso di errore
    """
    stampa_intestazione("AGGIUNGI NUOVO POSSESSORE")
    
    # Se il comune non è preselezionato, chiedilo all'utente
    if comune_preselezionato:
        comune = comune_preselezionato
        print(f"Comune: {comune}")
    else:
        comune = input("Comune: ")
    
    cognome_nome = input("Cognome e nome: ")
    paternita = input("Paternita (es. 'fu Roberto'): ")
    
    # Calcola automaticamente il nome completo
    nome_completo = f"{cognome_nome} {paternita}"
    conferma = input(f"Nome completo: [{nome_completo}] (premi INVIO per confermare o inserisci un valore diverso): ")
    if conferma:
        nome_completo = conferma
    
    if comune and cognome_nome:
        # Esegui l'inserimento tramite procedura
        possessore_id = db.insert_possessore(comune, cognome_nome, paternita, nome_completo, True)
        if possessore_id:
            print(f"Possessore {nome_completo} inserito con successo (ID: {possessore_id})")
            return possessore_id
        else:
            print("Errore durante l'inserimento")
    else:
        print("Dati incompleti, operazione annullata")
    
    return None

def inserisci_localita(db):
    """
    Funzione per l'inserimento di una nuova località
    
    Args:
        db: Istanza del database manager
        
    Returns:
        Optional[int]: ID della località inserita, None in caso di errore
    """
    stampa_intestazione("AGGIUNGI NUOVA LOCALITA")
    
    comune = input("Comune: ")
    nome = input("Nome localita: ")
    
    if not comune or not nome:
        print("Dati incompleti, operazione annullata")
        return None
    
    # Chiedi il tipo di località
    print("\nSeleziona il tipo di localita:")
    print("1. Regione")
    print("2. Via")
    print("3. Borgata")
    tipo_scelta = input("Scegli un'opzione (1-3): ")
    
    tipo_mapping = {
        "1": "regione",
        "2": "via",
        "3": "borgata"
    }
    
    if tipo_scelta not in tipo_mapping:
        print("Scelta non valida, operazione annullata")
        return None
    
    tipo = tipo_mapping[tipo_scelta]
    
    # Chiedi il civico solo per le vie
    civico = None
    if tipo == "via":
        civico_input = input("Numero civico (opzionale): ")
        if civico_input and civico_input.isdigit():
            civico = int(civico_input)
    
    # Esegui l'inserimento
    try:
        query = """
        INSERT INTO localita (comune_nome, nome, tipo, civico) 
        VALUES (%s, %s, %s, %s) 
        RETURNING id
        """
        if db.execute_query(query, (comune, nome, tipo, civico)):
            result = db.fetchone()
            if result:
                localita_id = result['id']
                db.commit()
                print(f"Localita {nome} inserita con successo (ID: {localita_id})")
                return localita_id
    except Exception as e:
        print(f"Errore durante l'inserimento della localita: {e}")
        db.rollback()
    
    print("Errore durante l'inserimento o localita gia esistente")
    return None

def menu_principale(db):
    """Menu principale per testare varie funzionalità"""
    while True:
        stampa_intestazione("MENU PRINCIPALE")
        print("1. Consultazione dati")
        print("2. Inserimento e gestione dati")
        print("3. Generazione report")
        print("4. Manutenzione database")
        print("5. Sistema di audit")  # Nuova opzione
        print("6. Esci")  # Cambiato da 5 a 6
        
        scelta = input("\nSeleziona un'opzione (1-6): ")  # Cambiato da 1-5 a 1-6
        
        if scelta == "1":
            menu_consultazione(db)
        elif scelta == "2":
            menu_inserimento(db)
        elif scelta == "3":
            menu_report(db)
        elif scelta == "4":
            menu_manutenzione(db)
        elif scelta == "5":  # Nuova opzione
            menu_audit(db)
        elif scelta == "6":  # Cambiato da 5 a 6
            break
        else:
            print("Opzione non valida!")

def aggiungi_comune(db):
    """Funzione per l'inserimento di un nuovo comune"""
    stampa_intestazione("AGGIUNGI NUOVO COMUNE")
    nome = input("Nome comune: ")
    provincia = input("Provincia: ")
    regione = input("Regione: ")
    
    if nome and provincia and regione:
        # Recupera periodi storici disponibili dal database
        if db.execute_query("SELECT id, nome, anno_inizio, anno_fine FROM periodo_storico ORDER BY anno_inizio"):
            periodi = db.fetchall()
            
            if periodi:
                print("\nSeleziona il periodo storico:")
                for i, periodo in enumerate(periodi, 1):
                    anno_fine = periodo['anno_fine'] if periodo['anno_fine'] else 'presente'
                    print(f"{i}. {periodo['nome']} ({periodo['anno_inizio']}-{anno_fine})")
                
                scelta = input("\nNumero periodo (default: Repubblica Italiana): ")
                
                # Imposta il periodo predefinito (Repubblica Italiana)
                periodo_id = next((p['id'] for p in periodi if p['nome'] == 'Repubblica Italiana'), periodi[-1]['id'])
                
                # Se l'utente ha scelto un periodo
                if scelta.isdigit() and 1 <= int(scelta) <= len(periodi):
                    periodo_id = periodi[int(scelta)-1]['id']
                
                # Esegui l'inserimento con il periodo
                if db.execute_query(
                    "INSERT INTO comune (nome, provincia, regione, periodo_id) VALUES (%s, %s, %s, %s) ON CONFLICT (nome) DO NOTHING",
                    (nome, provincia, regione, periodo_id)
                ):
                    db.commit()
                    print(f"Comune {nome} inserito con successo o già esistente")
                else:
                    print("Errore durante l'inserimento")
            else:
                print("Impossibile recuperare i periodi storici, verrà usato il periodo predefinito")
                # Inserimento senza periodo (usa default)
                if db.execute_query(
                    "INSERT INTO comune (nome, provincia, regione) VALUES (%s, %s, %s) ON CONFLICT (nome) DO NOTHING",
                    (nome, provincia, regione)
                ):
                    db.commit()
                    print(f"Comune {nome} inserito con successo o già esistente")
                else:
                    print("Errore durante l'inserimento")
        else:
            print("Errore nel recupero dei periodi storici, verrà usato il periodo predefinito")
            # Inserimento senza periodo (usa default)
            if db.execute_query(
                "INSERT INTO comune (nome, provincia, regione) VALUES (%s, %s, %s) ON CONFLICT (nome) DO NOTHING",
                (nome, provincia, regione)
            ):
                db.commit()
                print(f"Comune {nome} inserito con successo o già esistente")
            else:
                print("Errore durante l'inserimento")
    else:
        print("Dati incompleti, operazione annullata")
def menu_consultazione(db):
    """Menu per operazioni di consultazione"""
    while True:
        stampa_intestazione("CONSULTAZIONE DATI")
        print("1. Elenco comuni")
        print("2. Elenco partite per comune")
        print("3. Elenco possessori per comune")
        print("4. Ricerca partite")
        print("5. Dettagli partita")
        print("6. Elenco localita per comune")
        print("7. Torna al menu principale")
        
        scelta = input("\nSeleziona un'opzione (1-7): ")
        
        if scelta == "1":
            # Elenco comuni
            search_term = input("Termine di ricerca (lascia vuoto per tutti): ")
            comuni = db.get_comuni(search_term)
            stampa_intestazione(f"COMUNI REGISTRATI ({len(comuni)})")
            for c in comuni:
                print(f"{c['nome']} ({c['provincia']}, {c['regione']})")
        
        elif scelta == "2":
            # Elenco partite per comune
            comune = input("Inserisci il nome del comune (anche parziale): ")
            partite = db.get_partite_by_comune(comune)
            stampa_intestazione(f"PARTITE DEL COMUNE {comune.upper()} ({len(partite)})")
            for p in partite:
                stato = "ATTIVA" if p['stato'] == 'attiva' else "INATTIVA"
                print(f"ID: {p['id']} - Partita {p['numero_partita']} - {p['tipo']} - {stato}")
                if p['possessori']:
                    print(f"  Possessori: {p['possessori']}")
                print(f"  Immobili: {p['num_immobili']}")
                print()
        
        elif scelta == "3":
            # Elenco possessori per comune
            comune = input("Inserisci il nome del comune: ")
            possessori = db.get_possessori_by_comune(comune)
            stampa_intestazione(f"POSSESSORI DEL COMUNE {comune.upper()} ({len(possessori)})")
            for p in possessori:
                stato = "ATTIVO" if p['attivo'] else "NON ATTIVO"
                print(f"ID: {p['id']} - {p['nome_completo']} - {stato}")
        
        elif scelta == "4":
            # Ricerca partite
            stampa_intestazione("RICERCA PARTITE")
            print("Inserisci i criteri di ricerca (lascia vuoto per non specificare)")
            comune = input("Comune (anche parziale): ")
            numero = input("Numero partita: ")
            possessore = input("Nome possessore (anche parziale): ")
            natura = input("Natura immobile (anche parziale): ")
            
            # Converti il numero in intero se specificato
            numero_partita = int(numero) if numero.strip() else None
            
            # Esegui la ricerca
            partite = db.search_partite(
                comune_nome=comune if comune.strip() else None,
                numero_partita=numero_partita,
                possessore=possessore if possessore.strip() else None,
                immobile_natura=natura if natura.strip() else None
            )
            
            stampa_intestazione(f"RISULTATI RICERCA ({len(partite)})")
            for p in partite:
                print(f"ID: {p['id']} - {p['comune_nome']} - Partita {p['numero_partita']} - {p['tipo']}")
        
        elif scelta == "5":
            # Dettagli partita
            id_partita = input("Inserisci l'ID della partita: ")
            if id_partita.isdigit():
                partita = db.get_partita_details(int(id_partita))
                if partita:
                    stampa_intestazione(f"DETTAGLI PARTITA {partita['numero_partita']} - {partita['comune_nome']}")
                    print(f"ID: {partita['id']}")
                    print(f"Tipo: {partita['tipo']}")
                    print(f"Stato: {partita['stato']}")
                    print(f"Data impianto: {partita['data_impianto']}")
                    if partita['data_chiusura']:
                        print(f"Data chiusura: {partita['data_chiusura']}")
                    
                    # Possessori
                    print("\nPOSSESSORI:")
                    for pos in partita['possessori']:
                        print(f"- ID: {pos['id']} - {pos['nome_completo']}")
                        if pos['quota']:
                            print(f"  Quota: {pos['quota']}")
                    
                    # Immobili
                    print("\nIMMOBILI:")
                    for imm in partita['immobili']:
                        print(f"- ID: {imm['id']} - {imm['natura']} - {imm['localita_nome']}")
                        if 'tipologia' in imm and imm['tipologia']:
                            print(f"  Tipologia: {imm['tipologia']}")
                        if imm['consistenza']:
                            print(f"  Consistenza: {imm['consistenza']}")
                        if imm['classificazione']:
                            print(f"  Classificazione: {imm['classificazione']}")
                    
                    # Variazioni
                    if partita['variazioni']:
                        print("\nVARIAZIONI:")
                        for var in partita['variazioni']:
                            print(f"- ID: {var['id']} - {var['tipo']} del {var['data_variazione']}")
                            if var['tipo_contratto']:
                                print(f"  Contratto: {var['tipo_contratto']} del {var['data_contratto']}")
                                if var['notaio']:
                                    print(f"  Notaio: {var['notaio']}")
                else:
                    print("Partita non trovata!")
            else:
                print("ID non valido!")
        
        elif scelta == "6":
            # Elenco località per comune
            comune = input("Inserisci il nome del comune (anche parziale): ")
            if comune:
                query = """
                SELECT id, nome, tipo, civico 
                FROM localita 
                WHERE comune_nome ILIKE %s 
                ORDER BY tipo, nome
                """
                if db.execute_query(query, (f"%{comune}%",)):
                    localita = db.fetchall()
                    stampa_intestazione(f"LOCALITA DEL COMUNE {comune.upper()} ({len(localita)})")
                    for loc in localita:
                        civico_str = f", {loc['civico']}" if loc['civico'] else ""
                        print(f"ID: {loc['id']} - {loc['nome']}{civico_str} ({loc['tipo']})")
                else:
                    print("Errore durante la ricerca delle localita")
            else:
                print("Nome comune richiesto")
        
        elif scelta == "7":
            break
        else:
            print("Opzione non valida!")
        
        input("\nPremi INVIO per continuare...")

def menu_inserimento(db):
    """Menu per operazioni di inserimento e gestione"""
    while True:
        stampa_intestazione("INSERIMENTO E GESTIONE DATI")
        print("1. Aggiungi nuovo comune")
        print("2. Aggiungi nuovo possessore")
        print("3. Aggiungi nuova localita")
        print("4. Registra nuova proprieta")
        print("5. Registra passaggio di proprieta")
        print("6. Registra consultazione")
        print("7. Torna al menu principale")
        
        scelta = input("\nSeleziona un'opzione (1-7): ")
        
        if scelta == "1":
            # Aggiungi comune
            aggiungi_comune(db)
        
        elif scelta == "2":
            # Aggiungi possessore
            inserisci_possessore(db)
        
        elif scelta == "3":
            # Aggiungi località
            inserisci_localita(db)
        
        elif scelta == "4":
            # Registra nuova proprietà
            stampa_intestazione("REGISTRA NUOVA PROPRIETA")
            
            # Raccolta dati principali
            comune = input("Comune: ")
            numero_partita = input("Numero partita: ")
            
            try:
                # Verifica se i dati di base sono validi
                if not comune or not numero_partita.isdigit():
                    raise ValueError("Comune o numero partita non validi")
                
                numero_partita = int(numero_partita)
                data_impianto = input("Data impianto (YYYY-MM-DD): ")
                data_impianto = datetime.strptime(data_impianto, "%Y-%m-%d").date()
                
                # Raccolta dati possessori
                possessori = []
                while True:
                    stampa_intestazione("INSERIMENTO POSSESSORE")
                    nome_completo = input("Nome completo possessore (vuoto per terminare): ")
                    if not nome_completo:
                        break
                    
                    # Verifica se il possessore esiste già
                    possessore_id = db.check_possessore_exists(nome_completo, comune)
                    if possessore_id:
                        print(f"Possessore esistente con ID: {possessore_id}")
                        cognome_nome = input("Cognome e nome (se diverso): ")
                        paternita = input("Paternita (se diversa): ")
                        quota = input("Quota (vuoto se proprieta esclusiva): ")
                        
                        possessore = {
                            "nome_completo": nome_completo,
                            "cognome_nome": cognome_nome if cognome_nome else nome_completo.split()[0],
                            "paternita": paternita,
                        }
                    else:
                        # Nuovo possessore
                        print(f"Possessore non trovato. Inserisci i dettagli:")
                        cognome_nome = input("Cognome e nome: ")
                        paternita = input("Paternita: ")
                        quota = input("Quota (vuoto se proprieta esclusiva): ")
                        
                        possessore = {
                            "nome_completo": nome_completo,
                            "cognome_nome": cognome_nome,
                            "paternita": paternita
                        }
                    
                    if quota:
                        possessore["quota"] = quota
                    
                    possessori.append(possessore)
                    print(f"Possessore {nome_completo} aggiunto")
                
                if not possessori:
                    raise ValueError("Nessun possessore inserito")
                
                # Raccolta dati immobili
                immobili = []
                while True:
                    stampa_intestazione("INSERIMENTO IMMOBILE")
                    natura = input("Natura immobile (vuoto per terminare): ")
                    if not natura:
                        break
                    
                    # Aggiunta della tipologia immobile
                    tipologia = input("Tipologia immobile (opzionale): ")
                    
                    # Selezione o inserimento località
                    print("\nGestione localita:")
                    print("1. Usa localita esistente")
                    print("2. Inserisci nuova localita")
                    scelta_localita = input("Scegli un'opzione (1-2): ")
                    
                    localita_id = None
                    localita_nome = None
                    tipo_localita = None
                    
                    if scelta_localita == "1":
                        # Cerca e usa una località esistente
                        localita_nome = input("Nome localita esistente: ")
                        query = "SELECT id, nome, tipo FROM localita WHERE nome ILIKE %s AND comune_nome ILIKE %s"
                        if db.execute_query(query, (f"%{localita_nome}%", f"%{comune}%")):
                            localita_risultati = db.fetchall()
                            
                            if not localita_risultati:
                                print("Nessuna localita trovata con questo nome")
                                continue
                            
                            print("\nLocalita trovate:")
                            for i, loc in enumerate(localita_risultati, 1):
                                print(f"{i}. {loc['nome']} ({loc['tipo']}), ID: {loc['id']}")
                            
                            scelta_idx = input("Seleziona una localita (numero): ")
                            if scelta_idx.isdigit() and 0 < int(scelta_idx) <= len(localita_risultati):
                                localita_selezionata = localita_risultati[int(scelta_idx) - 1]
                                localita_id = localita_selezionata['id']
                                localita_nome = localita_selezionata['nome']
                                tipo_localita = localita_selezionata['tipo']
                            else:
                                print("Scelta non valida")
                                continue
                        else:
                            print("Errore durante la ricerca delle localita")
                            continue
                    
                    elif scelta_localita == "2":
                        # Inserisci una nuova località
                        localita_id = inserisci_localita(db)
                        if not localita_id:
                            print("Inserimento localita fallito")
                            continue
                    else:
                        print("Scelta non valida")
                        continue
                    
                    # Altri dati immobile
                    classificazione = input("Classificazione: ")
                    
                    numero_piani = input("Numero piani (opzionale): ")
                    numero_vani = input("Numero vani (opzionale): ")
                    consistenza = input("Consistenza (opzionale): ")
                    
                    immobile = {
                        "natura": natura,
                        "tipologia": tipologia,  # Nuovo campo tipologia
                        "localita_id": localita_id,  # Usiamo l'ID invece del nome
                        "classificazione": classificazione
                    }
                    
                    if numero_piani:
                        immobile["numero_piani"] = int(numero_piani)
                    if numero_vani:
                        immobile["numero_vani"] = int(numero_vani)
                    if consistenza:
                        immobile["consistenza"] = consistenza
                    
                    immobili.append(immobile)
                    print(f"Immobile {natura} aggiunto")
                
                if not immobili:
                    raise ValueError("Nessun immobile inserito")
                
                # Registrazione della proprietà usando la versione modificata
                if db.registra_nuova_proprieta_v2(
                    comune, numero_partita, data_impianto, possessori, immobili
                ):
                    print(f"Proprieta registrata con successo: {comune}, partita {numero_partita}")
                else:
                    print("Errore durante la registrazione della proprieta")
                
            except ValueError as e:
                print(f"Errore: {e}")
            except Exception as e:
                print(f"Errore imprevisto: {e}")
        
        elif scelta == "5":
            # Registra passaggio di proprietà
            stampa_intestazione("REGISTRA PASSAGGIO DI PROPRIETA")
            
            try:
                # Partita di origine
                partita_origine_id = input("ID partita di origine: ")
                if not partita_origine_id.isdigit():
                    raise ValueError("ID partita non valido")
                
                partita_origine_id = int(partita_origine_id)
                
                # Dati nuova partita
                comune = input("Comune nuova partita: ")
                numero_partita = input("Numero nuova partita: ")
                if not numero_partita.isdigit():
                    raise ValueError("Numero partita non valido")
                
                numero_partita = int(numero_partita)
                
                # Dati variazione
                tipo_variazione = input("Tipo variazione (Vendita/Successione/Frazionamento): ")
                data_variazione = input("Data variazione (YYYY-MM-DD): ")
                data_variazione = datetime.strptime(data_variazione, "%Y-%m-%d").date()
                
                # Dati contratto
                tipo_contratto = input("Tipo contratto: ")
                data_contratto = input("Data contratto (YYYY-MM-DD): ")
                data_contratto = datetime.strptime(data_contratto, "%Y-%m-%d").date()
                notaio = input("Notaio (opzionale): ")
                repertorio = input("Repertorio (opzionale): ")
                
                # Possessori e immobili
                includi_possessori = input("Specificare nuovi possessori? (s/n): ").lower() == 's'
                nuovi_possessori = None
                
                if includi_possessori:
                    nuovi_possessori = []
                    while True:
                        nome_completo = input("Nome completo possessore (vuoto per terminare): ")
                        if not nome_completo:
                            break
                        
                        # Verifica se il possessore esiste
                        possessore_id = db.check_possessore_exists(nome_completo, comune)
                        
                        if possessore_id:
                            print(f"Possessore trovato con ID: {possessore_id}")
                            cognome_nome = input("Cognome e nome (se diverso): ")
                            paternita = input("Paternita (se diversa): ")
                        else:
                            print(f"Possessore non trovato nel database.")
                            risposta = input("Vuoi inserire un nuovo possessore? (s/n): ")
                            if risposta.lower() == 's':
                                possessore_id = inserisci_possessore(db, comune)
                                if not possessore_id:
                                    continue
                                
                                # Recupera i dati del possessore appena inserito
                                db.execute_query(
                                    "SELECT cognome_nome, paternita, nome_completo FROM possessore WHERE id = %s",
                                    (possessore_id,)
                                )
                                possessore_data = db.fetchone()
                                if possessore_data:
                                    cognome_nome = possessore_data['cognome_nome']
                                    paternita = possessore_data['paternita']
                                    nome_completo = possessore_data['nome_completo']
                            else:
                                continue
                        
                        nuovi_possessori.append({
                            "nome_completo": nome_completo,
                            "cognome_nome": cognome_nome,
                            "paternita": paternita
                        })
                
                includi_immobili = input("Specificare immobili da trasferire? (s/n): ").lower() == 's'
                immobili_da_trasferire = None
                
                if includi_immobili:
                    immobili_da_trasferire = []
                    while True:
                        immobile_id = input("ID immobile da trasferire (vuoto per terminare): ")
                        if not immobile_id:
                            break
                        
                        if immobile_id.isdigit():
                            immobili_da_trasferire.append(int(immobile_id))
                
                note = input("Note (opzionale): ")
                
                # Registrazione del passaggio
                if db.registra_passaggio_proprieta(
                    partita_origine_id, comune, numero_partita, tipo_variazione, data_variazione,
                    tipo_contratto, data_contratto, notaio=notaio, repertorio=repertorio,
                    nuovi_possessori=nuovi_possessori, immobili_da_trasferire=immobili_da_trasferire,
                    note=note
                ):
                    print(f"Passaggio di proprieta registrato con successo")
                else:
                    print("Errore durante la registrazione del passaggio di proprieta")
                
            except ValueError as e:
                print(f"Errore: {e}")
            except Exception as e:
                print(f"Errore imprevisto: {e}")
        
        elif scelta == "6":
            # Registra consultazione
            stampa_intestazione("REGISTRA CONSULTAZIONE")
            
            try:
                data = input("Data consultazione (YYYY-MM-DD, vuoto per oggi): ")
                if data:
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                else:
                    data = date.today()
                
                richiedente = input("Richiedente: ")
                if not richiedente:
                    raise ValueError("Richiedente obbligatorio")
                
                documento = input("Documento identita: ")
                motivazione = input("Motivazione: ")
                materiale = input("Materiale consultato: ")
                funzionario = input("Funzionario autorizzante: ")
                
                if db.registra_consultazione(
                    data, richiedente, documento, motivazione, materiale, funzionario
                ):
                    print("Consultazione registrata con successo")
                else:
                    print("Errore durante la registrazione della consultazione")
                
            except ValueError as e:
                print(f"Errore: {e}")
            except Exception as e:
                print(f"Errore imprevisto: {e}")
        
        elif scelta == "7":
            break
        else:
            print("Opzione non valida!")
        
        input("\nPremi INVIO per continuare...")

def menu_report(db):
    """Menu per la generazione di report"""
    while True:
        stampa_intestazione("GENERAZIONE REPORT")
        print("1. Certificato di proprieta")
        print("2. Report genealogico")
        print("3. Report possessore")
        print("4. Report consultazioni")
        print("5. Torna al menu principale")
        
        scelta = input("\nSeleziona un'opzione (1-5): ")
        
        if scelta == "1":
            # Certificato di proprietà
            partita_id = input("Inserisci l'ID della partita: ")
            if partita_id.isdigit():
                certificato = db.genera_certificato_proprieta(int(partita_id))
                
                # Verifica se ci sono dati prima di proporre il salvataggio
                if certificato and not certificato.startswith('Partita con ID'):
                    stampa_intestazione("CERTIFICATO DI PROPRIETA")
                    print(certificato)
                    
                    # Salvataggio su file
                    if input("\nSalvare su file? (s/n): ").lower() == 's':
                        filename = f"certificato_partita_{partita_id}_{date.today()}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(certificato)
                        print(f"Certificato salvato nel file: {filename}")
                else:
                    print("Nessun dato disponibile per questa partita")
            else:
                print("ID non valido!")
        
        elif scelta == "2":
            # Report genealogico
            partita_id = input("Inserisci l'ID della partita: ")
            if partita_id.isdigit():
                report = db.genera_report_genealogico(int(partita_id))
                
                # Verifica se ci sono dati prima di proporre il salvataggio
                if report and not report.startswith('Partita con ID'):
                    stampa_intestazione("REPORT GENEALOGICO")
                    print(report)
                    
                    # Salvataggio su file
                    if input("\nSalvare su file? (s/n): ").lower() == 's':
                        filename = f"report_genealogico_{partita_id}_{date.today()}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(report)
                        print(f"Report salvato nel file: {filename}")
                else:
                    print("Nessun dato disponibile per questa partita")
            else:
                print("ID non valido!")
        
        elif scelta == "3":
            # Report possessore
            possessore_id = input("Inserisci l'ID del possessore: ")
            if possessore_id.isdigit():
                report = db.genera_report_possessore(int(possessore_id))
                
                # Verifica se ci sono dati prima di proporre il salvataggio
                if report and not report.startswith('Possessore con ID'):
                    stampa_intestazione("REPORT POSSESSORE")
                    print(report)
                    
                    # Salvataggio su file
                    if input("\nSalvare su file? (s/n): ").lower() == 's':
                        filename = f"report_possessore_{possessore_id}_{date.today()}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(report)
                        print(f"Report salvato nel file: {filename}")
                else:
                    print("Nessun dato disponibile per questo possessore")
            else:
                print("ID non valido!")
        
        elif scelta == "4":
            # Report consultazioni
            stampa_intestazione("REPORT CONSULTAZIONI")
            
            # Chiedi i parametri di filtro
            print("Inserisci i parametri per filtrare (lascia vuoto per non applicare filtro)")
            data_inizio_str = input("Data inizio (YYYY-MM-DD): ")
            data_fine_str = input("Data fine (YYYY-MM-DD): ")
            richiedente = input("Richiedente: ")
            
            # Converti le date
            data_inizio = None
            data_fine = None
            
            if data_inizio_str:
                try:
                    data_inizio = datetime.strptime(data_inizio_str, "%Y-%m-%d").date()
                except ValueError:
                    print("Formato data non valido, filtro non applicato")
            
            if data_fine_str:
                try:
                    data_fine = datetime.strptime(data_fine_str, "%Y-%m-%d").date()
                except ValueError:
                    print("Formato data non valido, filtro non applicato")
            
            # Verifica se specificare richiedente
            richiedente = richiedente if richiedente.strip() else None
            
            # Genera il report
            report = db.genera_report_consultazioni(data_inizio, data_fine, richiedente)
            
            if report:
                # Visualizza il report
                stampa_intestazione("REPORT CONSULTAZIONI")
                print(report)
                
                # Salvataggio su file
                if input("\nSalvare su file? (s/n): ").lower() == 's':
                    oggi = date.today().strftime("%Y%m%d")
                    filename = f"report_consultazioni_{oggi}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"Report salvato nel file: {filename}")
            else:
                print("Nessun dato disponibile o errore durante la generazione del report")
        
        elif scelta == "5":
            break
        else:
            print("Opzione non valida!")
        
        input("\nPremi INVIO per continuare...")

def menu_manutenzione(db):
    """Menu per la manutenzione del database"""
    while True:
        stampa_intestazione("MANUTENZIONE DATABASE")
        print("1. Verifica integrita database")
        print("2. Torna al menu principale")
        
        scelta = input("\nSeleziona un'opzione (1-2): ")
        
        if scelta == "1":
            # Verifica integrità
            stampa_intestazione("VERIFICA INTEGRITA DATABASE")
            print("Avvio verifica...")
            
            problemi_trovati, messaggio = db.verifica_integrita_database()
            
            if problemi_trovati:
                print("\nATTENZIONE: Sono stati rilevati problemi di integrita!")
                print(messaggio)
                
                if input("\nEseguire correzione automatica? (s/n): ").lower() == 's':
                    db.execute_query("CALL ripara_problemi_database(TRUE)")
                    db.commit()
                    print("Correzione automatica eseguita.")
                    
                    # Verifica nuovamente
                    print("\nNuova verifica dopo la correzione:")
                    problemi_trovati, messaggio = db.verifica_integrita_database()
                    if problemi_trovati:
                        print("Ci sono ancora problemi. Potrebbe essere necessario un intervento manuale.")
                    else:
                        print("Tutti i problemi sono stati risolti!")
            else:
                print("\nNessun problema di integrita rilevato. Il database è in buono stato.")
        
        elif scelta == "2":
            break
        else:
            print("Opzione non valida!")
        
        input("\nPremi INVIO per continuare...")


def menu_audit(db):
    """Menu per la gestione e consultazione del sistema di audit"""
    while True:
        stampa_intestazione("SISTEMA DI AUDIT")
        print("1. Consulta log di audit")
        print("2. Visualizza cronologia di un record")
        print("3. Genera report di audit")
        print("4. Torna al menu principale")
        
        scelta = input("\nSeleziona un'opzione (1-4): ")
        
        if scelta == "1":
            # Consultazione log di audit
            stampa_intestazione("CONSULTA LOG DI AUDIT")
            
            # Raccogli i parametri di ricerca
            print("Inserisci i parametri di ricerca (lascia vuoto per non filtrare)")
            tabella = input("Nome tabella (es. partita, possessore): ")
            
            operazione = None
            op_scelta = input("Tipo operazione (1=Inserimento, 2=Aggiornamento, 3=Cancellazione, vuoto=tutte): ")
            if op_scelta == "1":
                operazione = "I"
            elif op_scelta == "2":
                operazione = "U"
            elif op_scelta == "3":
                operazione = "D"
            
            record_id = input("ID record: ")
            record_id = int(record_id) if record_id and record_id.isdigit() else None
            
            data_inizio_str = input("Data inizio (YYYY-MM-DD): ")
            data_fine_str = input("Data fine (YYYY-MM-DD): ")
            
            utente = input("Utente: ")
            
            # Converti le date
            data_inizio = None
            data_fine = None
            
            try:
                if data_inizio_str:
                    data_inizio = datetime.strptime(data_inizio_str, "%Y-%m-%d").date()
                if data_fine_str:
                    data_fine = datetime.strptime(data_fine_str, "%Y-%m-%d").date()
            except ValueError:
                print("Formato data non valido!")
                continue
            
            # Esegui la ricerca
            logs = db.get_audit_log(
                tabella=tabella if tabella else None,
                operazione=operazione,
                record_id=record_id,
                data_inizio=data_inizio,
                data_fine=data_fine,
                utente=utente if utente else None
            )
            
            # Visualizza i risultati
            stampa_intestazione(f"RISULTATI LOG AUDIT ({len(logs)})")
            
            if not logs:
                print("Nessun log trovato per i criteri specificati")
            else:
                for log in logs:
                    op_map = {"I": "Inserimento", "U": "Aggiornamento", "D": "Cancellazione"}
                    print(f"ID: {log['id']} - {op_map.get(log['operazione'], log['operazione'])} - {log['tabella']} - Record {log['record_id']}")
                    print(f"  Timestamp: {log['timestamp']} - Utente: {log['utente']}")
                    
                    # Mostra dettagli aggiuntivi per alcuni log
                    # Limitiamo la visualizzazione in linea per non sovraccaricare l'output
                    if input("\nVisualizzare dettagli delle modifiche? (s/n): ").lower() == 's':
                        if log['operazione'] == 'U' and log['dati_prima'] and log['dati_dopo']:
                            try:
                                import json
                                dati_prima = json.loads(log['dati_prima'])
                                dati_dopo = json.loads(log['dati_dopo'])
                                
                                print("\nModifiche:")
                                for chiave in dati_prima:
                                    if chiave in dati_dopo and dati_prima[chiave] != dati_dopo[chiave]:
                                        print(f"  - {chiave}: {dati_prima[chiave]} -> {dati_dopo[chiave]}")
                            except:
                                print("  Impossibile elaborare i dettagli delle modifiche")
                        elif log['operazione'] == 'I':
                            print("  Inserimento di un nuovo record")
                        elif log['operazione'] == 'D':
                            print("  Cancellazione di un record esistente")
        
        elif scelta == "2":
            # Visualizza cronologia di un record
            stampa_intestazione("CRONOLOGIA RECORD")
            
            tabella = input("Nome tabella (es. partita, possessore): ")
            record_id = input("ID record: ")
            
            if not tabella or not record_id.isdigit():
                print("Tabella e ID record sono richiesti!")
                continue
            
            record_id = int(record_id)
            
            # Ottieni la cronologia
            history = db.get_record_history(tabella, record_id)
            
            stampa_intestazione(f"CRONOLOGIA {tabella.upper()} ID {record_id} ({len(history)} modifiche)")
            
            if not history:
                print(f"Nessuna modifica registrata per {tabella} con ID {record_id}")
            else:
                for i, record in enumerate(history, 1):
                    op_map = {"I": "Inserimento", "U": "Aggiornamento", "D": "Cancellazione"}
                    print(f"{i}. {op_map.get(record['operazione'], record['operazione'])} - {record['timestamp']} - {record['utente']}")
                    
                    if record['operazione'] == 'U':
                        print("  Modifiche:")
                        try:
                            import json
                            dati_prima = json.loads(record['dati_prima']) if record['dati_prima'] else {}
                            dati_dopo = json.loads(record['dati_dopo']) if record['dati_dopo'] else {}
                            
                            for chiave in dati_prima:
                                if chiave in dati_dopo and dati_prima[chiave] != dati_dopo[chiave]:
                                    val_prima = "NULL" if dati_prima[chiave] is None else dati_prima[chiave]
                                    val_dopo = "NULL" if dati_dopo[chiave] is None else dati_dopo[chiave]
                                    print(f"    - {chiave}: {val_prima} -> {val_dopo}")
                        except Exception as e:
                            print(f"    Impossibile elaborare i dettagli: {e}")
                    
                    print()
        
        elif scelta == "3":
            # Genera report di audit
            stampa_intestazione("GENERA REPORT DI AUDIT")
            
            # Raccogli i parametri di ricerca
            print("Inserisci i parametri per il report (lascia vuoto per non filtrare)")
            tabella = input("Nome tabella (es. partita, possessore): ")
            
            operazione = None
            op_scelta = input("Tipo operazione (1=Inserimento, 2=Aggiornamento, 3=Cancellazione, vuoto=tutte): ")
            if op_scelta == "1":
                operazione = "I"
            elif op_scelta == "2":
                operazione = "U"
            elif op_scelta == "3":
                operazione = "D"
            
            data_inizio_str = input("Data inizio (YYYY-MM-DD): ")
            data_fine_str = input("Data fine (YYYY-MM-DD): ")
            
            utente = input("Utente: ")
            
            # Converti le date
            data_inizio = None
            data_fine = None
            
            try:
                if data_inizio_str:
                    data_inizio = datetime.strptime(data_inizio_str, "%Y-%m-%d").date()
                if data_fine_str:
                    data_fine = datetime.strptime(data_fine_str, "%Y-%m-%d").date()
            except ValueError:
                print("Formato data non valido!")
                continue
            
            # Genera il report
            report = db.genera_report_audit(
                tabella=tabella if tabella else None,
                operazione=operazione,
                data_inizio=data_inizio,
                data_fine=data_fine,
                utente=utente if utente else None
            )
            
            # Visualizza il report
            stampa_intestazione("REPORT DI AUDIT")
            print(report)
            
            # Salvataggio su file
            if input("\nSalvare su file? (s/n): ").lower() == 's':
                oggi = date.today().strftime("%Y%m%d")
                filename = f"report_audit_{oggi}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Report salvato nel file: {filename}")
        
        elif scelta == "4":
            break
        else:
            print("Opzione non valida!")
        
        input("\nPremi INVIO per continuare...")


def main():
    # Configura la connessione
    db_config = {
        "dbname": "catasto_storico",
        "user": "postgres",
        "password": "Markus74",  # Sostituisci con la tua password
        "host": "localhost",
        "port": 5432,
        "schema": "catasto"
    }
    
    # Inizializza il gestore
    db = CatastoDBManager(**db_config)
    
    # Verifica la connessione
    if not db.connect():
        print("ERRORE: Impossibile connettersi al database. Verifica i parametri.")
        sys.exit(1)
    
    try:
        # Esempi di operazioni
        menu_principale(db)
    except KeyboardInterrupt:
        print("\nOperazione interrotta dall'utente.")
    except Exception as e:
        print(f"ERRORE: {e}")
    finally:
        # Chiudi sempre la connessione
        db.disconnect()
        print("\nConnessione al database chiusa.")

if __name__ == "__main__":
    main()