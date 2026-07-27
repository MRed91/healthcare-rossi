# Diagramma ER

Modello dati del sistema di prenotazione visite del Centro Medico Rossi.

Un paziente può avere più prenotazioni, un medico riceve più prenotazioni: la tabella `appointments` realizza la relazione molti-a-molti tra pazienti e medici, arricchita dagli attributi propri della prenotazione (data/ora, motivo, stato).

```mermaid
erDiagram
    PATIENT ||--o{ APPOINTMENT : "prenota"
    DOCTOR ||--o{ APPOINTMENT : "riceve"

    PATIENT {
        int id PK
        string first_name
        string last_name
        string fiscal_code UK
        string email UK
        string phone
        date birth_date
    }

    DOCTOR {
        int id PK
        string first_name
        string last_name
        string specialization
        string email UK
        string phone
        int visit_duration_minutes
    }

    APPOINTMENT {
        int id PK
        int patient_id FK
        int doctor_id FK
        datetime scheduled_at
        string reason
        string status
        datetime created_at
    }
```

Lo stato della prenotazione (`status`) è un enumerato con valori: `prenotata`, `annullata`, `completata`.

La durata della visita non è salvata sulla singola prenotazione ma dipende dal medico (`visit_duration_minutes`): servirà per il calcolo degli slot disponibili e il controllo delle sovrapposizioni.
