import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import FastAPI

from database import db
from vistas import router as vistas_router


def leer_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    base = Path(__file__).parent

    if not url and (base / ".env").exists():
        for linea in (base / ".env").read_text(encoding="utf-8-sig").splitlines():
            if linea.strip().startswith("DATABASE_URL="):
                url = linea.split("=", 1)[1].strip().strip('"').strip("'")

    for nombre in ("cadena", "cadena.txt", "Docs/cadena"):
        archivo = base / nombre
        if not url and archivo.exists():
            url = archivo.read_text(encoding="utf-8-sig").strip()

    if not url:
        raise RuntimeError(f"No se encontró la URL de la base de datos. Busqué en: {base}")

    partes = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(partes.query) if k != "channel_binding"]
    return urlunsplit(partes._replace(query=urlencode(query)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect(leer_database_url())
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)

app.include_router(vistas_router)