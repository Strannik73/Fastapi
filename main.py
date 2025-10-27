# uvicorn main:app --reload                  (запуск )

import csv
from datetime import timedelta, datetime
import uuid
import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# Подключение всех статических файлов, шаблонов,
# инициализация веб-приложения, описание глобальных переменных
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# app.mount("/sources", StaticFiles(directory="sources"), name="sources")
templates = Jinja2Templates(directory="templates")

USERS = "users.csv"
SESSION_TTL = timedelta(10)
sessions = {}
white_urls = ["/", "/login", "/logout"]

# Контрорль авторизации и сессии
@app.middleware("http")
async def check_session(request: Request, call_next):
    if request.url.path.startswith("/static") or request.url.path in white_urls:
        return await call_next(request)

    session_id = request.cookies.get("session_id")
    if session_id not in sessions:
        return RedirectResponse(url="/")
    
    created_session = sessions[session_id]
    if datetime.now() - created_session > SESSION_TTL:
        del sessions[session_id]
        return RedirectResponse(url="/")

    return await call_next(request)   

# Маршрутизации приложения
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})  #{"request": request} Если нужно обращаться к вебу и обратно(нужен всегда)


@app.post("/templates/login")
def login(request: Request,
          username: str = Form(...),
          password: str = Form(...)):
    users = pd.read_csv(USERS)
    if username  in users['users'].values[0]:
        if str(users[users['users'] == username].values[0][1]) == password:
            session_id = str(uuid.uuid4())
            sessions[session_id] = datetime.now()
            response = RedirectResponse(url=f"/home/{username}", status_code=302)
            response.set_cookie(key="session_id", value=session_id)
            return response
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль"})
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин"})
    
@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    del sessions[session_id] 
    return templates.TemplateResponse("login.html", {"request": request, "message": "Сессия завершина", "url": "/login"})

@app.get("/main", response_class=HTMLResponse)
def main_page(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

@app.get("/home/{username}", response_class=HTMLResponse)
def home(request: Request, username: str):
    # Если нужно показывать личную страницу — можно вернуть main.html с данными пользователя
    return templates.TemplateResponse("main.html", {"request": request, "username": username})

@app.get("/home/admin", response_class=HTMLResponse)
def get_start_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/templates/register")
def register(request: Request,
             username: str = Form(...),
             password: str = Form(...)):
    try:
        users = pd.read_csv(USERS)
    except Exception:
        users = pd.DataFrame(columns=["users", "password"])

    if username in users["users"].values:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Пользователь уже существует"})

    users = users.append({"users": username, "password": password}, ignore_index=True)
    users.to_csv(USERS, index=False)

    session_id = str(uuid.uuid4())
    sessions[session_id] = datetime.now()
    response = RedirectResponse(url="/main", status_code=302)
    response.set_cookie(key="session_id", value=session_id)
    return



# # from datetime import timedelta, datetime
# import uuid
# import pandas as pd
# from fastapi import FastAPI, Form, Request
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates

# app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# USERS = "users.csv"
# SESSION_TTL = timedelta(days=10)
# sessions = {}
# white_urls = ["/", "/login", "/logout", "/register", "/main"]

# @app.middleware("http")
# async def check_session(request: Request, call_next):
#     if request.url.path.startswith("/static") or request.url.path in white_urls:
#         return await call_next(request)
#     session_id = request.cookies.get("session_id")
#     if not session_id or session_id not in sessions:
#         return RedirectResponse(url="/login")
#     created = sessions.get(session_id)
#     if not created or datetime.now() - created > SESSION_TTL:
#         sessions.pop(session_id, None)
#         return RedirectResponse(url="/login")
#     return await call_next(request)

# @app.get("/", response_class=HTMLResponse)
# @app.get("/login", response_class=HTMLResponse)
# def get_login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

# @app.post("/login")
# def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
#     try:
#         users = pd.read_csv(USERS)
#     except Exception:
#         users = pd.DataFrame(columns=["users", "password"])

#     if username in users["users"].values:
#         stored_password = users.loc[users["users"] == username, "password"].values[0]
#         if str(stored_password) == str(password):
#             session_id = str(uuid.uuid4())
#             sessions[session_id] = datetime.now()
#             response = RedirectResponse(url="/main", status_code=303)
#             response.set_cookie(key="session_id", value=session_id, httponly=True)
#             return response
#         return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль"})
#     return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин"})

# @app.get("/register", response_class=HTMLResponse)
# def get_register_page(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})

# @app.post("/register")
# def post_register(request: Request, username: str = Form(...), password: str = Form(...)):
#     try:
#         users = pd.read_csv(USERS)
#     except Exception:
#         users = pd.DataFrame(columns=["users", "password"])

#     if username in users["users"].values:
#         return templates.TemplateResponse("register.html", {"request": request, "error": "Пользователь уже существует"})

#     users = users.append({"users": username, "password": password}, ignore_index=True)
#     users.to_csv(USERS, index=False)

#     session_id = str(uuid.uuid4())
#     sessions[session_id] = datetime.now()
#     response = RedirectResponse(url="/main", status_code=303)
#     response.set_cookie(key="session_id", value=session_id, httponly=True)
#     return response

# @app.get("/main", response_class=HTMLResponse)
# def main_page(request: Request):
#     return templates.TemplateResponse("main.html", {"request": request})

# @app.get("/logout", response_class=HTMLResponse)
# def logout(request: Request):
#     session_id = request.cookies.get("session_id")
#     if session_id:
#         sessions.pop(session_id, None)
#     return RedirectResponse(url="/login", status_code=303)
