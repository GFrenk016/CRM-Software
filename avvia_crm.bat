@echo off
title CRM La Piacentino
cd /d "%~dp0"

REM --- Ambiente virtuale (creato solo se manca) ---
if not exist ".venv\Scripts\activate.bat" (
    echo Primo avvio: creazione dell'ambiente virtuale, un momento...
    python -m venv .venv
)
call ".venv\Scripts\activate.bat"

REM --- Dipendenze: sempre allineate a requirements.txt ---
REM Eseguito a ogni avvio (non solo alla creazione del .venv) cosi' i pacchetti
REM nuovi, es. Flask-Migrate, arrivano anche a chi aveva gia' un .venv. E' veloce
REM quando e' gia' tutto installato: pip salta i download e non tocca la rete.
echo Controllo/aggiornamento delle dipendenze da requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo AVVISO: non e' stato possibile aggiornare le dipendenze ^(sei offline?^).
    echo Proseguo con i pacchetti gia' installati.
    echo.
)

REM --- Controllo database "legacy" (creato prima delle migrazioni) ---
REM Un crm.db creato dal vecchio db.create_all() ha le tabelle ma NON la tabella
REM alembic_version: con le migrazioni le nuove tabelle (Pratiche, Veicoli) non
REM verrebbero create. Lo rileviamo qui e avvisiamo l'utente PRIMA di avviare.
if exist "crm.db" (
    python -c "import sqlite3,sys;con=sqlite3.connect('crm.db');rows=con.execute('SELECT type,name FROM sqlite_master').fetchall();con.close();tables=[n for t,n in rows if t=='table'];sys.exit(2 if tables and 'alembic_version' not in tables else 0)"
    if errorlevel 2 goto legacy_db
)

goto start_app

:legacy_db
echo.
echo ============================================================
echo   ATTENZIONE: rilevato un database "crm.db" datato.
echo.
echo   E' stato creato prima dell'introduzione delle migrazioni e
echo   contiene solo DATI DI ESEMPIO. Non e' compatibile con il
echo   nuovo sistema: le tabelle Pratiche e Veicoli non verrebbero
echo   create e l'app potrebbe non funzionare correttamente.
echo.
echo   Soluzione: fai un backup ed elimina crm.db. Verra' ricreato
echo   automaticamente, aggiornato e con i dati di esempio.
echo ============================================================
echo.
choice /C SN /N /M "Faccio io backup (crm.db.bak) ed elimino crm.db per procedere? [S/N] "
if errorlevel 2 goto abort_legacy

REM Scelta S: backup + eliminazione, poi si prosegue con la ricreazione.
if exist "crm.db.bak" del /Q "crm.db.bak"
copy /Y "crm.db" "crm.db.bak" >nul
del /Q "crm.db"
echo.
echo Backup salvato in crm.db.bak e crm.db rimosso: verra' ricreato aggiornato.
echo.
goto start_app

:abort_legacy
echo.
echo Avvio interrotto: nessun file e' stato modificato.
echo Quando vuoi, fai un backup di crm.db, eliminalo e riavvia questo file.
echo.
pause
exit /b 1

:start_app
start "" http://localhost:5000
python app.py

pause
