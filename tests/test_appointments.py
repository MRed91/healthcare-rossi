from datetime import date, timedelta

from tests.conftest import next_weekday, past_weekday, slot_at


def prenota(client, headers, doctor_id, quando, **extra):
    return client.post("/api/appointments", headers=headers,
                       json={"doctor_id": doctor_id, "scheduled_at": quando, **extra})


def test_prenotazione_richiede_autenticazione(client, seed):
    res = prenota(client, {}, seed["cardiologo"], slot_at(next_weekday(), 10))
    assert res.status_code == 401


def test_paziente_prenota_per_se(client, patient_headers, seed):
    res = prenota(client, patient_headers, seed["cardiologo"], slot_at(next_weekday(), 10),
                  reason="Controllo pressione")
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "prenotata"
    assert body["patient"]["id"] == seed["mario"]
    assert body["doctor"]["last_name"] == "Bianchi"


def test_paziente_non_puo_prenotare_per_altri(client, patient_headers, seed):
    res = prenota(client, patient_headers, seed["cardiologo"], slot_at(next_weekday(), 10),
                  patient_id=seed["giulia"])
    assert res.status_code == 403


def test_amministratore_prenota_indicando_il_paziente(client, admin_headers, seed):
    res = prenota(client, admin_headers, seed["cardiologo"], slot_at(next_weekday(), 11),
                  patient_id=seed["giulia"])
    assert res.status_code == 201
    assert res.json()["patient"]["id"] == seed["giulia"]


def test_amministratore_deve_indicare_il_paziente(client, admin_headers, seed):
    res = prenota(client, admin_headers, seed["cardiologo"], slot_at(next_weekday(), 11))
    assert res.status_code == 422


def test_medico_inesistente(client, patient_headers):
    res = prenota(client, patient_headers, 999, slot_at(next_weekday(), 10))
    assert res.status_code == 404


def test_orario_gia_occupato(client, patient_headers, admin_headers, seed):
    quando = slot_at(next_weekday(), 10)
    assert prenota(client, patient_headers, seed["cardiologo"], quando).status_code == 201

    res = prenota(client, admin_headers, seed["cardiologo"], quando, patient_id=seed["giulia"])
    assert res.status_code == 409
    assert res.json()["detail"] == "Il medico ha già una prenotazione in questo orario"


def test_sovrapposizione_parziale_con_visita_esistente(client, patient_headers, admin_headers, seed):
    # visita da 30 minuti alle 10:00: le 10:30 sono libere, prima no
    assert prenota(client, patient_headers, seed["cardiologo"], slot_at(next_weekday(), 10)).status_code == 201
    res = prenota(client, admin_headers, seed["cardiologo"], slot_at(next_weekday(), 10, 30),
                  patient_id=seed["giulia"])
    assert res.status_code == 201


def test_paziente_con_due_visite_nello_stesso_orario(client, patient_headers, seed):
    quando = slot_at(next_weekday(), 10)
    assert prenota(client, patient_headers, seed["cardiologo"], quando).status_code == 201

    res = prenota(client, patient_headers, seed["generico"], quando)
    assert res.status_code == 409
    assert res.json()["detail"] == "Il paziente ha già una prenotazione in questo orario"


def test_prenotazione_fuori_orario(client, patient_headers, seed):
    assert prenota(client, patient_headers, seed["cardiologo"], slot_at(next_weekday(), 21)).status_code == 422
    assert prenota(client, patient_headers, seed["cardiologo"], slot_at(next_weekday(), 8)).status_code == 422


def test_prenotazione_non_allineata_agli_slot(client, patient_headers, seed):
    res = prenota(client, patient_headers, seed["cardiologo"], slot_at(next_weekday(), 10, 7))
    assert res.status_code == 422
    assert "slot" in res.json()["detail"]


def test_prenotazione_nel_fine_settimana(client, patient_headers, seed):
    sabato = date.today() + timedelta(days=1)
    while sabato.weekday() != 5:
        sabato += timedelta(days=1)
    res = prenota(client, patient_headers, seed["cardiologo"], slot_at(sabato, 10))
    assert res.status_code == 422
    assert "fine settimana" in res.json()["detail"]


def test_prenotazione_nel_passato(client, patient_headers, seed):
    res = prenota(client, patient_headers, seed["cardiologo"], slot_at(past_weekday(), 10))
    assert res.status_code == 422
    assert "passato" in res.json()["detail"]


def test_slot_occupato_sparisce_dalla_lista(client, patient_headers, seed):
    giorno = next_weekday().isoformat()
    prima = client.get(f"/api/doctors/{seed['cardiologo']}/slots?day={giorno}").json()

    assert prenota(client, patient_headers, seed["cardiologo"], prima[0]).status_code == 201

    dopo = client.get(f"/api/doctors/{seed['cardiologo']}/slots?day={giorno}").json()
    assert len(dopo) == len(prima) - 1
    assert prima[0] not in dopo


def test_paziente_vede_solo_le_proprie_prenotazioni(client, patient_headers, admin_headers, seed):
    prenota(client, patient_headers, seed["cardiologo"], slot_at(next_weekday(), 10))
    prenota(client, admin_headers, seed["cardiologo"], slot_at(next_weekday(), 11), patient_id=seed["giulia"])

    assert client.get("/api/appointments", headers=admin_headers).json()["total"] == 2

    proprie = client.get("/api/appointments", headers=patient_headers).json()
    assert proprie["total"] == 1
    assert proprie["items"][0]["patient"]["id"] == seed["mario"]


def test_filtro_agenda_per_giornata(client, admin_headers, booked, seed):
    oggi = next_weekday().isoformat()
    res = client.get(f"/api/appointments?day={oggi}", headers=admin_headers)
    assert res.json()["total"] == 1


def test_dettaglio_di_una_prenotazione_altrui(client, patient_headers, admin_headers, seed):
    altrui = prenota(client, admin_headers, seed["cardiologo"], slot_at(next_weekday(), 11),
                     patient_id=seed["giulia"]).json()
    res = client.get(f"/api/appointments/{altrui['id']}", headers=patient_headers)
    assert res.status_code == 403


def test_annullamento_da_parte_del_paziente(client, patient_headers, booked):
    res = client.post(f"/api/appointments/{booked['id']}/cancel", headers=patient_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "annullata"


def test_annullamento_libera_lo_slot(client, patient_headers, booked, seed):
    giorno = next_weekday().isoformat()
    occupati = client.get(f"/api/doctors/{seed['cardiologo']}/slots?day={giorno}").json()
    client.post(f"/api/appointments/{booked['id']}/cancel", headers=patient_headers)
    liberi = client.get(f"/api/doctors/{seed['cardiologo']}/slots?day={giorno}").json()
    assert len(liberi) == len(occupati) + 1


def test_doppio_annullamento(client, patient_headers, booked):
    client.post(f"/api/appointments/{booked['id']}/cancel", headers=patient_headers)
    res = client.post(f"/api/appointments/{booked['id']}/cancel", headers=patient_headers)
    assert res.status_code == 409


def test_completamento_riservato_allamministrazione(client, patient_headers, admin_headers, booked):
    assert client.post(f"/api/appointments/{booked['id']}/complete",
                       headers=patient_headers).status_code == 403
    res = client.post(f"/api/appointments/{booked['id']}/complete", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "completata"


def test_annullamento_di_una_visita_completata(client, admin_headers, patient_headers, booked):
    client.post(f"/api/appointments/{booked['id']}/complete", headers=admin_headers)
    res = client.post(f"/api/appointments/{booked['id']}/cancel", headers=patient_headers)
    assert res.status_code == 409


def test_prenotazione_inesistente(client, admin_headers):
    assert client.get("/api/appointments/999", headers=admin_headers).status_code == 404
