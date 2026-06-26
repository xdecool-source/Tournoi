rem pour l'exécution de .bat ouvrir un terminal sous VS code puis selection ▼ et choisir Command Prompt 
rem Microsoft Windows [version 10.0.26200.8457]
rem (c) Microsoft Corporation. Tous droits réservés.

@echo off
setlocal


set DATABASE_URL=postgresql://neondb_owner:npg_l72zqeXUxFbP@ep-muddy-cloud-ab6fra5w.eu-west-2.aws.neon.tech/neondb?sslmode=require
set PGPASSWORD=npg_l72zqeXUxFbP
set PGSSLMODE=require

echo =========================
echo Selection du fichier backup
echo =========================

powershell -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.OpenFileDialog; $f.InitialDirectory='C:\Users\XavierO\Tournoi\DB_export\export'; $f.Filter='Backup Files (*.backup)|*.backup'; $f.Title='Selectionner un backup PostgreSQL'; if($f.ShowDialog() -eq 'OK'){Write-Output $f.FileName}" > temp_backup.txt
set /p BACKUP_FILE=<temp_backup.txt
del temp_backup.txt

if "%BACKUP_FILE%"=="" (
    echo Aucun fichier selectionne.
    pause
    exit /b
)
echo.
echo Fichier choisi :
echo %BACKUP_FILE%
pause

echo =========================
echo Nettoyage schema
echo =========================

"C:\Program Files\PostgreSQL\18\bin\psql.exe" ^
  "%DATABASE_URL%" ^
  -c "DROP SCHEMA IF EXISTS public CASCADE;"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" ^
  "%DATABASE_URL%" ^
  -c "CREATE SCHEMA public;"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" ^
  "%DATABASE_URL%" ^
  -c "GRANT ALL ON SCHEMA public TO public;"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" ^
  "%DATABASE_URL%" ^
  -c "GRANT ALL ON SCHEMA public TO neondb_owner;"

echo =========================
echo Extensions PostgreSQL
echo =========================

"C:\Program Files\PostgreSQL\18\bin\psql.exe" ^
  "%DATABASE_URL%" ^
  -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" ^
  "%DATABASE_URL%" ^
  -c "CREATE EXTENSION IF NOT EXISTS ""uuid-ossp"";"

"C:\Program Files\PostgreSQL\18\bin\psql.exe" ^
  "%DATABASE_URL%" ^
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo =========================
echo Restore backup
echo =========================

"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" ^
  --verbose ^
  --clean ^
  --if-exists ^
  --no-owner ^
  --no-privileges ^
  -d "%DATABASE_URL%" ^
  "%BACKUP_FILE%"

pause