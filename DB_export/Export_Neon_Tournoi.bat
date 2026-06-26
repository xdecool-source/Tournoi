@echo off

set PGPASSWORD=npg_l72zqeXUxFbP
set PGSSLMODE=require
set DATE=%DATE:/=-%_%TIME::=-%

"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" ^
 -h ep-muddy-cloud-ab6fra5w.eu-west-2.aws.neon.tech ^
 -p 5432 ^
 -U neondb_owner ^
 -d neondb ^
 -F c ^
 -f "C:\Users\XavierO\Tournoi\DB_export\export\Tournoi_Neon_%DATE%.backup"

@echo on

"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" ^
-l "C:\Users\XavierO\Tournoi\DB_export\export\Tournoi_Neon_%DATE%.backup"
