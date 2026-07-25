# Healthcare API — Prenotazione visite mediche

Project Work per il CdS *Informatica per le Aziende Digitali* (L-31), Università Telematica Pegaso.

**Traccia PW 16** — Sviluppo di una applicazione full-stack API-based per un'organizzazione del settore sanitario.

## Il progetto

Applicazione full-stack per la gestione delle prenotazioni di visite mediche del **Centro Medico Aurora**, una clinica privata (caso di studio). Il sistema espone un backend REST sviluppato con **FastAPI** e un frontend in **HTML/CSS/JavaScript** per pazienti e amministrazione.

Lo sviluppo procede per fasi incrementali, documentate in [ROADMAP.md](ROADMAP.md).

## Stack tecnologico

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Documentazione API:** OpenAPI/Swagger generata automaticamente

## Avvio in locale

```bash
# 1. Creare e attivare l'ambiente virtuale
python3 -m venv .venv
source .venv/bin/activate

# 2. Installare le dipendenze
pip install -r requirements.txt

# 3. Avviare il server di sviluppo
uvicorn app.main:app --reload
```

L'applicazione è raggiungibile su `http://127.0.0.1:8000`:

- `http://127.0.0.1:8000/` — frontend (landing page)
- `http://127.0.0.1:8000/health` — health check
- `http://127.0.0.1:8000/docs` — documentazione Swagger UI
- `http://127.0.0.1:8000/redoc` — documentazione ReDoc

## Struttura del progetto

```
healthcare-api/
├── app/
│   ├── core/          # Configurazione dell'applicazione
│   └── main.py        # Entry point e factory FastAPI
├── frontend/
│   ├── css/           # Fogli di stile
│   ├── js/            # Script client (chiamate alle API)
│   └── index.html     # Landing page
├── requirements.txt   # Dipendenze Python
└── ROADMAP.md         # Fasi di sviluppo del progetto
```
