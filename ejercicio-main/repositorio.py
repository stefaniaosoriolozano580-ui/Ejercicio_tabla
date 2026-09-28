from decimal import Decimal


async def obtener_productos(conn) -> list[dict]:
    """Devuelve todos los productos, ordenados por nombre."""
    filas = await conn.fetch(
        "SELECT id, nombre, precio, cantidad, descripcion "
        "FROM productos ORDER BY nombre"
    )
    return [dict(f) for f in filas]


async def obtener_producto(conn, producto_id: int) -> dict | None:
    """Busca un producto por su clave primaria (id)."""
    fila = await conn.fetchrow(
        "SELECT id, nombre, precio, cantidad, descripcion "
        "FROM productos WHERE id = $1",
        producto_id,
    )
    return dict(fila) if fila else None


async def actualizar_producto(
    conn,
    producto_id: int,
    nombre: str,
    precio: float,
    cantidad: int,
    descripcion: str | None,
) -> bool:
    """Actualiza un producto identificado por su clave primaria (id)."""
    resultado = await conn.execute(
        "UPDATE productos "
        "SET nombre = $1, precio = $2, cantidad = $3, descripcion = $4 "
        "WHERE id = $5",
        nombre,
        Decimal(str(precio)),
        cantidad,
        descripcion,
        producto_id,
    )
    return resultado == "UPDATE 1"