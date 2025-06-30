import datetime
from flask import session
import mysql.connector
from mysql.connector import Error

# ---------------------- CONEXIÓN A LA BASE DE DATOS ----------------------

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='ugel'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error de conexión: {e}")
    return None

# ------------------------- USUARIOS -------------------------

def insertar_usuario(nombre, apellido, dni, telefono, correo, institucion, clave):
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor()
            sql = '''
                INSERT INTO usuarios 
                (nombre, apellido, dni, telefono, correo_electronico, institucion, clave)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(sql, (nombre, apellido, dni, telefono, correo, institucion, clave))
            conexion.commit()
            cursor.close()
            conexion.close()
            return True
        except Error as e:
            print("⚠️ Error al insertar usuario: " + e.msg)
            return False
    else:
        print("❌ No se pudo conectar a la base de datos")
    return False


def verificar_credenciales(correo, clave):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM usuarios WHERE correo_electronico = %s AND clave = %s", 
            (correo, clave)
        )
        resultado = cursor.fetchone()
        return resultado is not None
    except mysql.connector.Error as e:
        print("Error al verificar credenciales: " + e.msg)
        return False
    finally:
        cursor.close()
        conn.close()

def obtener_datos_usuario(correo):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE correo_electronico = %s", (correo,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado

# --------------------- REGISTRO ACADÉMICO ---------------------

def guardar_registro_academico(nombre_estudiante, motivo, fecha, hora, estado, evidencia_url):
    conexion = get_db_connection()
    if conexion and 'usuario' in session:
        try:
            cursor = conexion.cursor()
            usuario_id = session['usuario'].get('id')  # ✅ Aquí usamos el ID numérico
            sql = '''
                INSERT INTO registro_academico 
                (nombre_estudiante, motivo, fecha, hora, estado, evidencia, usuario_id )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(sql, (nombre_estudiante, motivo, fecha, hora, estado, evidencia_url, usuario_id))
            conexion.commit()
            return True
        except Error as e:
            print(f"❌ Error al guardar registro académico: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

def obtener_registros_academicos():
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM registro_academico ORDER BY fecha_registro DESC")
            resultados = cursor.fetchall()
            return resultados
        except Error as e:
            print(f"❌ Error al obtener registros académicos: {e}")
        finally:
            cursor.close()
            conexion.close()
    return []

# --------------------- REGISTRO INFRAESTRUCTURA ---------------------
# Guarda un nuevo incidente de infraestructura
from datetime import datetime
from flask import session

def guardar_registro_infraestructura(problema, descripcion_problema, imagen_url, seguimiento, estado, tipo):
    conexion = get_db_connection()
    if conexion and 'usuario' in session:
        try:
            cursor = conexion.cursor()
            usuario_id = session['usuario'].get('id')  # Asegúrate de que 'id' está en la sesión
            fecha_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Fecha actual

            sql = '''
                INSERT INTO registro_infraestructura 
                (problema, descripcion_problema, imagen_problema, seguimiento, estado, fecha_registro, usuario_id, tipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            valores = (
                problema,
                descripcion_problema,
                imagen_url,
                seguimiento,
                estado,
                fecha_registro,
                usuario_id,
                tipo
            )

            cursor.execute(sql, valores)
            conexion.commit()
            print("✅ Registro de infraestructura guardado correctamente.")
            return True
        except Exception as e:
            print(f"❌ Error al guardar registro de infraestructura: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()
    else:
        print("❌ Error: No hay conexión a la base de datos o sesión de usuario no iniciada.")
        return False


def obtener_registros_infraestructura():
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM registro_infraestructura ORDER BY fecha_registro DESC")
            resultados = cursor.fetchall()
            return resultados
        except Error as e:
            print(f"❌ Error al obtener registros de infraestructura: {e}")
        finally:
            cursor.close()
            conexion.close()
    return []

# ------------------------ DASHBOARD ------------------------

def obtener_metricas_dashboard():
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("SELECT COUNT(*) AS total FROM registro_infraestructura")
            total_infra = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) AS total FROM registro_academico")
            total_acad = cursor.fetchone()['total']

            total_incidentes = total_infra + total_acad

            cursor.execute("SELECT COUNT(*) AS resueltos FROM registro_infraestructura WHERE estado = 'Resuelto'")
            resueltos_infra = cursor.fetchone()['resueltos']

            cursor.execute("SELECT COUNT(*) AS resueltos FROM registro_academico WHERE estado = 'Resuelto'")
            resueltos_acad = cursor.fetchone()['resueltos']

            total_resueltos = resueltos_infra + resueltos_acad

            cursor.execute("SELECT COUNT(*) AS en_proceso FROM registro_infraestructura WHERE estado = 'En proceso'")
            en_proceso_infra = cursor.fetchone()['en_proceso']

            cursor.execute("SELECT COUNT(*) AS en_proceso FROM registro_academico WHERE estado = 'En proceso'")
            en_proceso_acad = cursor.fetchone()['en_proceso']

            total_en_proceso = en_proceso_infra + en_proceso_acad

            cursor.execute("SELECT COUNT(DISTINCT institucion) AS total_instituciones FROM usuarios")
            total_instituciones = cursor.fetchone()['total_instituciones']

            return {
                'total_incidentes': total_incidentes,
                'total_resueltos': total_resueltos,
                'total_en_proceso': total_en_proceso,
                'total_instituciones': total_instituciones
            }

        except Error as e:
            print(f"❌ Error al obtener métricas: {e}")
        finally:
            cursor.close()
            conexion.close()
    return {}

def obtener_ultima_incidencia():
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("SELECT id, fecha_registro FROM registro_infraestructura ORDER BY fecha_registro DESC LIMIT 1")
            infra = cursor.fetchone()

            cursor.execute("SELECT id, fecha_registro FROM registro_academico ORDER BY fecha_registro DESC LIMIT 1")
            acad = cursor.fetchone()

            if not infra and not acad:
                return None

            if infra and acad:
                return infra if infra['fecha_registro'] > acad['fecha_registro'] else acad
            return infra or acad

        except Error as e:
            print(f"❌ Error al obtener última incidencia: {e}")
        finally:
            cursor.close()
            conexion.close()
    return None

def obtener_incidencias_por_estado(estado):
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            resultados = []

            # Infraestructura
            cursor.execute("""
                SELECT u.institucion, CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                       u.correo_electronico AS correo, ri.estado,
                       'Infraestructura' AS tipo
                FROM registro_infraestructura ri
                LEFT JOIN usuarios u ON ri.usuario_id = u.id
                WHERE ri.estado = %s
            """, (estado,))
            infra = cursor.fetchall()
            for r in infra:
                r['institucion'] = r['institucion'] or 'Desconocido'
                r['registrado_por'] = r['registrado_por'] or 'Desconocido'
                r['correo'] = r['correo'] or 'Desconocido'
            resultados += infra

            # Académico
            cursor.execute("""
                SELECT u.institucion, CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                       u.correo_electronico AS correo, ra.estado,
                       'Académico' AS tipo
                FROM registro_academico ra
                LEFT JOIN usuarios u ON ra.usuario_id = u.id
                WHERE ra.estado = %s
            """, (estado,))
            acad = cursor.fetchall()
            for r in acad:
                r['institucion'] = r['institucion'] or 'Desconocido'
                r['registrado_por'] = r['registrado_por'] or 'Desconocido'
                r['correo'] = r['correo'] or 'Desconocido'
            resultados += acad

            return resultados
        except Exception as e:
            print(f"❌ Error al obtener incidencias por estado: {e}")
        finally:
            cursor.close()
            conexion.close()
    return []
def obtener_todos_los_usuarios():
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios")
            resultados = cursor.fetchall()
            return resultados
        except Error as e:
            print("❌ Error al obtener usuarios: " + e.msg)
        finally:
            cursor.close()
            conexion.close()
    return []
def obtener_usuario_por_id(usuario_id):
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    
    sql = "SELECT * FROM usuarios WHERE id = %s"
    cursor.execute(sql, (usuario_id,))
    usuario = cursor.fetchone()

    cursor.close()
    conexion.close()
    
    return usuario

def eliminar_usuario_por_id(usuario_id):
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
            conexion.commit()
            return True
        except Error as e:
            print(f"❌ Error al eliminar usuario con ID {usuario_id}: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()
    else:
        print("❌ Error de conexión al intentar eliminar usuario")
        return False

def obtener_instituciones():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT institucion FROM usuarios WHERE institucion IS NOT NULL AND institucion != ''")
        resultados = cursor.fetchall()
        return resultados
    except Exception as e:
        print("Error al obtener instituciones: " + e.msg)
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_registros_filtrados_por_institucion(institucion):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if institucion:
        query = """
        SELECT 
            r.nombre_estudiante,
            r.motivo,
            r.fecha,
            r.hora,
            r.estado,
            u.institucion,
            r.evidencia
        FROM registro_academico r
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE u.institucion = %s
        """
        cursor.execute(query, (institucion,))
    else:
        query = """
        SELECT 
            r.nombre_estudiante,
            r.motivo,
            r.fecha,
            r.hora,
            r.estado,
            u.institucion,
            r.evidencia
        FROM registro_academico r
        JOIN usuarios u ON r.usuario_id = u.id
        """
        cursor.execute(query)

    resultados = cursor.fetchall()
    conn.close()
    return resultados

def actualizar_usuario_por_id(usuario_id, nombre, apellido, dni, telefono, correo, institucion, clave):
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor()
            sql = '''
                UPDATE usuarios 
                SET nombre = %s, apellido = %s, dni = %s, telefono = %s, 
                    correo_electronico = %s, institucion = %s, clave = %s
                WHERE id = %s
            '''
            cursor.execute(sql, (nombre, apellido, dni, telefono, correo, institucion, clave, usuario_id))
            conexion.commit()
            return True
        except Error as e:
            print(f"❌ Error al actualizar usuario con ID {usuario_id}: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()
    else:
        print("❌ Error de conexión al intentar actualizar usuario")
        return False
def obtener_incidente_por_nombre(tipo, nombre_institucion):
    conexion = get_db_connection()
    if not conexion:
        return None

    try:
        cursor = conexion.cursor(dictionary=True)

        if tipo.lower() in ['académico', 'academico']:
            query = """
                SELECT 
                    u.institucion, 
                    CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                    u.correo_electronico AS correo, 
                    u.telefono AS telefono,
                    ra.estado, 
                    'Académico' AS tipo,
                    ra.motivo AS descripcion
                FROM registro_academico ra
                LEFT JOIN usuarios u ON ra.usuario_id = u.id
                WHERE u.institucion = %s
                ORDER BY ra.fecha_registro DESC
                LIMIT 1
            """
        else:
            query = """
                SELECT 
                    u.institucion, 
                    CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                    u.correo_electronico AS correo, 
                    u.telefono AS telefono,
                    ri.estado, 
                    'Infraestructura' AS tipo,
                    ri.descripcion_problema AS descripcion
                FROM registro_infraestructura ri
                LEFT JOIN usuarios u ON ri.usuario_id = u.id
                WHERE u.institucion = %s
                ORDER BY ri.fecha_registro DESC
                LIMIT 1
            """

        cursor.execute(query, (nombre_institucion,))
        resultado = cursor.fetchone()
        return resultado

    except Exception as e:
        print(f"❌ Error al obtener incidente por nombre: {e}")
        return None

    finally:
        cursor.close()
        conexion.close()
def obtener_todas_las_evidencias_por_institucion(institucion=None):
    conexion = get_db_connection()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor(dictionary=True)
        resultados = []

        # Evidencias académicas
        if institucion:
            cursor.execute("""
                SELECT 
                    'Académico' AS tipo,
                    r.nombre_estudiante,
                    r.motivo,
                    r.fecha,
                    r.hora,
                    r.estado,
                    u.institucion,
                    r.evidencia
                FROM registro_academico r
                JOIN usuarios u ON r.usuario_id = u.id
                WHERE u.institucion = %s
            """, (institucion,))
        else:
            cursor.execute("""
                SELECT 
                    'Académico' AS tipo,
                    r.nombre_estudiante,
                    r.motivo,
                    r.fecha,
                    r.hora,
                    r.estado,
                    u.institucion,
                    r.evidencia
                FROM registro_academico r
                JOIN usuarios u ON r.usuario_id = u.id
            """)
        resultados += cursor.fetchall()

        # Evidencias de infraestructura
        if institucion:
            cursor.execute("""
                SELECT 
                    'Infraestructura' AS tipo,
                    '' AS nombre_estudiante,
                    r.descripcion_problema AS motivo,
                    DATE(r.fecha_registro) AS fecha,
                    TIME(r.fecha_registro) AS hora,
                    r.estado,
                    u.institucion,
                    r.imagen_problema AS evidencia
                FROM registro_infraestructura r
                JOIN usuarios u ON r.usuario_id = u.id
                WHERE u.institucion = %s
            """, (institucion,))
        else:
            cursor.execute("""
                SELECT 
                    'Infraestructura' AS tipo,
                    '' AS nombre_estudiante,
                    r.descripcion_problema AS motivo,
                    DATE(r.fecha_registro) AS fecha,
                    TIME(r.fecha_registro) AS hora,
                    r.estado,
                    u.institucion,
                    r.imagen_problema AS evidencia
                FROM registro_infraestructura r
                JOIN usuarios u ON r.usuario_id = u.id
            """)
        resultados += cursor.fetchall()

        return resultados

    except Exception as e:
        print("❌ Error al obtener todas las evidencias:", e)
        return []

    finally:
        cursor.close()
        conexion.close()
def actualizar_incidencia_por_nombre(institucion, tipo, estado, descripcion, correo, telefono):
    conexion = get_db_connection()
    if not conexion:
        print("❌ Error: No se pudo conectar a la base de datos")
        return False

    try:
        cursor = conexion.cursor()

        # Obtener el ID del usuario mediante el correo electrónico
        cursor.execute("SELECT id FROM usuarios WHERE correo_electronico = %s", (correo,))
        resultado = cursor.fetchone()
        if not resultado:
            print("❌ Error: No se encontró el usuario con ese correo")
            return False

        usuario_id = resultado[0]

        # Buscar el incidente más reciente por institución (vía relación con usuario_id)
        if tipo.lower() == 'infraestructura':
            cursor.execute("""
                SELECT ri.id FROM registro_infraestructura ri
                JOIN usuarios u ON ri.usuario_id = u.id
                WHERE u.institucion = %s
                ORDER BY ri.fecha_registro DESC
                LIMIT 1
            """, (institucion,))
        else:  # académico
            cursor.execute("""
                SELECT ra.id FROM registro_academico ra
                JOIN usuarios u ON ra.usuario_id = u.id
                WHERE u.institucion = %s
                ORDER BY ra.fecha_registro DESC
                LIMIT 1
            """, (institucion,))

        incidente = cursor.fetchone()
        if not incidente:
            print("❌ Error: No se encontró el incidente con esa institución")
            return False

        incidente_id = incidente[0]

        # Actualizar incidente
        if tipo.lower() == 'infraestructura':
            sql = """
                UPDATE registro_infraestructura
                SET estado = %s,
                    descripcion_problema = %s,
                    usuario_id = %s
                WHERE id = %s
            """
        else:
            sql = """
                UPDATE registro_academico
                SET estado = %s,
                    motivo = %s,
                    usuario_id = %s
                WHERE id = %s
            """

        cursor.execute(sql, (estado, descripcion, usuario_id, incidente_id))
        conexion.commit()
        print("✅ Incidente actualizado correctamente.")
        return True

    except Error as e:
        print(f"❌ Error al actualizar incidente: {e}")
        return False
def obtener_registros_infraestructura():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM registro_infraestructura ORDER BY fecha_registro DESC")
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados
   
def obtener_registros_academico(usuario_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                nombre_estudiante, motivo, fecha, hora, estado, evidencia_url
            FROM registro_academico
            WHERE usuario_id = %s
            ORDER BY fecha DESC
        """, (usuario_id,))
        return cursor.fetchall()
    except Exception as e:
        print("❌ Error al obtener registros académicos:", e)
        return []
    finally:
        cursor.close()
        conn.close()
