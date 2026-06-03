from contextlib import contextmanager
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import ENGINE, Base, Categoria, Producto, Venta, DetalleVenta, Fiado, FiadoItem, ProductosMayoreo, \
    PrecioDocumentos, PrecioMantemiento
from models import Observacion

# ── Sesión ────────────────────────────────────────────────────────────────────
@contextmanager
def get_session():
    with Session(ENGINE) as session:
        yield session

# ── Inicializar base de datos ─────────────────────────────────────────────────
def init_db():
    Base.metadata.create_all(ENGINE)

# ── Categorías ────────────────────────────────────────────────────────────────
def get_categorias():
    with get_session() as s:
        return [c.nombre for c in s.query(Categoria).order_by(Categoria.nombre).all()]

def get_categoria_id(nombre):
    with get_session() as s:
        cat = s.query(Categoria).filter_by(nombre=nombre).first()
        if cat is None:
            raise ValueError(f"Categoría '{nombre}' no existe en la base de datos.")
        return cat.id

def crear_categoria(nombre):
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    with get_session() as s:
        if s.query(Categoria).filter_by(nombre=nombre).first():
            raise ValueError(f"Ya existe una categoría llamada '{nombre}'.")
        cat = Categoria(nombre=nombre)
        s.add(cat)
        s.commit()
        return cat.id

def editar_categoria(cid, nuevo_nombre):
    nuevo_nombre = nuevo_nombre.strip()
    if not nuevo_nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    with get_session() as s:
        if s.query(Categoria).filter(
            Categoria.nombre == nuevo_nombre, Categoria.id != cid
        ).first():
            raise ValueError(f"Ya existe una categoría llamada '{nuevo_nombre}'.")
        cat = s.get(Categoria, cid)
        if cat is None:
            raise ValueError(f"Categoría con ID {cid} no existe.")
        cat.nombre = nuevo_nombre
        s.commit()

def eliminar_categoria(cid):
    with get_session() as s:
        count = s.query(Producto).filter_by(categoria_id=cid).count()
        if count > 0:
            raise ValueError(
                f"No se puede eliminar: la categoría tiene {count} producto(s) asignado(s).\n"
                "Reasigna o elimina los productos primero."
            )
        cat = s.get(Categoria, cid)
        if cat is None:
            raise ValueError("Categoría no encontrada.")
        s.delete(cat)
        s.commit()

def sincronizar_producto_desde_doc(nombre, precio, cat_nombre):
    """
    Crea o actualiza un producto en inventario desde un precio_documento.
    Retorna: 'creado' | 'actualizado'
    """
    with get_session() as s:
        cat = s.query(Categoria).filter_by(nombre=cat_nombre).first()
        if cat is None:
            raise ValueError(f"Categoría '{cat_nombre}' no existe.")
        prod = s.query(Producto).filter_by(nombre=nombre, categoria_id=cat.id).first()
        if prod:
            prod.precio = precio
            s.commit()
            return "actualizado"
        else:
            s.add(Producto(categoria_id=cat.id, nombre=nombre,
                           tipo="Servicio", precio=precio, stock=0))
            s.commit()
            return "creado"

def get_categorias_detalle():
    """Retorna lista de dicts con id, nombre y cantidad de productos."""
    with get_session() as s:
        cats = s.query(Categoria).order_by(Categoria.id.asc()).all()
        return [
            {"id": c.id, "nombre": c.nombre,
             "count": s.query(Producto).filter_by(categoria_id=c.id).count()}
            for c in cats
        ]

# ── Productos ─────────────────────────────────────────────────────────────────
def get_productos(buscar="", categoria=None):
    with get_session() as s:
        q = s.query(Producto, Categoria).join(Categoria)
        if buscar:
            q = q.filter(
                Producto.nombre.ilike(f"%{buscar}%") |
                Categoria.nombre.ilike(f"%{buscar}%")
            )
        if categoria:
            q = q.filter(Categoria.nombre == categoria)
        rows = q.order_by(Categoria.nombre, Producto.nombre).all()
        return [{"id": p.id, "cat": c.nombre, "nombre": p.nombre,
                 "precio": p.precio, "stock": p.stock, "tipo": p.tipo,
                 "precio_variable": p.precio_variable or 0}
                for p, c in rows]




def get_productos_en_stock(buscar=""):
    with get_session() as s:
        q = s.query(Producto).filter(
            (Producto.stock > 0) | (Producto.tipo == "Servicio")
        )
        if buscar:
            q = q.filter(Producto.nombre.ilike(f"%{buscar}%"))
        return [{"id": p.id, "nombre": p.nombre, "precio": p.precio,
                 "stock": p.stock, "tipo": p.tipo,
                 "precio_variable": p.precio_variable or 0}
                for p in q.order_by(Producto.nombre).all()]

def get_producto(pid):
    with get_session() as s:
        p = s.get(Producto, pid)
        if p is None:
            raise ValueError(f"Producto con ID {pid} no existe.")
        c = s.get(Categoria, p.categoria_id)
        if c is None:
            raise ValueError(f"La categoría del producto ID {pid} fue eliminada.")
        return {"id": p.id, "nombre": p.nombre, "precio": p.precio,
                "stock": p.stock, "tipo": p.tipo,
                "categoria_id": p.categoria_id, "cat": c.nombre,
                "precio_variable": p.precio_variable or 0}

def crear_producto(cat_nombre, nombre, tipo, precio, stock, precio_variable=0):
    with get_session() as s:
        cat = s.query(Categoria).filter_by(nombre=cat_nombre).first()
        if cat is None:
            raise ValueError(f"Categoría '{cat_nombre}' no existe.")
        p = Producto(categoria_id=cat.id, nombre=nombre,
                     tipo=tipo, precio=precio, stock=stock,
                     precio_variable=precio_variable)
        s.add(p)
        s.commit()
        return p.id

def editar_producto(pid, cat_nombre, nombre, tipo, precio, precio_variable=0):
    with get_session() as s:
        cat = s.query(Categoria).filter_by(nombre=cat_nombre).first()
        if cat is None:
            raise ValueError(f"Categoría '{cat_nombre}' no existe.")
        p   = s.get(Producto, pid)
        if p is None:
            raise ValueError(f"Producto con ID {pid} no existe.")
        p.categoria_id = cat.id
        p.nombre       = nombre
        p.tipo         = tipo
        p.precio       = precio
        p.precio_variable = precio_variable
        s.commit()

def eliminar_producto(pid):
    with get_session() as s:
        s.delete(s.get(Producto, pid))
        s.commit()

def agregar_stock(pid, cantidad):
    with get_session() as s:
        s.get(Producto, pid).stock += cantidad
        s.commit()

# ── Ventas ────────────────────────────────────────────────────────────────────
def registrar_venta(fecha, total, items, descuento=0.0):
    with get_session() as s:
        venta = Venta(fecha=fecha, total=total, descuento=descuento)
        s.add(venta)
        s.flush()
        for it in items:
            s.add(DetalleVenta(
                venta_id    = venta.id,
                producto_id = it["producto_id"],
                nombre_venta=it.get("nombre_venta", ""),
                cantidad    = it["cantidad"],
                precio_unit = it["precio_unit"],
                subtotal    = it["subtotal"],
                descuento = it.get("descuento", 0.0)))
            if it.get("tipo", "Producto") == "Producto":
                s.get(Producto, it["producto_id"]).stock -= it["cantidad"]
        s.commit()

def get_ventas():
    with get_session() as s:
        ventas = s.query(Venta).order_by(Venta.id.desc()).limit(100).all()
        result = []
        for v in ventas:
            detalles = (s.query(DetalleVenta, Producto)
                         .join(Producto)
                         .filter(DetalleVenta.venta_id == v.id).all())
            resumen = ", ".join(f"{p.nombre} x{d.cantidad}" for d, p in detalles)
            result.append({"id": v.id, "fecha": v.fecha,
                            "total": v.total, "descuento": v.descuento,
                            "resumen": resumen})
        return result

def get_detalle_venta(venta_id):
    with get_session() as s:
        rows = (s.query(DetalleVenta, Producto)
                  .join(Producto)
                  .filter(DetalleVenta.venta_id == venta_id).all())
        return [{"prod": d.nombre_venta or p.nombre,
                 "cantidad": d.cantidad,
                 "precio_unit": d.precio_unit,
                 "subtotal": d.subtotal,
                 "descuento": d.descuento or 0.0}
                for d, p in rows]


def get_ventas_hoy(fecha_prefix):
    with get_session() as s:
        ventas = (s.query(Venta)
                   .filter(Venta.fecha.like(f"{fecha_prefix}%"))
                   .order_by(Venta.id.asc()).all())
        result = []
        for v in ventas:
            detalles = (s.query(DetalleVenta, Producto)
                         .join(Producto)
                         .filter(DetalleVenta.venta_id == v.id).all())
            items = [{
                "producto": d.nombre_venta or p.nombre,
                "cantidad": d.cantidad,
                "precio":   d.precio_unit,
                "subtotal": d.subtotal,
                "descuento": d.descuento or 0.0,
            } for d, p in detalles]
            resumen = ", ".join(f"{it['producto']} x{it['cantidad']}" for it in items)
            result.append({"id": v.id, "fecha": v.fecha, "total": v.total,
                            "descuento": v.descuento or 0.0,
                            "resumen": resumen, "items": items})
        return result


# ── Dashboard ─────────────────────────────────────────────────────────────────
def get_stats(hoy_prefix, mes_prefix):
    with get_session() as s:
        total_prod = s.query(func.count(Producto.id)).scalar()
        sin_stock  = s.query(func.count(Producto.id)).filter(
            Producto.stock == 0, Producto.tipo == "Producto").scalar()
        ventas_hoy = (s.query(func.coalesce(func.sum(Venta.total), 0))
                       .filter(Venta.fecha.like(f"{hoy_prefix}%")).scalar())
        ventas_mes = (s.query(func.coalesce(func.sum(Venta.total), 0))
                       .filter(Venta.fecha.like(f"{mes_prefix}%")).scalar())
        return total_prod, sin_stock, float(ventas_hoy), float(ventas_mes)

def get_stock_bajo(limite=5):
    with get_session() as s:
        rows = (s.query(Producto, Categoria).join(Categoria)
                  .filter(Producto.stock <= limite, Producto.tipo == "Producto")
                  .order_by(Producto.stock.asc()).limit(20).all())
        return [{"nombre": p.nombre, "stock": p.stock, "cat": c.nombre}
                for p, c in rows]

# ── Observaciones / Caja chica ────────────────────────────────────────────────
def get_observaciones_hoy(fecha_prefix):
    with get_session() as s:
        rows = (s.query(Observacion)
                  .filter(Observacion.fecha.like(f"{fecha_prefix}%"))
                  .order_by(Observacion.id.desc()).all())
        return [{"id": o.id, "fecha": o.fecha,
                 "monto": o.monto, "concepto": o.concepto}
                for o in rows]

def agregar_observacion(fecha, monto, concepto):
    with get_session() as s:
        s.add(Observacion(fecha=fecha, monto=monto, concepto=concepto))
        s.commit()

def eliminar_observacion(oid):
    with get_session() as s:
        s.delete(s.get(Observacion, oid))
        s.commit()

# ── Fiados / Deudas ───────────────────────────────────────────────────────────
def get_fiados(filtro="pendiente", buscar=""):
    """filtro: 'pendiente' | 'pagado' | 'todos'"""
    with get_session() as s:
        q = s.query(Fiado)
        if filtro == "pendiente":
            q = q.filter(Fiado.estado == "pendiente")
        elif filtro == "pagado":
            q = q.filter(Fiado.estado == "pagado")
        if buscar:
            q = q.filter(Fiado.cliente.ilike(f"%{buscar}%"))
        rows = q.order_by(Fiado.id.desc()).all()

        result = []
        for f in rows:
            items = s.query(FiadoItem).filter(FiadoItem.fiado_id == f.id).all()
            resumen = ", ".join(f"{it.producto} x{it.cantidad}" for it in items)
            result.append({
                "id": f.id, "fecha": f.fecha, "cliente": f.cliente,
                "total": f.total, "estado": f.estado,
                "fecha_pago": f.fecha_pago, "notas": f.notas,
                "resumen": resumen,
                "num_items": len(items)
            })
        return result

def get_fiado_detalle(fid):
    """Retorna los items de una deuda específica."""
    with get_session() as s:
        items = s.query(FiadoItem).filter(FiadoItem.fiado_id == fid).all()
        return [{"producto": it.producto, "cantidad": it.cantidad,
                 "precio": it.precio, "subtotal": it.subtotal}
                for it in items]

def agregar_fiado(fecha, cliente, items, notas=""):
    """items = [{"producto", "cantidad", "precio", "subtotal"}, ...]"""
    with get_session() as s:
        total = sum(it["subtotal"] for it in items)
        deuda = Fiado(fecha=fecha, cliente=cliente, total=total, notas=notas)
        s.add(deuda)
        s.flush()
        for it in items:
            s.add(FiadoItem(fiado_id=deuda.id,
                             producto=it["producto"],
                             cantidad=it["cantidad"],
                             precio=it["precio"],
                             subtotal=it["subtotal"]))
        s.commit()

def marcar_pagado(fid, fecha_pago):
    with get_session() as s:
        f = s.get(Fiado, fid)
        f.estado = "pagado"
        f.fecha_pago = fecha_pago
        s.commit()

def eliminar_fiado(fid):
    with get_session() as s:
        s.delete(s.get(Fiado, fid))
        s.commit()

def get_stats_fiados():
    with get_session() as s:
        pendientes = s.query(Fiado).filter(Fiado.estado == "pendiente").all()
        return len(pendientes), sum(f.total for f in pendientes)

def limpiar_pagados_antiguos(dias=7):
    with get_session() as s:
        pagados = (s.query(Fiado)
                    .filter(Fiado.estado == "pagado",
                            Fiado.fecha_pago != None).all())
        ahora = datetime.now()
        borrados = 0
        for f in pagados:
            try:
                fpago = datetime.strptime(f.fecha_pago, "%Y-%m-%d %H:%M:%S")
                if (ahora - fpago).days >= dias:
                    s.delete(f)
                    borrados += 1
            except (ValueError, TypeError):
                continue
        s.commit()
        return borrados

def get_fiados_hoy(fecha_prefix):
    """
    Retorna para el reporte del día:
    - Fiados PAGADOS hoy (fecha_pago coincide con hoy)
    - Fiados PENDIENTES (sin importar cuándo se registraron)
    """
    with get_session() as s:
        fiados = (s.query(Fiado).filter(
            ((Fiado.estado == "pagado") &
             (Fiado.fecha_pago.like(f"{fecha_prefix}%")))
            |
            (Fiado.estado == "pendiente")
        ).order_by(Fiado.id.asc()).all())

        result = []
        for f in fiados:
            items_db = s.query(FiadoItem).filter(FiadoItem.fiado_id == f.id).all()
            items = [{
                "producto": it.producto,
                "cantidad": it.cantidad,
                "precio":   it.precio,
                "subtotal": it.subtotal,
            } for it in items_db]
            resumen = ", ".join(f"{it['producto']} x{it['cantidad']}" for it in items)
            fecha_mostrar = f.fecha_pago if f.estado == "pagado" else f.fecha
            result.append({
                "id": f.id,
                "fecha": fecha_mostrar,
                "fecha_registro": f.fecha,
                "cliente": f.cliente,
                "total": f.total,
                "estado": f.estado,
                "resumen": resumen,
                "items": items,
            })
        return result


def get_mayoreos(producto_id):
    with get_session() as s:
        rows = s.query(ProductosMayoreo).filter_by(producto_id=producto_id).all()
        return [{"id": r.id, "nombre": r.nombre, "precio": r.precio} for r in rows]

def guardar_mayoreos(producto_id, mayoreos):
    """presentaciones = [{"nombre": str, "precio": float}, ...]"""
    with get_session() as s:
        # Borrar las anteriores y reemplazar
        s.query(ProductosMayoreo).filter_by(producto_id=producto_id).delete()
        for p in mayoreos:
            s.add(ProductosMayoreo(
                producto_id=producto_id,
                nombre=p["nombre"],
                precio=p["precio"]))
        s.commit()



# ── Precio de documentos ───────────────────────────────────────────────────────────
def get_precio_documentos():
    with get_session() as s:
        rows = s.query(PrecioDocumentos).order_by(PrecioDocumentos.id.asc()).all()
        return [{"id": r.id, "nombre": r.nombre, "precio": r.precio,
                 "precio_descargar": r.precio_descargar,
                 "precio_validaciones": r.precio_validaciones,
                 "link_validaciones": r.link_validaciones}
                for r in rows]

def get_precio_documento(fid):
    with get_session() as s:
        r = s.get(PrecioDocumentos, fid)
        return {"id": r.id, "nombre": r.nombre, "precio": r.precio,
                "precio_descargar": r.precio_descargar,
                "precio_validaciones": r.precio_validaciones,
                "link_validaciones": r.link_validaciones}

def guardar_precio_documento(fid, nombre, precio, precio_descargar,
                              precio_validaciones, link_validaciones):
    with get_session() as s:
        if fid is None:
            s.add(PrecioDocumentos(nombre=nombre, precio=precio,
                                   precio_descargar=precio_descargar,
                                   precio_validaciones=precio_validaciones,
                                   link_validaciones=link_validaciones))
        else:
            r = s.get(PrecioDocumentos, fid)
            r.nombre               = nombre
            r.precio               = precio
            r.precio_descargar     = precio_descargar
            r.precio_validaciones  = precio_validaciones
            r.link_validaciones    = link_validaciones
        s.commit()

def eliminar_precio_documento(fid):
    with get_session() as s:
        s.delete(s.get(PrecioDocumentos, fid))
        s.commit()


# ── Precio de Mantenimiento ───────────────────────────────────────────────────────────

def get_precio_mantenimientos():
    with get_session() as s:
        rows = s.query(PrecioMantemiento).order_by(PrecioMantemiento.id.asc()).all()
        return [{"id": r.id, "nombre": r.nombre, "precio": r.precio, "observaciones": r.observaciones} for r in rows]

def get_precio_mantenimiento(fid):
    with get_session() as s:
        r = s.get(PrecioMantemiento, fid)
        return {"id": r.id, "nombre": r.nombre, "precio": r.precio,
                "observaciones": r.observaciones}


def guardar_precio_mantenimiento(fid, nombre, precio, observaciones):
    with get_session() as s:
        if fid is None:
            s.add(PrecioMantemiento(nombre=nombre, precio=precio, observaciones=observaciones))
        else:
            r = s.get(PrecioMantemiento, fid)
            r.nombre = nombre
            r.precio = precio
            r.observaciones = observaciones
        s.commit()

def eliminar_precio_mantenimiento(fid):
    with get_session() as s:
        s.delete(s.get(PrecioMantemiento, fid))
        s.commit()