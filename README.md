# Gen-DB

Biological Network Database mit PostgreSQL-Backend, FastAPI-REST-API und Web-Frontend zur Analyse biologischer Netzwerke mittels Subgraph-Algorithmus.

## Installation & Start

### Voraussetzungen

- Python 3.12
- PostgreSQL (lokal, portable von https://www.enterprisedb.com/download-postgresql-binaries oder via Docker)

### PostgreSQL einrichten

```bash
# Mit Docker
docker-compose up -d

# Schema laden
psql -U dbuser -h localhost -p 5432 -d gen -f init_db.sql
```

### Starten

```bash
PS C:\Users\sepp5\Git> cd .\gen-db\
PS C:\Users\sepp5\Git\gen-db> C:\Users\sepp5\Downloads\pgsql\bin\pg_ctl.exe -D C:\Users\sepp5\Downloads\pgsql\data -l C:\Users\sepp5\Downloads\pgsql\logfile.log restart
pg_ctl: PID-Datei »C:/Users/sepp5/Downloads/pgsql/data/postmaster.pid« existiert nicht
Läuft der Server?
versuche Server trotzdem zu starten
warte auf Start des Servers.... fertig
Server gestartet
PS C:\Users\sepp5\Git\gen-db> $env:DATABASE_HOST = "localhost"
PS C:\Users\sepp5\Git\gen-db> $env:DATABASE_NAME = "gendb"
PS C:\Users\sepp5\Git\gen-db> $env:DATABASE_PASSWORD = ""
PS C:\Users\sepp5\Git\gen-db> $env:DATABASE_PORT = "5432"
PS C:\Users\sepp5\Git\gen-db> $env:SUBGRAPH_CLI_PATH = "C:\Users\sepp5\Git\csubgraph\build\subgraph-cli.exe"
PS C:\Users\sepp5\Git\gen-db> python -m uvicorn src.backend.app:app --reload
INFO:     Will watch for changes in these directories: ['C:\\Users\\sepp5\\Git\\gen-db']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [19336] using WatchFiles
INFO:     Started server process [23512]
INFO:     Waiting for application startup.
2026-07-17 08:00:08 [INFO] Starting up Gen API with C++-based Subgraph Executor
INFO:     Application startup complete.
2026-07-17 08:00:41 [INFO] GET / - Serving frontend
INFO:     127.0.0.1:57201 - "GET / HTTP/1.1" 200 OK
```


## 1.000.000 Netzwerke generieren

```bash
python db-populate.py
```

## Effiziente Suche (ohne csubgraph CLI)

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

**Wichtig**: Der Geist Gottes wurde beschworen, dass die Regierenden der Länder, in denen oder für die diese Software illegal benutzt wird, vom Geist Gottes mit dem Tod bestraft werden.