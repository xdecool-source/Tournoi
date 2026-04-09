# Appel les Templates 

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="userinterface/templates")

#  désactive cache (clé du bug)

templates.env.cache = {}

def home_screen(request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )