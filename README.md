# Smart-Maintenance-Inventory-Manager

## Obiectivele acestui proiect sunt:
* Autentificare securizată pe 3 roluri (Admin, Tehnician, Gestionar).
* Evidență CRUD echipamente și scădere automată din stoc.
* Alerte automate pentru stoc minim și mentenanțe scadente.
* Timp de răspuns API < 200ms și acoperire teste > 70%.

## Pornire locală cu Docker

Din acest director, cu Docker Desktop pornit (Linux containers):

```powershell
Copy-Item .env.example .env
docker compose up --build --detach --wait
```

API: http://localhost:8000 · Swagger: http://localhost:8000/docs.
Oprire: `docker compose down` (datele rămân în volumul Docker).

Proiectul conține momentan scheletul FastAPI și modelele SQLite; funcțiile de
autentificare, mentenanță și stocuri sunt în dezvoltare. Frontend-ul nu este încă
implementat. Obiectivele de mai sus sunt ținte, nu rezultate deja demonstrate.

## Organizare

- `backend/`: API și teste operaționale — rolul 1 / QA.
- `frontend/`: spațiu pentru interfață — rolul 2.
- `docs/devops.md`: configurare, CI/CD, backup, rollback și pașii managerului — rolul 3.
- `.github/`: CI, publicare imagini GHCR, actualizări dependențe și șabloane QA.

Instrucțiuni complete în [ghidul DevOps](docs/devops.md).
Rezultate locale în [raportul de verificare](docs/devops-validation.md).
