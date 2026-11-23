# Vigilact: engineering an observable contract protocol

**Progetto open source sperimentale · Python, Go, HTTP/JSON · Apache-2.0**

Un sistema software può comunicare ciò che è accaduto, ma spesso è altrettanto importante sapere **cosa avrebbe dovuto accadere**. Vigilact esplora un modello semplice: un'applicazione propone un contratto operativo, un observer ne accetta le condizioni, raccoglie evidenze e produce un esito verificabile.

Il progetto nasce come ricerca applicata su interoperabilità, progettazione di API, gestione delle scadenze e resilienza dei sistemi distribuiti. Non è un servizio di notifiche: emette eventi neutri che un software esterno può utilizzare per audit, diagnostica, integrazioni o notifiche.

## Cosa ho realizzato

La prima implementazione di riferimento è in **Python/FastAPI con SQLite**. Una seconda implementazione indipendente del solo profilo Core, scritta in **Go**, permette di testare il comportamento esterno del protocollo senza riutilizzare il codice Python.

Nella versione sperimentale `v0.4.0a2` ho concentrato gli sprint sulla qualità delle evidenze:

- la medesima suite di 22 verifiche HTTP/restart viene applicata ai due observer;
- 12 scenari generati da un seed verificano isolamento fra agent, replay e corrispondenza degli esiti;
- un report JSON confronta l'hash di una traccia normalizzata dei comportamenti;
- test di *fault injection* verificano l'atomicità tra stato del contratto, ricezione delle evidenze ed eventi di valutazione;
- test Python, controlli Go, esempi e documentazione sono riproducibili localmente.

## Cosa dimostrano, e cosa no

Le prove dimostrano conformità **parziale e circoscritta** al profilo `core.expected_event/0.1`. Non dimostrano correttezza per tutti gli input, sicurezza in produzione, alta disponibilità o compatibilità completa fra tutti i componenti. Le funzioni di comando remoto dell'implementazione Python non appartengono al profilo Core condiviso.

Una lezione importante del progetto è distinguere **assenza di evidenza** da **prova di un fallimento**: un job non osservato entro il termine potrebbe essere stato eseguito senza riuscire a comunicarlo. Vigilact esplicita questa limitazione nella semantica del protocollo.

## Perché lo sviluppo come open source

L'interoperabilità va dimostrata, non dichiarata. Pubblicare specifiche, implementazioni diverse, scenari falsificabili e limiti noti rende possibile una revisione tecnica esterna. È anche un modo concreto per documentare il mio lavoro su software architecture, distributed systems e backend engineering.

**Repository:** `atellaluca/vigilact` (inserire link quando pubblicato)  
**Documentazione prevista:** `vigilact.atellaluca.com` (attivare soltanto dopo verifica DNS e GitHub Pages)  
**Licenza:** Apache-2.0 · **Stato:** alpha sperimentale, non production-ready.
