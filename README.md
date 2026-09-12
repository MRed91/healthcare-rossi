# Healthcare API — Prenotazione visite mediche

Project Work per il CdS *Informatica per le Aziende Digitali* (L-31), Università Telematica Pegaso.

**Traccia PW 16** — Sviluppo di una applicazione full-stack API-based per un'organizzazione del settore sanitario.

## Il progetto

Applicazione full-stack per la gestione delle prenotazioni di visite mediche del **Centro Medico Aurora**, una clinica privata (caso di studio). Il sistema espone un backend REST sviluppato con **FastAPI** e un frontend in **HTML/CSS/JavaScript** per pazienti e amministrazione.

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

# 3. Popolare il database con dati di esempio (opzionale)
python -m app.seed

# 4. Avviare il server di sviluppo
uvicorn app.main:app --reload
```

L'applicazione è raggiungibile su `http://127.0.0.1:8000`:

- `http://127.0.0.1:8000/` — frontend (landing page)
- `http://127.0.0.1:8000/health` — health check
- `http://127.0.0.1:8000/api/auth` — registrazione, login JWT e profilo
- `http://127.0.0.1:8000/api/patients` — API pazienti (solo amministrazione)
- `http://127.0.0.1:8000/api/doctors` — API medici, con orari liberi su `/{id}/slots`
- `http://127.0.0.1:8000/api/appointments` — API prenotazioni
- `http://127.0.0.1:8000/docs` — documentazione Swagger UI
- `http://127.0.0.1:8000/redoc` — documentazione ReDoc

Lo script di seed crea due utenze di prova: `admin@centromedicorossi.it` / `admin123!` (amministrazione) e `mario.verdi@example.com` / `paziente123!` (paziente).

## Test

La suite automatica usa pytest e il TestClient di FastAPI, con un database SQLite di prova
ricreato prima di ogni test e rimosso al termine: i dati di sviluppo non vengono mai toccati.

```bash
pip install -r requirements-dev.txt
python -m pytest tests -v
```

## Struttura del progetto

```
healthcare-api/
├── app/
│   ├── core/          # Configurazione dell'applicazione
│   ├── routers/       # Endpoint REST (auth, pazienti, medici, prenotazioni)
│   ├── database.py    # Engine, sessione e base ORM
│   ├── models.py      # Modelli SQLAlchemy (Patient, Doctor, Appointment, User)
│   ├── schemas.py     # Schemi Pydantic di input/output
│   ├── scheduling.py  # Regole di agenda: orari, conflitti, slot liberi
│   ├── security.py    # Hashing password, token JWT e controlli di ruolo
│   ├── seed.py        # Popolamento del database con dati di esempio
│   └── main.py        # Entry point e factory FastAPI
├── docs/              # Documentazione di progetto (diagramma ER)
├── tests/             # Test automatici (pytest + TestClient)
├── frontend/
│   ├── css/           # Fogli di stile
│   ├── js/            # Script client (sessione, chiamate alle API, logica pagine)
│   └── *.html         # Home, medici, prenotazione, login, area personale, admin
└── Rrequirements.txt   # Dipendenze Python
```
