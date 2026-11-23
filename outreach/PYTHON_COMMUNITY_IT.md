# Community Python: versione italiana

Sto sperimentando un protocollo open source per **contratti operativi osservabili**, con un server Python/FastAPI e un secondo observer Go indipendente. L'idea è piccola e precisa: un agent dichiara un evento atteso entro una scadenza; il server registra se l'evidenza corrispondente è arrivata in tempo.

Mi interessava verificare la semantica senza limitarmi a testare l'SDK Python:

- **22 controlli HTTP/restart** per ciascuno dei due observer;
- **12 scenari differenziali** riproducibili con due agent, replay e isolamento delle identità;
- hash identico delle osservazioni normalizzate Python/Go;
- fault injection sulle transazioni SQLite, per verificare rollback e singolo evento terminale.

La suite Python locale supera **62 test**. Non è un protocollo stabile, né un server production-ready: il profilo condiviso copre solo eventi one-shot attesi.

La domanda su cui mi piacerebbe confrontarmi è: **quali altri casi limite o errori temporali dovrei introdurre nella suite prima di evolvere la specifica?**

Repository e docs: **[inserire URL dopo la pubblicazione]**.
