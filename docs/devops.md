# Ghid DevOps — rolul 3

## Domeniu și stadiu

Mediul de demonstrație ales este local, cu Docker Compose și SQLite persistent.
Backend-ul existent este FastAPI. Rutele de autentificare, echipamente, stocuri și
tichete nu sunt încă implementate. Frontend-ul este rezervat rolului 2.
Acest livrabil pregătește rularea, verificarea și distribuirea backend-ului.
Nu reprezintă validarea funcționalităților aplicației sau o lansare în producție.

## Pornire și operare

Din rădăcina depozitului, cu Docker Desktop pornit în modul Linux containers:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up --build --detach --wait
docker compose ps
curl.exe --fail http://localhost:8000/health/ready
docker compose logs --tail 100 backend
docker compose down
```

Swagger: http://localhost:8000/docs. Portul se poate schimba prin `API_PORT` în
`.env`. Pentru alt frontend, configurați `CORS_ORIGINS` cu origini separate prin
virgulă, fără slash final. După schimbarea `.env`, rulați din nou `compose up`.
Portul API este legat de 127.0.0.1 pentru demonstrația pe calculatorul local.

`/health/live` verifică procesul; `/health/ready` verifică și conexiunea SQL,
returnând HTTP 503 fără detalii interne dacă baza nu este disponibilă.
Docker folosește readiness pentru starea healthy. Politica de restart repornește
un proces care se închide; simpla stare unhealthy nu declanșează un restart.

Volumul `smartmim-data` păstrează `/data/smartmim.db` după recrearea containerului.
Fișierul SQLite existent din repository nu este copiat în imagine sau volum.
La prima pornire se creează o bază goală. Nu rulați `docker compose down --volumes`
pe mediul cu date de păstrat: comanda șterge volumul.

## Backup și restaurare

Backup consistent folosind API-ul SQLite, cu backend pornit (PowerShell):

```powershell
New-Item -ItemType Directory -Force backups
$backupName = "smartmim-$(Get-Date -Format yyyyMMdd-HHmmss).db"
docker compose exec -T backend python -c "import sqlite3; source=sqlite3.connect('/data/smartmim.db'); target=sqlite3.connect('/tmp/backup.db'); source.backup(target); target.close(); source.close()"
docker compose cp backend:/tmp/backup.db "backups/$backupName"
```

Păstrați copii și în afara calculatorului. Verificați restaurarea înainte de o
demonstrație importantă. Pentru restaurare, opriți backend-ul și înlocuiți baza
din volum printr-un container temporar cu aceeași imagine și același utilizator:

```powershell
# Alegeți explicit fișierul de restaurat și faceți întâi backup la datele curente.
docker compose stop backend
docker compose run --rm --no-deps -v "${PWD}/backups:/backups:ro" backend python -c "import sqlite3; source=sqlite3.connect('file:/backups/NUME-BACKUP.db?mode=ro', uri=True); target=sqlite3.connect('/data/smartmim.db'); source.backup(target); target.close(); source.close()"
docker compose up --detach --wait
```

Înlocuiți `NUME-BACKUP.db` cu numele copiei. Nu restaurați peste o bază folosită
de procese active. Copiile pot conține date personale și nu se comit în Git.

## Integrare și livrare

La fiecare pull request și push pe `main`, CI execută instalarea dependențelor
fixate, `pip check`, lint pentru erori Python, pytest cu prag 70% și raport XML.
Un job separat construiește imaginea, așteaptă starea healthy, verifică API-ul și
persistența volumului după recreare. Volumele sunt șterse doar pe runnerul efemer.

După un CI reușit pentru un push pe `main`, workflow-ul Publish container
construiește exact commit-ul verificat și publică în:

`ghcr.io/smart-maintenance/smart-maintenance-inventory-manager/backend:sha-<SHA_COMPLET>`

Se folosește `GITHUB_TOKEN` cu `packages: write`, fără parolă personală în cod.
Publicarea unei imagini este livrare continuă; pornirea ei local rămâne explicită.
Nu există deploy automat pe un server extern. Pentru a rula o imagine publicată:

```powershell
# Înlocuiți SHA_COMPLET. Pentru pachet privat, autentificați-vă întâi în GHCR.
docker pull ghcr.io/smart-maintenance/smart-maintenance-inventory-manager/backend:sha-SHA_COMPLET
docker tag ghcr.io/smart-maintenance/smart-maintenance-inventory-manager/backend:sha-SHA_COMPLET smartmim-backend:local
docker compose up --detach --no-build --wait
```

Pentru rollback, repetați cu SHA-ul anterior. Dacă schema bazei s-a schimbat,
rollback-ul imaginii poate necesita și restaurarea unei copii compatibile.

## Configurare GitHub de către manager

Fișierele sunt pregătite local; setările de mai jos trebuie aplicate în GitHub:

1. Deschideți PR către `main`, după commit și push pe o ramură de lucru.
2. În Settings → Rules → Rulesets, protejați `main`: PR obligatoriu, cel puțin o
   aprobare de la un coleg, verificări `Backend tests` și `Docker smoke test`,
   blocare force push și ștergere. Selectați verificările după prima rulare CI.
3. Confirmați că GitHub Actions este activat și politica organizației permite
   publicarea pachetelor cu `GITHUB_TOKEN`. Vizibilitatea pachetului se setează
   separat în GHCR; nu presupuneți că este public.
4. Folosiți issue-uri pentru bug-uri și PR-uri pentru schimbări. Rolul 1 revizuiește
   schimbările backend, rolul 2 frontend, iar rolul 3 configurația și testele.

Nu sunt configurate automat reguli GitHub și nu este efectuat push din acest livrabil.

## Dependențe și verificare locală

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest
```

`requirements.txt` și `requirements-dev.in` definesc dependențele; fișierele `.lock`
fixează inclusiv dependențele tranzitive. Regenerați ambele cu pip-tools, revizuiți
diferențele și rulați CI înainte de integrare. Mediul Docker/CI este Python 3.12;
verificarea locală poate folosi Python 3.10+.

```powershell
.\.venv\Scripts\python.exe -m pip install pip-tools
.\.venv\Scripts\pip-compile.exe --no-emit-trusted-host --output-file backend/requirements.lock backend/requirements.txt
.\.venv\Scripts\pip-compile.exe --no-emit-trusted-host --output-file backend/requirements-dev.lock backend/requirements-dev.in
```

## Limite și responsabilități următoare

- Pragul de acoperire se aplică surselor existente; nu demonstrează cerințele încă
  neimplementate. Testele actuale verifică infrastructura și schema inițială.
- Backend: autentificare/RBAC, tranzacții pentru stoc, migrații versionate înainte
  de modificarea unei baze cu date. `create_all` creează tabele, nu migrează coloane.
- QA: teste funcționale pe roluri, integrare consum/alerte și măsurători pentru
  50 de utilizatori și obiectivul API sub 200 ms după implementarea rutelor.
- `passlib[bcrypt]` provine din scheletul existent; compatibilitatea hashingului
  trebuie testată și dependențele revizuite când se implementează autentificarea.
- Baza `backend/smartmim.db` este deja urmărită de Git. `.gitignore` împiedică
  adăugarea altor baze, dar nu o elimină din istoric; echipa decide eliminarea ei
  și verifică să nu conțină date sensibile înainte de publicare.
- Pentru producție sunt necesare decizii separate: HTTPS, secrete, migrații,
  monitorizare externă, backup automat și eventual PostgreSQL.

Referințe: [Docker Compose](https://docs.docker.com/compose/gettingstarted/),
[publicarea imaginilor cu GitHub Actions](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images).
