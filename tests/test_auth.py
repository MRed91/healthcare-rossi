from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, PATIENT_EMAIL, PATIENT_PASSWORD


def test_login_restituisce_un_token(client):
    res = client.post("/api/auth/login", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_con_password_errata(client):
    res = client.post("/api/auth/login", data={"username": PATIENT_EMAIL, "password": "sbagliata"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Email o password errati"


def test_login_con_email_inesistente(client):
    res = client.post("/api/auth/login", data={"username": "nessuno@test.it", "password": "qualsiasi"})
    assert res.status_code == 401


def test_profilo_utente_autenticato(client, patient_headers):
    res = client.get("/api/auth/me", headers=patient_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == PATIENT_EMAIL
    assert body["role"] == "patient"
    assert body["patient"]["last_name"] == "Verdi"


def test_profilo_amministratore_senza_anagrafica(client, admin_headers):
    res = client.get("/api/auth/me", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "admin"
    assert res.json()["patient"] is None


def test_profilo_senza_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_profilo_con_token_non_valido(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer token-inventato"})
    assert res.status_code == 401


def test_registrazione_crea_paziente_e_utente(client):
    res = client.post("/api/auth/register", json={
        "first_name": "Paola", "last_name": "Neri", "fiscal_code": "NREPLA88C50H501T",
        "email": "paola.neri@test.it", "birth_date": "1988-03-10", "password": "ProvaPw.88",
    })
    assert res.status_code == 201
    assert res.json()["patient"]["fiscal_code"] == "NREPLA88C50H501T"

    # la nuova utenza è subito operativa
    login = client.post("/api/auth/login", data={"username": "paola.neri@test.it", "password": "ProvaPw.88"})
    assert login.status_code == 200


def test_registrazione_con_email_gia_usata(client):
    res = client.post("/api/auth/register", json={
        "first_name": "Falso", "last_name": "Doppione", "fiscal_code": "DPPFLS80A01H501Q",
        "email": PATIENT_EMAIL, "birth_date": "1980-01-01", "password": "ProvaPw.80",
    })
    assert res.status_code == 409


def test_registrazione_con_password_troppo_corta(client):
    res = client.post("/api/auth/register", json={
        "first_name": "Corta", "last_name": "Password", "fiscal_code": "PSSCRT90A01H501B",
        "email": "corta@test.it", "birth_date": "1990-01-01", "password": "breve",
    })
    assert res.status_code == 422


def test_password_non_salvata_in_chiaro(client, db):
    from app.models import User

    utente = db.query(User).filter(User.email == PATIENT_EMAIL).first()
    assert utente.hashed_password != PATIENT_PASSWORD
    assert utente.hashed_password.startswith("$2b$")
