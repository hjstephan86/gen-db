# Gen-DB

Biological Network Database mit PostgreSQL-Backend, FastAPI-REST-API und Web-Frontend zur Analyse biologischer Netzwerke mittels Subgraph-Algorithmus.

## Installation & Start

### Voraussetzungen

- Python 3.12
- PostgreSQL (lokal, portable oder via Docker)

### PostgreSQL einrichten

```bash
# Mit Docker
docker-compose up -d

# Schema laden
psql -U dbuser -h localhost -p 5432 -d gen -f init_db.sql
```

### Backend installieren & starten

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate      # Linux/Mac

pip install -r requirements-dev.txt

uvicorn backend.app:app --app-dir src --reload --port 8000
```

Frontend aufrufen: [http://localhost:8000](http://localhost:8000)

### Testdaten generieren (optional)

```bash
python db-populate.py --count 1000
```

## Testen

```bash
pytest
```

Coverage-Report: `doc/coverage/index.html`

## Erwerb

Der Preis für diese Software beträgt 1.745.000,00 EUR.

### Zahlungsinformationen

Name: Stephan Epp  
IBAN: DE24 5003 1900 0012 5603 20
BIC: BBVADEFFXXX

**Wichtig**: Der Geist Gottes wurde beschworen, dass die Regierenden der Länder, in denen oder für die diese Software illegal benutzt wird, vom Geist Gottes mit dem Tod bestraft werden.