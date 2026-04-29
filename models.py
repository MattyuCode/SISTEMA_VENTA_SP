from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship
import pymysql
pymysql.install_as_MySQLdb()

# ── Cambia estos datos por los tuyos ─────────────────────────────────────────
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
    variante     = Column(String(150), default="")
    tipo         = Column(String(20),  default="Producto")  # Producto | Servicio
    precio       = Column(Float,       nullable=False)
    stock        = Column(Integer,     default=0)
    categoria    = relationship("Categoria",    back_populates="productos")
    detalles     = relationship("DetalleVenta", back_populates="producto")

class Venta(Base):
    __tablename__ = "ventas"
    id       = Column(Integer,    primary_key=True, autoincrement=True)
    fecha    = Column(String(30), nullable=False)
    total    = Column(Float,      nullable=False)
    detalles = relationship("DetalleVenta", back_populates="venta")

class DetalleVenta(Base):
    __tablename__ = "detalle_venta"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    venta_id    = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad    = Column(Integer, nullable=False)
    precio_unit = Column(Float,   nullable=False)
    subtotal    = Column(Float,   nullable=False)
    venta       = relationship("Venta",    back_populates="detalles")
    producto    = relationship("Producto", back_populates="detalles")