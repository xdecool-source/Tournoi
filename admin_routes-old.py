from fastapi import APIRouter, Header, HTTPException
from services.admin_ex_mail import process_admin_export
import os

router = APIRouter() 

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


def check_admin(api_key: str):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/admin/export")
async def trigger_export(x_api_key: str = Header(...)):

    check_admin(x_api_key)

    await process_admin_export()

    return {"status": "export lancé"}