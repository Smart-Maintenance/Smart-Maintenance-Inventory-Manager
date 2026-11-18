# Raport de verificare DevOps — 17 noiembrie 2026

## Rezultate locale

| Verificare | Rezultat |
| --- | --- |
| Windows, Python 3.10.11, pytest | 6 teste trecute |
| Linux în container, Python 3.12.16, pytest | 6 teste trecute |
| Acoperire surse existente | 100%, prag configurat 70% |
| `pip check`, Windows și Linux | Fără dependențe incompatibile |
| Ruff, Windows și Linux | Trecut |
| `docker compose config --quiet` | Valid |
| Build Docker și startup Compose | Trecut, backend healthy |
| `/health/ready` | HTTP 200, `status=ready` |
| Utilizator container | UID 10001, fără root |
| Persistență SQLite | Valoare de test păstrată după `down` și `up`; tabela temporară eliminată |
| Backup și restaurare SQLite | Copii temporare verificate prin `integrity_check` și prezența celor 6 tabele |
| `git diff --check` | Fără erori de whitespace |

La finalul verificării, serviciul backend este pornit pe
http://localhost:8000/docs, cu port legat de 127.0.0.1.

## Observații

- Acoperirea include modelele și infrastructura încărcată de teste. Nu constituie
  validarea funcțiilor de autentificare, consum piese sau notificări: rutele sunt
  încă goale. Obiectivele de performanță și concurență nu au fost măsurate.
- Starlette emite un avertisment de depreciere pentru TestClient cu `httpx`;
  testele trec cu versiunile fixate. Migrarea la clientul recomandat trebuie
  evaluată la următoarea actualizare a dependențelor.
- Testele Windows au necesitat acces în afara sandbox-ului pentru socket-ul local
  asyncio. Rularea Linux s-a făcut într-un director intern containerului deoarece
  scrierea SQLite folosită de coverage pe bind mount Windows a dat o eroare I/O.
  CI folosește un filesystem Linux nativ.
- Workflow-urile GitHub sunt pregătite în fișiere, dar nu au fost executate pe
  GitHub. Nu s-au făcut commit, push, publicare GHCR sau modificări de ruleset.
- Fișierul `backend/smartmim.db` urmărit anterior de Git nu a fost modificat de
  teste. Mediul Docker folosește o bază separată, în volumul propriu.
