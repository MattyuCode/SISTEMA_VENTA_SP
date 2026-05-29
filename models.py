from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
import pymysql
pymysql.install_as_MySQLdb()
#import psycopg2

# ── MySQL ─────────────────────────────────────────>
MYSQL_USER     = "root"
MYSQL_PASSWORD = "adminsp"
MYSQL_HOST     = "127.0.0.1"
MYSQL_PORT     = "3306"
MYSQL_DB       = "libreria"

ENGINE = create_engine(
    f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}",
    echo=False,
    pool_pre_ping=True
)


# ── SupaBase (PostgreSQL) ──────────────────────────>
#DB_USER     = "postgres.peztfdsxxhysidjfwflt"  # Tu usuario de Supabase
#DB_PASSWORD = "solucionesplus"                  # Tu contraseña
#DB_HOST     = "aws-1-us-east-2.pooler.supabase.com"
#DB_PORT     = "5432"
#DB_NAME     = "postgres"

# ✅ Connection string para PostgreSQL (NO mysql://)
#DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#ENGINE = create_engine(
#    DATABASE_URL,
#    echo=False,
#    pool_pre_ping=True,
    # ✅ Parámetros importantes para Supabase/PostgreSQL
#    connect_args={"sslmode": "require"}  # Supabase requiere SSL
#)
#SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)*/


class Base(DeclarativeBase):
    pass

class Categoria(Base):
    __tablename__ = "categorias"
    id        = Column(Integer,     primary_key=True, autoincrement=True)
    nombre    = Column(String(100), unique=True,      nullable=False)
    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = "productos"
    id           = Column(Integer,     primary_key=True, autoincrement=True)
    categoria_id = Column(Integer,     ForeignKey("categorias.id"))
    nombre       = Column(String(150), nullable=False)
    #variante     = Column(String(150), default="")
    tipo         = Column(String(20),  default="Producto")  # Producto | Servicio
    precio       = Column(Float,       nullable=False)
    stock        = Column(Integer,     default=0)
    categoria    = relationship("Categoria",    back_populates="productos")
    detalles     = relationship("DetalleVenta", back_populates="producto")
    mayoreos = relationship("ProductosMayoreo", back_populates="producto",
                                  cascade="all, delete-orphan")

class Venta(Base):
    __tablename__ = "ventas"
    id       = Column(Integer,    primary_key=True, autoincrement=True)
    fecha    = Column(String(30), nullable=False)
    total    = Column(Float,      nullable=False)
    descuento = Column(Float, default=0.0)
    detalles = relationship("DetalleVenta", back_populates="venta")

class DetalleVenta(Base):
    __tablename__ = "detalle_venta"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    venta_id    = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    nombre_venta = Column(String(200), default="")
    cantidad    = Column(Integer, nullable=False)
    precio_unit = Column(Float,   nullable=False)
    subtotal    = Column(Float,   nullable=False)
    descuento = Column(Float, default=0.0)
    venta       = relationship("Venta",    back_populates="detalles")
    producto    = relationship("Producto", back_populates="detalles")

class Observacion(Base):
    __tablename__ = "observaciones"
    id       = Column(Integer,     primary_key=True, autoincrement=True)
    fecha    = Column(String(30),  nullable=False)
    monto    = Column(Float,       nullable=False)
    concepto = Column(String(255), nullable=False)



class Fiado(Base):
    __tablename__ = "fiados"
    id         = Column(Integer,     primary_key=True, autoincrement=True)
    fecha      = Column(String(30),  nullable=False)
    cliente    = Column(String(150), nullable=False)
    total      = Column(Float,       default=0)
    estado     = Column(String(20),  default="pendiente")   # pendiente | pagado
    fecha_pago = Column(String(30),  default=None)
    notas      = Column(String(255), default="")
    items      = relationship("FiadoItem", back_populates="fiado",
                               cascade="all, delete-orphan")

class FiadoItem(Base):
    __tablename__ = "fiado_items"
    id        = Column(Integer,     primary_key=True, autoincrement=True)
    fiado_id  = Column(Integer,     ForeignKey("fiados.id"), nullable=False)
    producto  = Column(String(255), nullable=False)
    cantidad  = Column(Integer,     default=1)
    precio    = Column(Float,       nullable=False)
    subtotal  = Column(Float,       nullable=False)
    fiado     = relationship("Fiado", back_populates="items")


class ProductosMayoreo(Base):
    __tablename__ = "producto_mayoreo"
    id          = Column(Integer,     primary_key=True, autoincrement=True)
    producto_id = Column(Integer,     ForeignKey("productos.id"), nullable=False)
    nombre      = Column(String(50),  nullable=False)   # unidad, resma, caja, etc.
    precio      = Column(Float,       nullable=False)
    producto    = relationship("Producto", back_populates="mayoreos")