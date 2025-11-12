from flask import Flask, render_template, request, redirect, url_for
from models import db, Denuncia
import os
import logging
import urllib.parse as up

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la ruta base de la aplicación
basedir = os.path.abspath(os.path.dirname(__file__))

# Crear la aplicación Flask con rutas explícitas
app = Flask(__name__,
            template_folder=os.path.join(basedir, 'templates'),
            static_folder=os.path.join(basedir, 'static'))

# Determinar URL de la base de datos: usar DATABASE_URL si está definida (Postgres en Render)
raw_database_url = os.environ.get('DATABASE_URL')


def _resolve_database_url(raw_url):
    """Resolver la URL final a usar para SQLAlchemy.
    Intentamos validar la conexión a Postgres (si aplica) y percent-encode la contraseña
    cuando sea necesario. Si no está disponible o falla, devolvemos una URL SQLite local.
    """
    # Fallback SQLite local
    database_path = os.path.join(basedir, 'instance', 'denuncias.db')
    sqlite_url = f"sqlite:///{database_path}"

    if not raw_url:
        return sqlite_url

    # Normalizar prefijo
    url = raw_url
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    # Sólo intentamos validar Postgres URI
    if url.startswith('postgresql://'):
        # Intentar conectar usando psycopg2 directamente (antes de registrar SQLAlchemy)
        try:
            import psycopg2
        except Exception as e:
            logger.warning('psycopg2 no disponible localmente, usaremos SQLite fallback: %s', e)
            return sqlite_url

        # Intentar conexión directa; si falla por unicode, intentar percent-encode la contraseña
        try:
            # psycopg2 acepta el URI directamente
            conn = psycopg2.connect(url)
            conn.close()
            return url
        except Exception as first_err:
            logger.warning('Conexión directa a Postgres falló: %s', first_err)
            # Intentar percent-encode de la contraseña y reconectar
            try:
                parts = up.urlsplit(url)
                username = parts.username or ''
                password = parts.password or ''
                if password:
                    password_enc = up.quote_plus(password)
                    netloc = f"{username}:{password_enc}@{parts.hostname}"
                    if parts.port:
                        netloc += f":{parts.port}"
                    candidate = up.urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
                    conn = psycopg2.connect(candidate)
                    conn.close()
                    return candidate
            except Exception as second_err:
                logger.warning('Reintento con password encoded falló: %s', second_err)

    # Si todo lo anterior falla, usar SQLite local
    return sqlite_url


# Resolver y aplicar la URL final
database_url = _resolve_database_url(raw_database_url)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Engine options: ajustar según motor
if database_url.startswith('sqlite'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'check_same_thread': False}
    }
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

# Inicializar SQLAlchemy una sola vez con la URL final
try:
    db.init_app(app)
    with app.app_context():
        db.create_all()
    logger.info('Base de datos inicializada correctamente usando %s', database_url.split('://', 1)[0])
except Exception as e:
    logger.exception('Error inicializando la base de datos final: %s', e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/introduccion')
def introduccion():
    return render_template('introduccion.html')

@app.route('/tips')
def tips():
    return render_template('tips.html')

@app.route('/juego')
def juego():
    return render_template('juego.html')

@app.route('/denuncias', methods=['GET', 'POST'])
def denuncias():
    if request.method == 'POST':
        nombre = request.form['nombre'] or "Anónimo"
        lugar = request.form['lugar']
        numero = Denuncia.query.count() + 1
        nueva = Denuncia(numero=numero, nombre=nombre, lugar=lugar)
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('denuncias'))
    denuncias = Denuncia.query.all()
    return render_template('denuncias.html', denuncias=denuncias)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    denuncia = Denuncia.query.get_or_404(id)
    if request.method == 'POST':
        denuncia.nombre = request.form['nombre'] or "Anónimo"
        denuncia.lugar = request.form['lugar']
        db.session.commit()
        return redirect(url_for('denuncias'))
    return render_template('editar_denuncia.html', denuncia=denuncia)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    denuncia = Denuncia.query.get_or_404(id)
    db.session.delete(denuncia)
    db.session.commit()
    return redirect(url_for('denuncias'))

if __name__ == '__main__':
    # En desarrollo, usar debug=True. En producción (Render), gunicorn maneja esto
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))