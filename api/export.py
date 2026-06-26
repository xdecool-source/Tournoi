"""
Génère et télécharge le fichier Excel des inscriptions.
GET /export-excel
POST /admin/export
GET /inscrits
GET /export-inscrits

"""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from export.generate_inscription import generate
from services.db import get_conn

from api.admin import get_current_admin

router = APIRouter()

templates = Jinja2Templates(
    directory="userinterface/templates"
)

# Export Excel

@router.get("/export-excel")

async def export_excel(
    admin=Depends(get_current_admin)
):
    stream = generate()
    if not stream:
        raise HTTPException(
            status_code=404,
            detail="Aucune donnée"
        )
    now = datetime.now(
        ZoneInfo("Europe/Paris")
    ).strftime("%d-%m-%Y_%Hh%M")

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            f'attachment; filename="Inscriptions_Tournoi_{now}.xlsx"'
        }
    )

# Export Excel Admin

@router.post("/admin/export")

async def download_excel(
    admin=Depends(get_current_admin)
):
    excel_stream = generate()
    if not excel_stream:

        raise HTTPException(
            status_code=500,
            detail="Erreur génération Excel"
        )
    excel_stream.seek(0)
    filename = datetime.now(
        ZoneInfo("Europe/Paris")
    ).strftime(

        "Inscriptions_Tournoi_%d-%m-%Y_%Hh%M.xlsx"
    )
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            f"attachment; filename={filename}"
        }
    )

# Liste des inscrits

@router.get("/inscrits")

async def get_inscrits():
    try:
        async with get_conn() as conn:
            rows = await conn.fetch("""

                -- JOUEURS ACTIFS
                SELECT i.dossard, i.licence, i.nom, i.prenom, i.club, i.points, i.paiement,
                    COALESCE (array_agg (CASE
                                WHEN it.statut='ATTENTE'
                                THEN it.tableau || '_ATTENTE'
                                ELSE it.tableau
                            END
                        )
                        FILTER ( WHERE it.tableau IS NOT NULL ),
                        '{}' ) AS tableaux, FALSE AS annule FROM inscriptions i 
                        LEFT JOIN inscription_tableaux it ON i.licence = it.licence
                GROUP BY i.dossard, i.licence, i.nom, i.prenom, i.club, i.points, i.paiement
                UNION ALL 
                SELECT di.dossard, di.licence, di.nom, di.prenom, di.club, di.points, di.paiement,
                    ARRAY[]::text[] AS tableaux,
                    TRUE AS annule
                FROM delete_inscrit di
                ORDER BY
                    annule ASC,
                    points DESC
            """)

            inscrits = []
            for r in rows:
                inscrits.append({
                    "dossard": r["dossard"],
                    "licence": r["licence"],
                    "nom": r["nom"],
                    "prenom": r["prenom"],
                    "club": r["club"],
                    "points": r["points"],
                    "tableaux": r["tableaux"],
                    "annule": r["annule"]
                })
        return {
            "success": True,
            "inscrits": inscrits
        }

    except Exception as e:
        print(
            "ERREUR EXPORT INSCRITS :",
            e
        )
        return {
            "success": False,
            "error": "Erreur serveur"
        }

# Page export inscrits

@router.get("/export-inscrits",response_class=HTMLResponse)

async def export_inscrits_page(
    request: Request
):
    return templates.TemplateResponse(
        "exportInscrits.html",
        {

            "request": request
        }
    )