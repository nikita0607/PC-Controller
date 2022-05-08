import pcclient

from fastapi import FastAPI, Request, Response, Cookie
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


async def render_template(req, filename, **kwargs):
    kwargs["request"] = req
    return templates.TemplateResponse(filename, kwargs)

 
@app.get("/", response_class=HTMLResponse)
async def main(req: Request, login: Optional[str] = Cookie(None)):
    print(login)
    return await render_template(req, "index.html")


@app.get("/login", response_class=HTMLResponse)
async def login(req: Request):
    return await render_template(req, "login.html")


@app.post("/login", response_class=HTMLResponse)
async def _login(req: Request, resp: Response):
    resp.set_cookie(key="login", value="value")
    return await main(req, "value")
