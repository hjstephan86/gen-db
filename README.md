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

## 1.000.000 Netzwerke generieren

```bash
python db-populate.py
```

## Effiziente Suche

```bash
(venv) PS C:\Users\sepp5\Git\gen-db> uvicorn backend.app:app --app-dir src --reload --port 8000
INFO:     Will watch for changes in these directories: ['C:\\Users\\sepp5\\Git\\gen-db']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [11520] using WatchFiles
INFO:     Started server process [20388]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
2026-06-24 07:40:50 [INFO] GET /api/networks limit=33 random=True
2026-06-24 07:40:50 [INFO] get_all_networks: limit=33 random_sample=True
2026-06-24 07:40:51 [INFO] get_all_networks: Fetched 33 records
2026-06-24 07:40:51 [INFO] GET /api/networks - Returned 33 networks
INFO:     127.0.0.1:64651 - "GET /api/networks?limit=33&random=true HTTP/1.1" 200 OK
2026-06-24 07:40:59 [INFO] GET /api/networks limit=33 random=True
2026-06-24 07:40:59 [INFO] get_all_networks: limit=33 random_sample=True
2026-06-24 07:41:01 [INFO] get_all_networks: Fetched 33 records
2026-06-24 07:41:01 [INFO] GET /api/networks - Returned 33 networks
INFO:     127.0.0.1:49775 - "GET /api/networks?limit=33&random=true HTTP/1.1" 200 OK
2026-06-24 07:42:46 [INFO] GET /api/networks/820154
2026-06-24 07:42:46 [INFO] get_network_by_id: network_id=820154
2026-06-24 07:42:47 [INFO] get_network_by_id: Found network 'metabolic_C._elegans_820154'
2026-06-24 07:42:47 [INFO] GET /api/networks/820154 - Found: metabolic_C._elegans_820154
INFO:     127.0.0.1:51144 - "GET /api/networks/820154 HTTP/1.1" 200 OK
2026-06-24 07:43:04 [INFO] POST /api/networks/search - nodes=15
2026-06-24 07:43:27 [INFO] search_subgraph: 306261 candidates for query (n=15, e=62)
2026-06-24 07:47:31 [INFO] search_subgraph: Found 306260 matches
2026-06-24 07:47:31 [INFO] POST /api/networks/search - Found 306260 matches
INFO:     127.0.0.1:52597 - "POST /api/networks/search HTTP/1.1" 200 OK
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
