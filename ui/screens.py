from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="ui/templates")
def home_screen(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
