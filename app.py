from flask import Flask, render_template, request, redirect, url_for
from models import db, Denuncia
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la ruta base de la aplicación
basedir = os.path.abspath(os.path.dirname(__file__))

# Crear la aplicación Flask con rutas explícitas
app = Flask(__name__,
            template_folder=os.path.join(basedir, 'templates'),
            static_folder=os.path.join(basedir, 'static'))

# Usar SQLite como base de datos predeterminada
database_url = os.environ.get('DATABASE_URL', '')
if not database_url or database_url.startswith('postgres'):
    database_url = 'sqlite:///denuncias.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'connect_args': {'timeout': 10},
}

db.init_app(app)

# Crear tablas si no existen
try:
    with app.app_context():
        db.create_all()
        logger.info("Base de datos inicializada correctamente")
except Exception as e:
    logger.error(f"Error al inicializar la base de datos: {e}")

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