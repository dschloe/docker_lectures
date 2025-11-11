import os, pymysql
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

DB_HOST=os.getenv("DB_HOST","db1"); DB_PORT=int(os.getenv("DB_PORT","3306"))
DB_USER=os.getenv("DB_USER","root"); DB_PASS=os.getenv("DB_PASS","1234")
DB_NAME=os.getenv("DB_NAME","testdb")

def conn(): return pymysql.connect(host=DB_HOST,port=DB_PORT,user=DB_USER,password=DB_PASS,database=DB_NAME,autocommit=True)

app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
tpl=Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    with conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT id,msg FROM demo ORDER BY id DESC LIMIT 5")
            rows=cur.fetchall()
    return tpl.TemplateResponse("index.html", {"request":request, "rows":rows})
