from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dependencias import ConnectionDep
from esquemas import ProductoActualizar
from repositorio import actualizar_producto, obtener_producto, obtener_productos

router = APIRouter(tags=["productos"])

templates = Jinja2Templates(directory="templates")


@router.get("/productos")
async def listar_productos(request: Request, conn: ConnectionDep):
    productos = await obtener_productos(conn)
    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={"productos": productos},
    )


@router.get("/productos/{producto_id}/editar")
async def editar_producto_vista(request: Request, conn: ConnectionDep, producto_id: int):
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_editar.html",
        context={
            "producto": producto,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": producto["cantidad"],
            "descripcion": producto["descripcion"] or "",
            "errores": {},
        },
    )


@router.get("/productos/{producto_id}/cancelar")
async def cancelar_edicion_vista(request: Request, conn: ConnectionDep, producto_id: int):
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_producto.html",
        context={"producto": producto},
    )


@router.post("/productos/{producto_id}")
async def guardar_producto_vista(
    request: Request,
    conn: ConnectionDep,
    producto_id: int,
    nombre: Annotated[str | None, Form()] = None,
    precio: Annotated[str | None, Form()] = None,
    cantidad: Annotated[str | None, Form()] = None,
    descripcion: Annotated[str | None, Form()] = None,
):
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )

    errores = {}
    datos = {
        "nombre": (nombre or "").strip(),
        "descripcion": (descripcion or "").strip() or None,
    }

    try:
        datos["precio"] = float((precio or "").strip().replace(",", "."))
    except ValueError:
        errores["precio"] = "El precio debe ser un número."

    try:
        datos["cantidad"] = int((cantidad or "").strip())
    except ValueError:
        errores["cantidad"] = "La cantidad debe ser un número entero."

    mensajes = {
        "nombre": "El nombre es obligatorio (máximo 100 caracteres).",
        "precio": "El precio debe ser mayor que cero.",
        "cantidad": "La cantidad debe ser un entero mayor o igual que cero.",
    }
    validado = None
    try:
        validado = ProductoActualizar(**datos)
    except ValidationError as e:
        for err in e.errors():
            campo = err["loc"][0]
            if campo in mensajes:
                errores.setdefault(campo, mensajes[campo])

    if errores or validado is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/fila_editar.html",
            status_code=422,
            context={
                "producto": producto,
                "nombre": nombre or "",
                "precio": precio or "",
                "cantidad": cantidad or "",
                "descripcion": descripcion or "",
                "errores": errores,
            },
        )

    ok = await actualizar_producto(
        conn,
        producto_id,
        validado.nombre,
        validado.precio,
        validado.cantidad,
        validado.descripcion,
    )
    if not ok:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )

    producto_actualizado = await obtener_producto(conn, producto_id)
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_actualizada.html",
        context={"producto": producto_actualizado},
    )