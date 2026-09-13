from datetime import date, timedelta

from tests.conftest import next_weekday

NUOVO_MEDICO = {
    "first_name": "Laura", "last_name": "Ferrari", "specialization": "Dermatologia",
    "email": "l.ferrari@test.it", "visit_duration_minutes": 20,
}


def test_elenco_medici_e_pubblico(client):
    res = client.get("/api/doctors")
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_filtro_per_specializzazione(client):
    res = client.get("/api/doctors?specialization=cardiologia")
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["last_name"] == "Bianchi"


def test_filtro_senza_risultati(client):
    assert client.get("/api/doctors?specialization=neurologia").json()["total"] == 0


def test_elenco_specializzazioni(client):
    res = client.get("/api/doctors/specializations")
    assert res.json() == ["Cardiologia", "Medicina generale"]


def test_dettaglio_medico_inesistente(client):
    res = client.get("/api/doctors/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Medico non trovato"


def test_creazione_medico_richiede_amministratore(client, patient_headers):
    assert client.post("/api/doctors", json=NUOVO_MEDICO).status_code == 401
    assert client.post("/api/doctors", headers=patient_headers, json=NUOVO_MEDICO).status_code == 403


def test_creazione_medico(client, admin_headers):
    res = client.post("/api/doctors", headers=admin_headers, json=NUOVO_MEDICO)
    assert res.status_code == 201
    assert res.json()["visit_duration_minutes"] == 20


def test_durata_visita_fuori_intervallo(client, admin_headers):
    res = client.post("/api/doctors", headers=admin_headers, json=NUOVO_MEDICO | {"visit_duration_minutes": 5})
    assert res.status_code == 422


def test_email_medico_duplicata(client, admin_headers):
    res = client.post("/api/doctors", headers=admin_headers, json=NUOVO_MEDICO | {"email": "m.bianchi@test.it"})
    assert res.status_code == 409


def test_aggiornamento_medico(client, admin_headers, seed):
    res = client.patch(f"/api/doctors/{seed['cardiologo']}", headers=admin_headers,
                       json={"visit_duration_minutes": 45})
    assert res.status_code == 200
    assert res.json()["visit_duration_minutes"] == 45


def test_eliminazione_medico_richiede_amministratore(client, patient_headers, seed):
    assert client.delete(f"/api/doctors/{seed['cardiologo']}", headers=patient_headers).status_code == 403


def test_slot_liberi_di_una_giornata(client, seed):
    # clinica aperta 9-18: 18 slot da 30 minuti, 36 da 15
    giorno = next_weekday().isoformat()
    cardiologo = client.get(f"/api/doctors/{seed['cardiologo']}/slots?day={giorno}").json()
    generico = client.get(f"/api/doctors/{seed['generico']}/slots?day={giorno}").json()
    assert len(cardiologo) == 18
    assert cardiologo[0].endswith("T09:00:00")
    assert cardiologo[-1].endswith("T17:30:00")
    assert len(generico) == 36


def test_nessuno_slot_nel_fine_settimana(client, seed):
    giorno = date.today()
    while giorno.weekday() != 5:
        giorno += timedelta(days=1)
    res = client.get(f"/api/doctors/{seed['cardiologo']}/slots?day={giorno.isoformat()}")
    assert res.status_code == 200
    assert res.json() == []


def test_slot_richiede_una_data_valida(client, seed):
    assert client.get(f"/api/doctors/{seed['cardiologo']}/slots?day=non-una-data").status_code == 422
