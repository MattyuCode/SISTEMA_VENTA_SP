from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import ENGINE, Base, Categoria, Producto, Venta, DetalleVenta

# ── Sesión ────────────────────────────────────────────────────────────────────
@contextmanager
def get_session():
    with Session(ENGINE) as session:
        yield session

# ── Inicializar base de datos ─────────────────────────────────────────────────
def init_db():
    Base.metadata.create_all(ENGINE)
    cats = ["Lápices","Lapiceros","Cuadernos","Hojas","Adhesivos","Papelería"]
    with get_session() as s:
        for nombre in cats:
            if not s.query(Categoria).filter_by(nombre=nombre).first():
                s.add(Categoria(nombre=nombre))
        s.commit()

# ── Categorías ────────────────────────────────────────────────────────────────
def get_categorias():
    with get_session() as s:
        return [c.nombre for c in s.query(Categoria).order_by(Categoria.nombre).all()]

def get_categoria_id(nombre):
    with get_session() as s:
        return s.query(Categoria).filter_by(nombre=nombre).first().id

# ── Productos ─────────────────────────────────────────────────────────────────
def get_productos(buscar=""):
    with get_session() as s:
        q = s.query(Producto, Categoria).join(Categoria)
        if buscar:
            q = q.filter(
                Producto.nombre.ilike(f"%{buscar}%") |
                Producto.variante.ilike(f"%{buscar}%") |
                Categoria.nombre.ilike(f"%{buscar}%")
            )
        rows = q.order_by(Categoria.nombre, Producto.nombre, Producto.variante).all()
        return [{"id": p.id, "cat": c.nombre, "nombre": p.nombre,
                 "variante": p.variante, "precio": p.precio,
                 "stock": p.stock, "tipo": p.tipo}
                for p, c in rows]

def get_productos_en_stock(buscar=""):
    with get_session() as s:
        q = s.query(Producto).filter(
            (Producto.stock > 0) | (Producto.tipo == "Servicio")
        )
        if buscar:
            q = q.filter(
                Producto.nombre.ilike(f"%{buscar}%") |
                Producto.variante.ilike(f"%{buscar}%")
            )
        return [{"id": p.id, "nombre": p.nombre, "variante": p.variante,
                 "precio": p.precio, "stock": p.stock, "tipo": p.tipo}
                for p in q.order_by(Producto.nombre, Producto.variante).all()]

def get_producto(pid):
    with get_session() as s:
        p = s.get(Producto, pid)
        c = s.get(Categoria, p.categoria_id)
        return {"id": p.id, "nombre": p.nombre, "variante": p.variante,
                "precio": p.precio, "stock": p.stock, "tipo": p.tipo,
                "categoria_id": p.categoria_id, "cat": c.nombre}

def crear_producto(cat_nombre, nombre, variante, tipo, precio, stock):
    with get_session() as s:
        cat = s.query(Categoria).filter_by(nombre=cat_nombre).first()
        s.add(Producto(categoria_id=cat.id, nombre=nombre, variante=variante,
                       tipo=tipo, precio=precio, stock=stock))
        s.commit()

def editar_producto(pid, cat_nombre, nombre, variante, tipo, precio):
    with get_session() as s:
        cat = s.query(Categoria).filter_by(nombre=cat_nombre).first()
        p   = s.get(Producto, pid)
        p.categoria_id = cat.id
        p.nombre       = nombre
        p.variante     = variante
        p.tipo         = tipo
        p.precio       = precio
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
def registrar_venta(fecha, total, items):
    """items = [{"producto_id", "cantidad", "precio_unit", "subtotal", "tipo"}, ...]"""
    with get_session() as s:
        venta = Venta(fecha=fecha, total=total)
        s.add(venta)
        s.flush()
        for it in items:
            s.add(DetalleVenta(
                venta_id    = venta.id,
                producto_id = it["producto_id"],
                cantidad    = it["cantidad"],
                precio_unit = it["precio_unit"],
                subtotal    = it["subtotal"]))
            # solo descuenta stock si es Producto
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
            resumen = ", ".join(
                f"{p.nombre} {p.variante}".strip() + f" x{d.cantidad}"
                for d, p in detalles)
            result.append({"id": v.id, "fecha": v.fecha,
                            "total": v.total, "resumen": resumen})
        return result

def get_detalle_venta(venta_id):
    with get_session() as s:
        rows = (s.query(DetalleVenta, Producto)
                  .join(Producto)
                  .filter(DetalleVenta.venta_id == venta_id).all())
        return [{"prod": f"{p.nombre} {p.variante}".strip(),
                 "cantidad": d.cantidad, "precio_unit": d.precio_unit,
                 "subtotal": d.subtotal}
                for d, p in rows]

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
        return [{"nombre": p.nombre, "variante": p.variante,
                 "stock": p.stock, "cat": c.nombre}
                for p, c in rows]