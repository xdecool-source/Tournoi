rem pour l'exécution de .bat ouvrir un terminal sous VS code puis selection ▼ et choisir Command Prompt 
rem Microsoft Windows [version 10.0.26200.8457]
rem (c) Microsoft Corporation. Tous droits réservés.

@echo off
setlocal


set DATABASE_URL=postgresql://neondb_owner:npg_l72zqeXUxFbP@ep-muddy-cloud-ab6fra5w.eu-west-2.aws.neon.tech/neondb?sslmode=require
set PGPASSWORD=npg_l72zqeXUxFbP
set PGSSLMODE=require


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

pause