# Teste API după integrarea rutelor

Verificare la 17 noiembrie 2026, Linux/Python 3.12.16 cu dependențele fixate din CI:
**41 teste trecute, 1 xfailed (QA-001), acoperire 100% pentru instrucțiuni și
ramurile existente**. `pip check` și Ruff trec. Pragul de 70% nu a fost modificat.
Există avertismente de depreciere pentru TestClient/httpx și `datetime.utcnow`;
acestea nu provoacă eșecul suitei. Workflow-ul GitHub trebuie rerulat după push.

Testele din `backend/tests/` folosesc exclusiv o bază SQLite temporară.
Schema este recreată înainte de fiecare scenariu API; tehnicianul de test este
inserat explicit, deoarece autentificarea nu este încă implementată.

## Scenarii acoperite

- Echipamente: creare, listare, serie duplicată, schimbarea și persistența celor
  trei stări, ID inexistent, stare invalidă și câmpuri obligatorii lipsă.
- Inventar: creare, listare, SKU duplicat, actualizare parțială, păstrarea
  câmpurilor nemodificate, respingerea valorilor negative, ID inexistent.
- Alerte: stoc zero, sub prag, egal cu pragul și peste prag; actualizarea
  pragului; marcarea unei notificări ca citită și notificare inexistentă.
- Mentenanță: creare și listare, trecerea echipamentului în mentenanță,
  echipament inexistent și câmp obligatoriu lipsă.
- Finalizare: fără piese, cu una sau mai multe piese distincte, consum 10−3=7,
  epuizarea stocului, atingerea pragului și generarea alertei; consumul este
  verificat și în tabela `ticket_parts`.
- Erori de finalizare: tichet inexistent, tichet deja închis, piesă inexistentă,
  stoc insuficient și consum nepozitiv. Respingerea unei cereri nu trebuie să
  modifice stocul, tichetul, starea echipamentului sau consumurile persistate.

Rulare din rădăcina proiectului:

```powershell
.\.venv\Scripts\python.exe -m pytest -rx
```

Pragul CI rămâne 70%. Acoperirea codului nu validează autentificarea, concurența,
performanța sau toate combinațiile posibile de date.

## Defect cunoscut QA-001 — consum duplicat pentru aceeași piesă

Severitate: ridicată — stocul poate deveni negativ.

Precondiții: o piesă cu stoc 10 și un tichet deschis. Cerere către
`POST /tickets/{id}/complete` cu aceeași piesă în două poziții:

```json
{
  "parts_used": [
    {"part_id": 1, "quantity_used": 6},
    {"part_id": 1, "quantity_used": 6}
  ]
}
```

Înlocuiți ID-urile cu înregistrările create pentru reproducere.

Rezultat așteptat: HTTP 400/422, fără schimbări în date, deoarece consumul total
12 depășește stocul 10.

Comportamentul actual validează fiecare poziție separat înainte de consum,
permițând finalizarea și stocul −2. Remedierea trebuie să valideze totalul pentru
fiecare piesă sau să respingă piesele duplicate înainte de orice modificare.

Testul `test_duplicate_part_cannot_exceed_available_stock` este marcat
`xfail(strict=True)`: documentează explicit defectul și nu este raportat ca test
trecut. După remediere, eliminați marcajul; o trecere neașteptată blochează CI
pentru a cere actualizarea acestui raport și a testului.

Nu s-a modificat logica rutelor în acest livrabil QA.
