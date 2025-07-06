from datetime import timedelta
import os
from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import traceback

# Importa funciones auxiliares necesarias
from utils import (
    obtener_registros_filtrados_por_institucion,
    actualizar_incidencia_por_nombre,
    obtener_incidencias_por_estado,
    obtener_registros_academico,
    obtener_registros_infraestructura,
    actualizar_incidencia_por_id,
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
    obtener_todas_las_evidencias_por_institucion,
    obtener_instituciones,
    obtener_incidente_por_nombre,
    obtener_metricas_usuario
)

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_segura'
load_dotenv()

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLAVE_VALIDA = "priuge450"
intentos_fallidos = 0
MAX_INTENTOS = 3
bloqueado = False

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos MySQL."""
    return mysql.connector.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        port=os.getenv('DB_PORT')
    )

@app.route('/', methods=['GET', 'POST'])
def login():
    """Maneja la autenticación de usuarios y administradores."""
    global intentos_fallidos, bloqueado
    usuario = request.form.get('usuario') if request.method == 'POST' else ""

    if request.method == 'POST':
        clave = request.form.get('clave')
        if bloqueado:
            flash("Demasiados intentos fallidos. Intente más tarde.", "danger")
            return render_template('login.html', bloqueado=True, usuario=usuario)

        if usuario == "admin@gmail.com" and clave == CLAVE_VALIDA:
            intentos_fallidos = 0
            session['usuario'] = {
                'nombre': 'Administrador',
                'apellido': 'Principal',
                'correo': 'admin@gmail.com',
                'id': 1
            }
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
            flash("Demasiados intentos fallidos.", "danger")
        else:
            flash("Credenciales incorrectas.", "danger")

    return render_template('login.html', bloqueado=bloqueado, usuario=usuario)

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario y redirige al login."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Muestra el dashboard para administradores con incidentes y métricas."""
    if 'usuario' not in session:
        return redirect(url_for('login'))
    incidentes = obtener_registros_infraestructura()
    metricas = obtener_metricas_dashboard()
    return render_template('dashboard.html', incidentes=incidentes, metricas=metricas)

@app.route('/dashboard_colegios')
def dashboard_colegios():
    """Muestra el dashboard para colegios con incidentes y métricas filtradas por usuario."""
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_id = session['usuario']['id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                r.id,
                u.institucion,
                r.descripcion_problema AS descripcion,
                r.estado,
                r.problema,
                r.fecha_registro AS fecha,
                u.correo_electronico AS correo,
                u.telefono AS telefono,
                r.comentarios,
                'infraestructura' AS tipo
            FROM registro_infraestructura r
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE r.usuario_id = %s
            ORDER BY r.fecha_registro DESC
        """, (usuario_id,))
        registros_infraestructura = cursor.fetchall()

        registros_academicos = obtener_registros_academico(usuario_id)
        for reg in registros_academicos:
            reg['institucion'] = session['usuario']['institucion']
            reg['correo'] = session['usuario']['correo_electronico']
            reg['telefono'] = session['usuario']['telefono']
            reg['tipo'] = 'academico'

        incidentes = registros_infraestructura + registros_academicos
        metricas = obtener_metricas_usuario(usuario_id, conn)

        return render_template('dashboard_colegios.html', incidentes=incidentes, metricas=metricas)
    except Exception as e:
        print("Error al cargar el dashboard_colegios:", e)
        return render_template('dashboard_colegios.html', incidentes=[], metricas={"total_incidentes": 0, "resueltos": 0, "en_proceso": 0})
    finally:
        conn.close()

@app.route('/api/metricas')
def api_metricas():
    """Devuelve métricas generales de incidentes en formato JSON."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM registro_infraestructura")
        infra_total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM registro_academico")
        academico_total = cursor.fetchone()[0]
        total_incidentes = infra_total + academico_total

        cursor.execute("SELECT COUNT(*) FROM registro_infraestructura WHERE estado = 'Resuelto'")
        infra_resueltos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM registro_academico WHERE estado = 'Resuelto'")
        academico_resueltos = cursor.fetchone()[0]
        resueltos = infra_resueltos + academico_resueltos

        cursor.execute("SELECT COUNT(*) FROM registro_infraestructura WHERE estado = 'En Proceso'")
        infra_en_proceso = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM registro_academico WHERE estado = 'En Proceso'")
        academico_en_proceso = cursor.fetchone()[0]
        en_proceso = infra_en_proceso + academico_en_proceso

        cursor.execute("""
            SELECT COUNT(DISTINCT u.institucion)
            FROM usuarios u
            JOIN registro_infraestructura ri ON u.id = ri.usuario_id
            UNION
            SELECT COUNT(DISTINCT u.institucion)
            FROM usuarios u
            JOIN registro_academico ra ON u.id = ra.usuario_id
        """)
        instituciones = sum(row[0] for row in cursor.fetchall())

        return jsonify({
            "total_incidentes": total_incidentes,
            "resueltos": resueltos,
            "en_proceso": en_proceso,
            "instituciones": instituciones
        })
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/metricas_usuario')
def api_metricas_usuario():
    """Devuelve métricas de incidentes específicas del usuario autenticado."""
    if 'usuario' not in session:
        return jsonify({"error": "No autenticado"}), 401
    usuario_id = session['usuario']['id']
    try:
        conn = get_db_connection()
        metricas = obtener_metricas_usuario(usuario_id, conn)
        return jsonify(metricas)
    except Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        conn.close()

@app.route('/registro_login_usuarios', methods=['GET', 'POST'])
def registro_login_usuarios():
    """Registra un nuevo usuario o muestra el formulario de registro."""
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
    """Muestra la página de gestión de estudiantes."""
    return render_template('estudiantes.html')

@app.route('/guardar_incidente', methods=['POST'])
def guardar_incidente():
    """Guarda un incidente académico con evidencia opcional."""
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
    """Muestra la página de incidentes para colegios."""
    return render_template('incidente_colegios.html')

@app.route('/estudiantes_colegios')
def estudiantes_colegios():
    """Muestra la página de estudiantes para colegios."""
    return render_template('estudiantes_colegios.html')

@app.route('/registro_incidente')
def registro_incidente():
    """Muestra la página de registro de incidentes."""
    return render_template('registro_incidente.html')

@app.route('/guardar_infraestructura', methods=['POST'])
def guardar_infraestructura():
    """Guarda un incidente de infraestructura con imagen opcional."""
    if 'usuario' not in session:
        flash("Debes iniciar sesión para registrar un incidente.", "danger")
        return redirect(url_for('login'))

    try:
        problema = request.form.get('problema')
        descripcion = request.form.get('descripcion_problema')
        estado = request.form.get('estado')
        alerta = request.form.get('alerta') == "on"
        imagen_file = request.files.get('imagen_problema')
        imagen_url = None

        if imagen_file and allowed_file(imagen_file.filename):
            filename = secure_filename(imagen_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(filepath)
            imagen_url = '/' + filepath.replace('\\', '/')

        exito = guardar_registro_infraestructura(problema, descripcion, imagen_url, estado, alerta)
        flash("Incidente de infraestructura registrado correctamente." if exito else "Error al registrar el incidente.", "success" if exito else "danger")
    except Exception as e:
        print("Error inesperado en guardar_infraestructura():", str(e))
        flash(f"Error inesperado: {e}", "danger")
    return redirect(url_for('incidente_colegios'))

@app.route('/api/incidencias/nuevas')
def contar_incidencias_nuevas():
    """Devuelve la cantidad de incidencias nuevas en formato JSON."""
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
    """Devuelve todos los incidentes de infraestructura en formato JSON."""
    conn = None
    cursor = None
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
    """Actualiza el estado de un incidente de infraestructura."""
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
    """Devuelve la última incidencia y verifica si es nueva para el usuario."""
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
    """Filtra incidentes por estado y devuelve los resultados en formato JSON."""
    try:
        data = request.get_json()
        if not data or 'estado' not in data:
            return jsonify({"error": "El campo 'estado' es obligatorio."}), 400
        estado = data['estado']
        estados_validos = ["Pendiente", "En proceso", "Resuelto"]
        if estado not in estados_validos:
            return jsonify({"error": f"Estado inválido: '{estado}'. Los válidos son: {', '.join(estados_validos)}"}), 400
        datos = obtener_incidencias_por_estado(estado)
        if not datos:
            return jsonify({"error": f"No se encontraron registros con estado '{estado}'"}), 404
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": "Error interno del servidor.", "detalle": str(e)}), 500

@app.route('/guardar_incidencia_colegios', methods=['POST'])
def guardar_incidencia_colegios():
    """Guarda un incidente de infraestructura desde el dashboard de colegios."""
    problema = request.form.get('problema')
    descripcion = request.form.get('descripcion_problema')
    estado = request.form.get('estado')
    alerta = request.form.get('alerta')
    imagen_file = request.files.get('imagen_problema')
    imagen_url = None

    if imagen_file and allowed_file(imagen_file.filename):
        filename = secure_filename(imagen_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagen_file.save(filepath)
        imagen_url = '/' + filepath.replace('\\', '/')

    exito = guardar_registro_infraestructura(problema, descripcion, imagen_url, estado, alerta)
    flash("Incidente registrado correctamente." if exito else "Error al registrar incidente.", "success" if exito else "danger")
    return redirect(url_for('dashboard_colegios'))

@app.route('/instituciones')
def instituciones_principal():
    """Muestra la página principal de instituciones."""
    return render_template('instituciones_principal.html')

@app.route("/api/usuarios")
def api_usuarios():
    """Devuelve la lista de todos los usuarios en formato JSON."""
    try:
        usuarios = obtener_todos_los_usuarios()
        return jsonify(usuarios)
    except Exception as e:
        print("Error en /api/usuarios:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/usuarios/<int:usuario_id>", methods=["DELETE"])
def eliminar_usuario(usuario_id):
    """Elimina un usuario por su ID."""
    exito = eliminar_usuario_por_id(usuario_id)
    if exito:
        return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200
    return jsonify({"error": "No se pudo eliminar el usuario"}), 500

@app.route('/modal/editar_usuario/<int:id>')
def modal_editar_usuario(id):
    """Muestra el formulario modal para editar un usuario."""
    usuario = obtener_usuario_por_id(id)
    return render_template('modaledit_usuarios.html', usuario=usuario)

@app.route('/evidencias')
def evidencias():
    """Muestra la página de evidencias con las instituciones disponibles."""
    instituciones = obtener_instituciones()
    return render_template('evidencias.html', instituciones=instituciones)

@app.route('/api/evidencias', methods=['POST'])
def api_evidencias():
    """Devuelve evidencias filtradas por institución en formato JSON."""
    try:
        data = request.get_json()
        institucion = data.get("institucion")
        registros = obtener_todas_las_evidencias_por_institucion(institucion)
        for r in registros:
            for key, value in r.items():
                if isinstance(value, timedelta):
                    r[key] = str(value)
        return jsonify(registros)
    except Exception as e:
        print("Error en /api/evidencias:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/actualizar_usuario', methods=['POST'])
def actualizar_usuario():
    """Actualiza la información de un usuario existente."""
    try:
        usuario_id = request.form['id']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        telefono = request.form['telefono']
        correo = request.form['correo_electronico']
        institucion = request.form['institucion']
        clave = request.form['clave']
        actualizado = actualizar_usuario_por_id(usuario_id, nombre, apellido, dni, telefono, correo, institucion, clave)
        return jsonify({'success': actualizado})
    except Exception as e:
        print(f"Error en /actualizar_usuario: {e}")
        return jsonify({'success': False})

@app.route('/api/incidente_por_nombre/<tipo>/<nombre>')
def api_obtener_incidente_por_nombre(tipo, nombre):
    """Obtiene un incidente por tipo y nombre en formato JSON."""
    try:
        incidente = obtener_incidente_por_nombre(tipo, nombre)
        if incidente:
            return jsonify(incidente)
        return jsonify({'error': 'No se encontró el incidente'}), 404
    except Exception as e:
        print("Error al buscar incidente por nombre:", e)
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route("/api/actualizar_incidente_por_nombre/<institucion>", methods=["PUT"])
def actualizar_incidente_por_nombre_api(institucion):
    """Actualiza un incidente por institución y datos proporcionados."""
    try:
        datos = request.get_json()
        tipo = datos.get("tipo")
        estado = datos.get("estado")
        descripcion = datos.get("descripcion")
        correo = datos.get("correo")
        telefono = datos.get("telefono")
        comentarios = datos.get("comentarios")
        if not all([tipo, estado, descripcion, correo, telefono]):
            return jsonify({"error": "Faltan datos para actualizar"}), 400
        resultado = actualizar_incidencia_por_nombre(institucion, tipo, estado, descripcion, correo, telefono, comentarios)
        if resultado:
            return jsonify({"mensaje": "Incidente actualizado correctamente"}), 200
        return jsonify({"error": "No se pudo actualizar el incidente"}), 400
    except Exception as e:
        print(f"Error en el endpoint actualizar_incidente_por_nombre: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500    
    
@app.route('/api/actualizar_incidente/<int:incidente_id>', methods=['PUT'])
def actualizar_incidencia(incidente_id):
    """
    Actualiza un incidente por su ID con los datos proporcionados, permitiendo comentarios opcionales.
    """
    try:
        data = request.get_json()
        if not data:
            print(f"Error en /api/actualizar_incidente/{incidente_id}: No se proporcionaron datos")
            return jsonify({'success': False, 'error': 'No se proporcionaron datos'}), 400

        tipo_incidente = data.get('tipo_incidente')
        estado = data.get('estado')
        descripcion = data.get('descripcion')
        motivo = data.get('motivo')
        correo = data.get('correo')
        comentarios = data.get('comentarios', '')
        tipo_problema = data.get('tipo_problema')

        # Registro de datos recibidos para depuración
        print(f"Datos recibidos para actualizar incidente {incidente_id}:")
        print(f"Tipo incidente: {tipo_incidente}")
        print(f"Estado: {estado}")
        print(f"Comentarios: {comentarios}")

        # Validar campos obligatorios
        missing_fields = []
        if not tipo_incidente:
            missing_fields.append('tipo_incidente')
        if not estado:
            missing_fields.append('estado')
        if not correo:
            missing_fields.append('correo')

        if missing_fields:
            error_msg = f"Datos incompletos. Faltan los campos: {', '.join(missing_fields)}"
            print(f"Error en /api/actualizar_incidente/{incidente_id}: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400

        actualizado = actualizar_incidencia_por_id(incidente_id, tipo_incidente, estado, descripcion, motivo, correo, comentarios, tipo_problema)
        if actualizado:
            print(f"Actualizado incidente {incidente_id} con éxito")
            return jsonify({'success': True, 'message': 'Incidente actualizado con éxito'}), 200

        print(f"Error en /api/actualizar_incidente/{incidente_id}: No se pudo actualizar el incidente")
        return jsonify({'success': False, 'error': 'No se pudo actualizar el incidente'}), 400
    except Exception as e:
        print(f"Error en /api/actualizar_incidente/{incidente_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/incidente_por_id/<int:id>/<string:tipo>', methods=['GET'])
def obtener_incidente_por_id(id, tipo):
    """Obtiene un incidente por su ID y tipo en formato JSON."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if tipo.lower() == 'infraestructura':
            cursor.execute("""
                SELECT 
                    r.id,
                    u.institucion,
                    CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                    r.descripcion_problema AS descripcion,
                    r.estado,
                    r.problema,
                    r.fecha_registro AS fecha,
                    u.correo_electronico AS correo,
                    u.telefono AS telefono,
                    r.comentarios,
                    'infraestructura' AS tipo
                FROM registro_infraestructura r
                JOIN usuarios u ON r.usuario_id = u.id
                WHERE r.id = %s
            """, (id,))
        elif tipo.lower() == 'academico':
            cursor.execute("""
                SELECT 
                    r.id,
                    u.institucion,
                    CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                    r.motivo,
                    r.estado,
                    r.nombre_estudiante,
                    r.fecha AS fecha,
                    u.correo_electronico AS correo,
                    u.telefono AS telefono,
                    r.comentarios,
                    'academico' AS tipo
                FROM registro_academico r
                JOIN usuarios u ON r.usuario_id = u.id
                WHERE r.id = %s
            """, (id,))
        else:
            return jsonify({"error": "Tipo de incidente inválido"}), 400
        incidente = cursor.fetchone()
        if incidente:
            return jsonify(incidente)
        return jsonify({"error": "Incidente no encontrado"}), 404
    except Exception as e:
        print("Error al obtener incidente por id:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    """Inicia la aplicación Flask en modo debug."""
    app.run(debug=True, port=5000)