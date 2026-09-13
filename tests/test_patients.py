NUOVO_PAZIENTE = {
    "first_name": "Anna", "last_name": "Colombo", "fiscal_code": "CLMNNA92H47F205Y",
    "email": "anna.colombo@test.it", "birth_date": "1992-06-07",
}


def test_elenco_pazienti_senza_token(client):
    assert client.get("/api/patients").status_code == 401


def test_elenco_pazienti_con_ruolo_paziente(client, patient_headers):
    res = client.get("/api/patients", headers=patient_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Operazione riservata all'amministrazione"


def test_elenco_pazienti_da_amministratore(client, admin_headers):
    res = client.get("/api/patients", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert {item["last_name"] for item in body["items"]} == {"Verdi", "Bianco"}


def test_paginazione(client, admin_headers):
    res = client.get("/api/patients?page=1&size=1", headers=admin_headers)
    body = res.json()
    assert body["total"] == 2 and body["size"] == 1
    assert len(body["items"]) == 1


def test_ricerca_per_cognome(client, admin_headers):
    res = client.get("/api/patients?q=verdi", headers=admin_headers)
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["first_name"] == "Mario"


def test_creazione_paziente(client, admin_headers):
    res = client.post("/api/patients", headers=admin_headers, json=NUOVO_PAZIENTE)
    assert res.status_code == 201
    assert res.json()["id"]


def test_codice_fiscale_normalizzato_in_maiuscolo(client, admin_headers):
    dati = NUOVO_PAZIENTE | {"fiscal_code": "clmnna92h47f205y"}
    res = client.post("/api/patients", headers=admin_headers, json=dati)
    assert res.status_code == 201
    assert res.json()["fiscal_code"] == "CLMNNA92H47F205Y"


def test_codice_fiscale_non_valido(client, admin_headers):
    res = client.post("/api/patients", headers=admin_headers, json=NUOVO_PAZIENTE | {"fiscal_code": "ABC123"})
    assert res.status_code == 422


def test_email_non_valida(client, admin_headers):
    res = client.post("/api/patients", headers=admin_headers, json=NUOVO_PAZIENTE | {"email": "non-una-email"})
    assert res.status_code == 422


def test_codice_fiscale_duplicato(client, admin_headers):
    dati = NUOVO_PAZIENTE | {"fiscal_code": "VRDMRA85M01H501Z"}
    res = client.post("/api/patients", headers=admin_headers, json=dati)
    assert res.status_code == 409
    assert "codice fiscale" in res.json()["detail"]


def test_email_duplicata(client, admin_headers):
    res = client.post("/api/patients", headers=admin_headers, json=NUOVO_PAZIENTE | {"email": "mario.verdi@test.it"})
    assert res.status_code == 409


def test_dettaglio_paziente_inesistente(client, admin_headers):
    res = client.get("/api/patients/999", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "Paziente non trovato"


def test_aggiornamento_parziale(client, admin_headers, seed):
    res = client.patch(f"/api/patients/{seed['mario']}", headers=admin_headers, json={"phone": "3339998877"})
    assert res.status_code == 200
    body = res.json()
    assert body["phone"] == "3339998877"
    assert body["last_name"] == "Verdi"


def test_aggiornamento_con_email_di_un_altro_paziente(client, admin_headers, seed):
    res = client.patch(f"/api/patients/{seed['mario']}", headers=admin_headers,
                       json={"email": "giulia.bianco@test.it"})
    assert res.status_code == 409


def test_aggiornamento_mantiene_la_propria_email(client, admin_headers, seed):
    res = client.patch(f"/api/patients/{seed['mario']}", headers=admin_headers,
                       json={"email": "mario.verdi@test.it"})
    assert res.status_code == 200


def test_eliminazione(client, admin_headers, seed):
    assert client.delete(f"/api/patients/{seed['giulia']}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/patients/{seed['giulia']}", headers=admin_headers).status_code == 404
