from datetime import timedelta
import os
from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import mysql.connector
from utils import obtener_incidencias_por_estado
from werkzeug.exceptions import BadRequest, InternalServerError
# Funciones auxiliares necesarias

from utils import (
    insertar_usuario,
    guardar_registro_academico,
    guardar_registro_infraestructura,
    verificar_credenciales,
    obtener_metricas_dashboard,
    obtener_ultima_incidencia,
    obtener_datos_usuario,
    obtener_todos_los_usuarios,
    eliminar_usuario_por_id,
    obtener_usuario_por_id,
    actualizar_usuario_por_id,
        obtener_registros_filtrados_por_institucion  # ✅ <--- Asegúrate de tener esta línea

    
)

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_segura'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLAVE_VALIDA = "priuge450"
intentos_fallidos = 0
MAX_INTENTOS = 3
bloqueado = False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return mysql.connector.connect(
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'ugel')
    )

@app.route('/', methods=['GET', 'POST'])
def login():
    global intentos_fallidos, bloqueado
    usuario = request.form.get('usuario') if request.method == 'POST' else ""

    if request.method == 'POST':
        clave = request.form.get('clave')

        if bloqueado:
            flash("Demasiados intentos fallidos. Intente más tarde.")
            return render_template('login.html', bloqueado=True, usuario=usuario)

        if usuario == "admin@gmail.com" and clave == CLAVE_VALIDA:
            intentos_fallidos = 0
            session['usuario'] = {'nombre': 'Administrador', 'apellido': 'Principal', 'correo': 'admin@gmail.com'}
            return redirect(url_for('dashboard'))

        if verificar_credenciales(usuario, clave):
            intentos_fallidos = 0
            datos_usuario = obtener_datos_usuario(usuario)
            if datos_usuario:
                session['usuario'] = datos_usuario
                return redirect(url_for('dashboard_colegios'))

        intentos_fallidos += 1
        if intentos_fallidos >= MAX_INTENTOS:
            bloqueado = True
            flash("Demasiados intentos fallidos.")
        else:
            flash("Credenciales incorrectas.")

    return render_template('login.html', bloqueado=bloqueado, usuario=usuario)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    metricas = obtener_metricas_dashboard()
    return render_template('dashboard.html', metricas=metricas)

@app.route('/dashboard_colegios')
def dashboard_colegios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    metricas = obtener_metricas_dashboard()
    return render_template('dashboard_colegios.html', metricas=metricas)

@app.route('/api/metricas')
def api_metricas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM incidentes")
        total_incidentes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM incidentes WHERE estado = 'Resuelto'")
        resueltos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM incidentes WHERE estado = 'En Proceso'")
        en_proceso = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT institucion_id) FROM incidentes")
        instituciones = cursor.fetchone()[0]

        return jsonify({
            "total_incidentes": total_incidentes,
            "resueltos": resueltos,
            "en_proceso": en_proceso,
            "instituciones": instituciones
        })
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/registro_login_usuarios', methods=['GET', 'POST'])
def registro_login_usuarios():
    if request.method == 'POST':
        datos = {
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'dni': request.form.get('dni'),
            'telefono': request.form.get('telefono'),
            'correo': request.form.get('correo'),
            'institucion': request.form.get('institucion'),
            'clave': request.form.get('clave')
        }
        exito = insertar_usuario(**datos)
        flash('Usuario registrado exitosamente.' if exito else 'Hubo un error al registrar el usuario.', 'success' if exito else 'danger')
        return redirect(url_for('registro_login_usuarios'))
    return render_template('registro_login_usuarios.html')

@app.route('/estudiantes')
def estudiante():
    return render_template('estudiantes.html')

@app.route('/guardar_incidente', methods=['POST'])
def guardar_incidente():
    nombre = request.form.get('nombre_estudiante')
    motivo = request.form.get('motivo')
    fecha = request.form.get('fecha')
    hora = request.form.get('hora')
    estado = request.form.get('estado')
    evidencia_file = request.files.get('evidencia')
    evidencia_url = None

    if evidencia_file and allowed_file(evidencia_file.filename):
        filename = secure_filename(evidencia_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        evidencia_file.save(filepath)
        evidencia_url = '/' + filepath.replace('\\', '/')

    exito = guardar_registro_academico(nombre, motivo, fecha, hora, estado, evidencia_url)
    flash("Registro académico guardado exitosamente." if exito else "Error al guardar el registro académico.", "success" if exito else "danger")

    if 'usuario' in session and session['usuario'].get('correo') != 'admin@gmail.com':
        return redirect(url_for('incidente_colegios'))
    return redirect(url_for('estudiante'))

@app.route('/incidente-colegios')
def incidente_colegios():
    return render_template('incidente_colegios.html')

@app.route('/estudiantes_colegios')
def estudiantes_colegios():
    return render_template('estudiantes_colegios.html')

@app.route('/registro_incidente')
def registro_incidente():
    return render_template('registro_incidente.html')

@app.route('/guardar_infraestructura', methods=['POST'])
def guardar_infraestructura():
    if 'usuario' not in session:
        flash("❌ Debes iniciar sesión para registrar un incidente.", "danger")
        return redirect(url_for('login'))

    try:
        problema = request.form.get('problema')
        descripcion = request.form.get('descripcion_problema')
        seguimiento = request.form.get('seguimiento')
        estado = request.form.get('estado')
        alerta = request.form.get('alerta')
        alerta = True if alerta == "on" else False  # ✅ Interpretar checkbox
        imagen_file = request.files.get('imagen_problema')
        imagen_url = None

        print("📥 Formulario recibido:")
        print(dict(request.form))

        if imagen_file and allowed_file(imagen_file.filename):
            filename = secure_filename(imagen_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(filepath)
            imagen_url = '/' + filepath.replace('\\', '/')
            print(f"📸 Imagen guardada en: {imagen_url}")

        exito = guardar_registro_infraestructura(
            problema, descripcion, imagen_url, seguimiento, estado, alerta
        )

        if exito:
            flash("✅ Incidente de infraestructura registrado correctamente.", "success")
        else:
            flash("❌ Error al registrar el incidente. Verifica los datos y vuelve a intentarlo.", "danger")

    except Exception as e:
        print("💥 Error inesperado en guardar_infraestructura():", str(e))
        flash(f"❌ Error inesperado: {e}", "danger")

    return redirect(url_for('incidente_colegios'))

@app.route('/api/incidencias/nuevas')
def contar_incidencias_nuevas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM incidencias WHERE estado = 'nueva'")
        resultado = cursor.fetchone()
        return jsonify({'nuevas': resultado[0]})
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/incidentes")
def api_incidentes():
    cursor = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, fecha_registro AS fecha, descripcion_problema AS descripcion, seguimiento AS institucion, estado FROM registro_infraestructura ORDER BY fecha_registro DESC")
        incidentes = cursor.fetchall()
        return jsonify(incidentes)
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/incidentes/<int:id>/estado", methods=["POST"])
def actualizar_estado(id):
    nuevo_estado = request.json.get("estado")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE registro_infraestructura SET estado = %s WHERE id = %s", (nuevo_estado, id))
        conn.commit()
        return jsonify({"success": True})
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/ultima_incidencia')
def api_ultima_incidencia():
    ultima = obtener_ultima_incidencia()
    if not ultima:
        return jsonify({'nueva': False})

    ultima_vista = session.get('ultima_incidencia_vista')

    if ultima_vista != ultima['id']:
        session['ultima_incidencia_vista'] = ultima['id']
        return jsonify({'nueva': True, 'id': ultima['id'], 'fecha': ultima['fecha_registro']})
    return jsonify({'nueva': False})

@app.route('/filtrar_estado', methods=['POST'])
def filtrar_estado():
    try:
        data = request.get_json()
        if not data or 'estado' not in data:
            return jsonify({"error": "El campo 'estado' es obligatorio."}), 400

        estado = data['estado']

        # Estados válidos con tildes y mayúsculas exactos como en la BD
        estados_validos = ["Pendiente", "En proceso", "Resuelto"]
        if estado not in estados_validos:
            return jsonify({
                "error": f"Estado inválido: '{estado}'. Los válidos son: {', '.join(estados_validos)}"
            }), 400

        datos = obtener_incidencias_por_estado(estado)

        if not datos:
            return jsonify({"error": f"No se encontraron registros con estado '{estado}'"}), 404

        return jsonify(datos), 200

    except Exception as e:
        return jsonify({
            "error": "Error interno del servidor.",
            "detalle": str(e)
        }), 500

@app.route('/guardar_incidencia_colegios', methods=['POST'])
def guardar_incidencia_colegios():
    problema = request.form.get('problema')
    descripcion = request.form.get('descripcion_problema')
    seguimiento = request.form.get('seguimiento')
    estado = request.form.get('estado')
    alerta = request.form.get('alerta')
    imagen_file = request.files.get('imagen_problema')
    imagen_url = None

    if imagen_file and allowed_file(imagen_file.filename):
        filename = secure_filename(imagen_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagen_file.save(filepath)
        imagen_url = '/' + filepath.replace('\\', '/')

    exito = guardar_registro_infraestructura(problema, descripcion, imagen_url, seguimiento, estado, alerta)

    flash("Incidente registrado correctamente." if exito else "Error al registrar incidente.",
          "success" if exito else "danger")
    return redirect(url_for('dashboard_colegios'))


@app.route('/instituciones')
def instituciones_principal():
    return render_template('instituciones_principal.html')


@app.route("/api/usuarios")
def api_usuarios():
    try:
        usuarios = obtener_todos_los_usuarios()
        return jsonify(usuarios)
    except Exception as e:
        print("❌ Error en /api/usuarios:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/usuarios/<int:usuario_id>", methods=["DELETE"])
def eliminar_usuario(usuario_id):
    exito = eliminar_usuario_por_id(usuario_id)
    if exito:
        return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200
    else:
        return jsonify({"error": "No se pudo eliminar el usuario"}), 500
    
@app.route('/modal/editar_usuario/<int:id>')
def modal_editar_usuario(id):
    usuario = obtener_usuario_por_id(id)
    return render_template('modaledit_usuarios.html', usuario=usuario)


from utils import obtener_instituciones  # Asegúrate de importar correctamente
@app.route('/evidencias')
def evidencias():
    instituciones = obtener_instituciones()  # Esto debe retornar los nombres desde `usuarios`
    return render_template('evidencias.html', instituciones=instituciones)


import traceback  # AÑADE esto al inicio de tu archivo si no lo tienes

@app.route('/api/evidencias', methods=['POST'])
def api_evidencias():
    try:
        data = request.get_json()
        print("📩 JSON recibido:", data)

        institucion = data.get("institucion")
        print(f"🏫 Institución seleccionada: {institucion}")

        registros = obtener_registros_filtrados_por_institucion(institucion)

        # Convertir cualquier objeto tipo timedelta a string
        for r in registros:
            for key, value in r.items():
                if isinstance(value, timedelta):
                    r[key] = str(value)

        print(f"✅ Total registros encontrados: {len(registros)}")
        return jsonify(registros)

    except Exception as e:
        print("❌ Error en /api/evidencias:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



@app.route('/actualizar_usuario', methods=['POST'])
def actualizar_usuario():
    try:
        usuario_id = request.form['id']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        telefono = request.form['telefono']
        correo = request.form['correo_electronico']
        institucion = request.form['institucion']
        clave = request.form['clave']

        actualizado = actualizar_usuario_por_id(
            usuario_id, nombre, apellido, dni, telefono, correo, institucion, clave
        )

        return jsonify({'success': actualizado})
    except Exception as e:
        print(f"❌ Error en /actualizar_usuario: {e}")
        return jsonify({'success': False})
    
    
from utils import obtener_incidente_por_nombre
@app.route('/api/incidente_por_nombre/<tipo>/<nombre>')
def api_obtener_incidente_por_nombre(tipo, nombre):
    print(f"📡 Buscando incidente para tipo='{tipo}', nombre='{nombre}'")
    try:
        incidente = obtener_incidente_por_nombre(tipo, nombre)
        print("✅ Resultado:", incidente)
        if incidente:
            return jsonify(incidente)
        else:
            return jsonify({'error': 'No se encontró el incidente'}), 404
    except Exception as e:
        print("❌ Error al buscar incidente por nombre:", e)
        return jsonify({'error': 'Error interno del servidor'}), 500

# Esta ruta ya está bien en tu app.py, asegúrate que en tu utils.py también estés manejando correctamente el nombre con espacios.

# También puedes añadir una codificación de espacios en tu JavaScript para que la URL no se corte:
# Ejemplo: encodeURIComponent(nombre)



if __name__ == '__main__':
    app.run(debug=True, port=5000)
