# Backend SmartMIM

FastAPI + SQLAlchemy + SQLite. Pentru Docker și CI consultați `../docs/devops.md`.

Rulare fără Docker din directorul `backend`, după instalarea dependențelor în
mediul virtual conform ghidului:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Implicit se folosește `sqlite:///./smartmim.db`. `DATABASE_URL` poate indica o bază
separată. Testele folosesc o bază temporară, fără să modifice baza proiectului.
`CORS_ORIGINS` controlează originile frontend permise, separate prin virgulă.
