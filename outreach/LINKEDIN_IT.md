# Bozza per LinkedIn (italiano)

Sto lavorando a **Vigilact**, un progetto open source sperimentale che nasce da una domanda: *come possiamo descrivere ciò che un sistema dovrebbe fare, e verificare in modo interoperabile se abbiamo ricevuto le evidenze attese?*

L'idea non è sviluppare l'ennesimo sistema di notifiche. Vigilact prova a definire un protocollo per **contratti operativi osservabili**: un agent propone un impegno, un observer accetta le condizioni supportate e registra l'esito in base alle evidenze ricevute.

Negli ultimi sprint mi sono concentrato su prove riproducibili, non sulle feature:

- Due observer HTTP indipendenti, **Python/FastAPI + SQLite** e **Go**.
- **22 verifiche HTTP e di recovery per implementazione** sullo stesso profilo Core sperimentale.
- **12 scenari differenziali con due agent**, e risultati normalizzati identici fra i server.
- **Fault injection** sulle transazioni: una scrittura fallita non lascia contratto, evidenza e outbox in uno stato parzialmente aggiornato.
- **62 test Python superati** in locale, prima della pubblicazione.

Per chiarezza: non è uno standard stabile né un servizio pronto per la produzione. Il profilo interoperabile è volutamente limitato agli eventi attesi (*one-shot expected events*).

La parte interessante, per me, è la progettazione delle **garanzie**: cosa possiamo affermare quando un evento non arriva? Come gestiamo replay, identità e fallimenti senza affermare cose che non sappiamo?

Il progetto verrà pubblicato come **`atellaluca/vigilact`** sotto licenza Apache-2.0, con specifica e documentazione. Mi piacerebbe ricevere feedback soprattutto sui limiti del modello e sui test di conformità.

[Inserire qui il link GitHub solo dopo la pubblicazione]

#Python #OpenSource #DistributedSystems #SoftwareArchitecture #BackendEngineering

---

**Nota prima di pubblicare:** se il numero dei test cambia in CI, aggiornare le metriche nel post con quelle effettivamente verificate sulla release pubblica. Non pubblicare l'URL della documentazione finché non è online.
