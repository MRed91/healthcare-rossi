from tests.conftest import next_weekday, slot_at


def test_statistiche_riservate_allamministrazione(client, patient_headers):
    assert client.get("/api/stats").status_code == 401
    assert client.get("/api/stats", headers=patient_headers).status_code == 403


def test_indicatori_su_database_popolato(client, admin_headers, booked):
    body = client.get("/api/stats", headers=admin_headers).json()
    assert body["total_patients"] == 2
    assert body["active_appointments"] == 1
    assert body["completed_appointments"] == 1
    assert body["cancelled_appointments"] == 0


def test_annullamento_aggiorna_gli_indicatori(client, admin_headers, patient_headers, booked):
    client.post(f"/api/appointments/{booked['id']}/cancel", headers=patient_headers)
    body = client.get("/api/stats", headers=admin_headers).json()
    assert body["active_appointments"] == 0
    assert body["cancelled_appointments"] == 1


def test_previsione_sui_prossimi_sette_giorni(client, admin_headers, booked):
    body = client.get("/api/stats", headers=admin_headers).json()
    assert len(body["next_days"]) == 7

    giorno = next_weekday().isoformat()
    atteso = next(d for d in body["next_days"] if d["day"] == giorno)
    assert atteso["count"] == 1


def test_visite_per_medico_escludono_le_annullate(client, admin_headers, patient_headers, booked, seed):
    per_medico = client.get("/api/stats", headers=admin_headers).json()["per_doctor"]
    assert per_medico[0]["doctor"] == "Bianchi Marco"
    assert per_medico[0]["count"] == 2

    client.post(f"/api/appointments/{booked['id']}/cancel", headers=patient_headers)
    per_medico = client.get("/api/stats", headers=admin_headers).json()["per_doctor"]
    assert per_medico[0]["count"] == 1


def test_statistiche_su_database_vuoto(client, admin_headers):
    body = client.get("/api/stats", headers=admin_headers).json()
    assert body["active_appointments"] == 0
    assert body["per_doctor"] == []
    assert sum(giorno["count"] for giorno in body["next_days"]) == 0
