# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from config import config
import requests
import base64
from functions import get_manifest, get_catalog, get_meta, get_stream, fix_b64, search_catalog, get_catalog_global
import sys

templates = Environment(loader=FileSystemLoader("templates"))
app = FastAPI()

def add_cors(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    template = templates.get_template("index.html")
    response = HTMLResponse(template.render(
        title=config['title'],
        logo=config['logo'],
        description=config['description'],
        version=config['version']
    ))
    return add_cors(response)

@app.get("/img")
async def proxy_logo(url: str):
    if not url:
        return add_cors(JSONResponse(content={"error": "Nenhuma URL fornecida"}, status_code=400))
    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            return add_cors(JSONResponse(content={"error": f"Erro ao buscar a imagem: {response.status_code}"}, status_code=400))
        content_type = response.headers.get("Content-Type", "image/jpeg")
        return add_cors(Response(content=response.content, media_type=content_type))
    except requests.exceptions.RequestException as e:
        return add_cors(JSONResponse(content={"error": f"Erro ao buscar a imagem: {str(e)}"}, status_code=500))
    
@app.get("/manifest.json")
async def manifest_standard(request: Request):
    manifest = {
        'id': 'org.community.xtreampro',
        'name': config['title'],
        'version': config['version'],
        'logo': config['logo'],
        'description': config['description'],
        'idPrefixes': ['tt'],
        'catalogs': [],
        'types': ["movie", "series", "tv"],
        'resources': ["catalog", "meta", "stream"],
        'behaviorHints': {'configurable': True, 'configurationRequired': True}
    }
    return add_cors(JSONResponse(content=manifest))

@app.get("/configure")
async def configure(request: Request):
    return RedirectResponse(url="/")

@app.get("/b64/{base64str}/configure")
async def configure2(base64str: str, request: Request):
    return RedirectResponse(url="/")
    
@app.get("/b64/{base64str}/manifest.json")
async def manifest_custom(base64str: str, request: Request):
    if not base64str:
        raise HTTPException(status_code=400, detail="Invalid request format")
    
    base64str = fix_b64(base64str)  # Corrige possíveis erros de Base64

    try:
        user_conf = base64.b64decode(base64str).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 configuration")

    manifest = get_manifest(base64str)
    return add_cors(JSONResponse(content=manifest))

@app.get("/b64/{base64str}/catalog/{type}/{id}/search={query}.json")
async def search_funcion(base64str: str, type: str, id: str, query: str, request: Request):   
    results = search_catalog(base64str, type, query)
    return add_cors(JSONResponse(content={"metas": results}))

@app.get("/b64/{base64str}/catalog/{type}/{id_prefix}/genre={genre}.json")
async def catalog_genre(base64str: str, type: str, id_prefix: str, genre: str, request: Request):  
    catalog = get_catalog(base64str, type, genre)
    return add_cors(JSONResponse(content={"metas": catalog}))

@app.get("/b64/{base64str}/catalog/{type}/{id}.json")
async def catalog_global(base64str: str, type: str, id: str, request: Request):  
    catalog = get_catalog_global(base64str, type)
    return add_cors(JSONResponse(content={"metas": catalog}))

@app.get("/b64/{base64str}/meta/{type}/{id}.json")
async def meta(base64str: str, type: str, id: str, request: Request):    
    meta = get_meta(base64str, type, id)
    return add_cors(JSONResponse(content={"meta": meta}))

@app.get("/b64/{base64str}/stream/{type}/{id}.json")
async def stream(base64str: str, type: str, id: str, request: Request):   
    streams = get_stream(base64str, type, id)
    return add_cors(JSONResponse(content={"streams": streams.get("streams", [])}))

# if __name__ == "__main__":
#     try:
#         if "--run" in sys.argv:
#             from uvicorn import Server, Config as Config_
#             config_ = Config_(app=app, host="0.0.0.0", port=80)
#             server = Server(config_)
#             server.run()
#     except:
#         pass






    








    

