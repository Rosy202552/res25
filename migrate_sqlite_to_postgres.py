# migrate_sqlite_to_postgres.py
# Ejecutar localmente donde tengas el archivo SQLite con datos.
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- Ajusta estas rutas/valores ---
# Ruta local a tu sqlite (ejemplo Windows)
sqlite_path = os.path.abspath(os.path.join("instance", "denuncias.db"))
sqlite_url = f"sqlite:///{sqlite_path}"

# URL de destino Postgres (pon aquí la DATABASE_URL de Render)
target = os.getenv("DATABASE_URL") or "postgresql://user:pass@host:5432/dbname"
# Si la URL empieza con postgres:// la convertimos
if target.startswith("postgres://"):
    target = target.replace("postgres://", "postgresql://", 1)

print("SQLite source:", sqlite_url)
print("Postgres target:", target)

engine_src = create_engine(sqlite_url)
engine_dst = create_engine(target)

SessionSrc = sessionmaker(bind=engine_src)
SessionDst = sessionmaker(bind=engine_dst)

src = SessionSrc()
dst = SessionDst()

# Asegurar que la tabla exista en Postgres (crea una tabla simple si no existe)
create_table_sql = """
CREATE TABLE IF NOT EXISTS denuncia (
    id INTEGER PRIMARY KEY,
    numero INTEGER NOT NULL,
    nombre VARCHAR(100),
    lugar VARCHAR(200) NOT NULL
);
"""
try:
    with engine_dst.begin() as conn:
        conn.execute(text(create_table_sql))
        print("Tabla 'denuncia' verificada/creada en Postgres")
except Exception as e:
    print("Error al asegurar la tabla en Postgres:", e)
    src.close()
    dst.close()
    raise

# Lee registros desde la tabla (adapta nombre si es diferente)
rows = src.execute(text("SELECT id, numero, nombre, lugar FROM denuncia")).fetchall()

print(f"Encontradas {len(rows)} filas en sqlite")

# Inserta en Postgres; si la tabla no existe, créala primero desde la app o con SQLAlchemy
for r in rows:
    # Usamos insert ON CONFLICT DO NOTHING para evitar duplicados si ya existen
    dst.execute(text(
        "INSERT INTO denuncia (id, numero, nombre, lugar) VALUES (:id, :numero, :nombre, :lugar) "
        "ON CONFLICT (id) DO NOTHING"
    ), dict(id=r[0], numero=r[1], nombre=r[2], lugar=r[3]))
dst.commit()

src.close()
dst.close()
print("Migración completada")