import datetime
from flask import session
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------- CONEXIÓN A LA BASE DE DATOS ----------------------

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos MySQL utilizando credenciales del entorno.
    """
    try:
        connection = mysql.connector.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            port=os.getenv('DB_PORT')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error de conexión: {e}")
    return None

# ------------------------- USUARIOS -------------------------

def insertar_usuario(nombre, apellido, dni, telefono, correo, institucion, clave):
    """
    Inserta un nuevo usuario en la base de datos con los datos proporcionados.
    """
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
            return True
        except Error as e:
            print(f"Error al insertar usuario: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()
    else:
        print("No se pudo conectar a la base de datos")
    return False

def verificar_credenciales(correo, clave):
    """
    Verifica si las credenciales proporcionadas coinciden con un usuario en la base de datos.
    """
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
        print(f"Error al verificar credenciales: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def obtener_datos_usuario(correo):
    """
    Obtiene los datos de un usuario específico basado en su correo electrónico.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE correo_electronico = %s", (correo,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado

# --------------------- REGISTRO ACADÉMICO ---------------------

def guardar_registro_academico(nombre_estudiante, motivo, fecha, hora, estado, evidencia_url):
    """
    Guarda un nuevo registro académico en la base de datos asociado al usuario en sesión.
    """
    conexion = get_db_connection()
    if conexion and 'usuario' in session:
        try:
            cursor = conexion.cursor()
            usuario_id = session['usuario'].get('id')
            sql = '''
                INSERT INTO registro_academico 
                (nombre_estudiante, motivo, fecha, hora, estado, evidencia, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(sql, (nombre_estudiante, motivo, fecha, hora, estado, evidencia_url, usuario_id))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al guardar registro académico: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

def obtener_registros_academicos():
    """
    Recupera todos los registros académicos ordenados por fecha de registro en orden descendente.
    """
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM registro_academico ORDER BY fecha_registro DESC")
            resultados = cursor.fetchall()
            return resultados
        except Error as e:
            print(f"Error al obtener registros académicos: {e}")
        finally:
            cursor.close()
            conexion.close()
    return []

# --------------------- REGISTRO INFRAESTRUCTURA ---------------------

def guardar_registro_infraestructura(problema, descripcion_problema, imagen_url, estado, tipo):
    """
    Registra un nuevo incidente de infraestructura en la base de datos con la fecha actual.
    """
    conexion = get_db_connection()
    if conexion and 'usuario' in session:
        try:
            cursor = conexion.cursor()
            usuario_id = session['usuario'].get('id')
            fecha_registro = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = '''
                INSERT INTO registro_infraestructura 
                (problema, descripcion_problema, imagen_problema, estado, fecha_registro, usuario_id, tipo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            valores = (problema, descripcion_problema, imagen_url, estado, fecha_registro, usuario_id, tipo)
            cursor.execute(sql, valores)
            conexion.commit()
            return True
        except Exception as e:
            print(f"Error al guardar registro de infraestructura: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()
    else:
        print("Error: No hay conexión a la base de datos o sesión de usuario no iniciada.")
        return False

def obtener_registros_infraestructura():
    """
    Recupera todos los registros de infraestructura ordenados por fecha de registro en orden descendente.
    """
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM registro_infraestructura ORDER BY fecha_registro DESC")
            resultados = cursor.fetchall()
            return resultados
        except Error as e:
            print(f"Error al obtener registros de infraestructura: {e}")
        finally:
            cursor.close()
            conexion.close()
    return []

# ------------------------ DASHBOARD ------------------------

def obtener_metricas_dashboard():
    """
    Calcula y devuelve métricas generales para el dashboard, como incidentes totales y estados.
    """
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
            print(f"Error al obtener métricas: {e}")
        finally:
            cursor.close()
            conexion.close()
    return {}

def obtener_ultima_incidencia():
    """
    Obtiene la incidencia más reciente registrada, comparando registros académicos e infraestructurales.
    """
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
            print(f"Error al obtener última incidencia: {e}")
        finally:
            cursor.close()
            conexion.close()
    return None


def obtener_incidencias_por_estado(estado):
    """
    Recupera todas las incidencias (académicas e infraestructurales) filtradas por estado.
    Args:
        estado (str): Estado de los incidentes a filtrar (Pendiente, En proceso, Resuelto).
    Returns:
        list: Lista de diccionarios con los datos de los incidentes.
    """
    conexion = get_db_connection()
    if not conexion:
        # Maneja el caso en que la conexión a la BD falla
        raise Exception("No se pudo establecer conexión con la base de datos")
    
    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        resultados = []

        # Consulta para incidentes de infraestructura
        cursor.execute("""
            SELECT u.institucion, CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                   'Infraestructura' AS tipo,
                   ri.id, ri.fecha_registro AS fecha
            FROM registro_infraestructura ri
            LEFT JOIN usuarios u ON ri.usuario_id = u.id
            WHERE ri.estado = %s
        """, (estado,))
        infra = cursor.fetchall()
        for r in infra:
            r['institucion'] = r['institucion'] or 'Desconocido'
            r['registrado_por'] = r['registrado_por'] or 'Desconocido'
        resultados += infra

        # Consulta para incidentes académicos
        cursor.execute("""
            SELECT u.institucion, CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                   'Académico' AS tipo, ra.id, ra.fecha_registro AS fecha
            FROM registro_academico ra
            LEFT JOIN usuarios u ON ra.usuario_id = u.id
            WHERE ra.estado = %s
        """, (estado,))
        acad = cursor.fetchall()
        for r in acad:
            r['institucion'] = r['institucion'] or 'Desconocido'
            r['registrado_por'] = r['registrado_por'] or 'Desconocido'
        resultados += acad

        return resultados
    
    except Exception as e:
        # Propaga la excepción con un mensaje detallado
        raise Exception(f"Error al obtener incidencias por estado: {str(e)}")
    
    finally:
        # Cierra el cursor y la conexión si existen
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def obtener_todos_los_usuarios():
    """
    Recupera la lista completa de usuarios registrados en la base de datos.
    """
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios")
            resultados = cursor.fetchall()
            return resultados
        except Error as e:
            print(f"Error al obtener usuarios: {e}")
        finally:
            cursor.close()
            conexion.close()
    return []

def obtener_usuario_por_id(usuario_id):
    """
    Obtiene los datos de un usuario específico basado en su ID.
    """
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)
    sql = "SELECT * FROM usuarios WHERE id = %s"
    cursor.execute(sql, (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conexion.close()
    return usuario

def eliminar_usuario_por_id(usuario_id):
    """
    Elimina un usuario de la base de datos utilizando su ID.
    """
    conexion = get_db_connection()
    if conexion:
        try:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al eliminar usuario con ID {usuario_id}: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()
    else:
        print("Error de conexión al intentar eliminar usuario")
        return False

def obtener_instituciones():
    """
    Recupera una lista de instituciones únicas registradas por los usuarios.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT institucion FROM usuarios WHERE institucion IS NOT NULL AND institucion != ''")
        resultados = cursor.fetchall()
        return resultados
    except Exception as e:
        print(f"Error al obtener instituciones: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_registros_filtrados_por_institucion(institucion):
    """
    Obtiene registros académicos filtrados por institución o todos si no se especifica institución.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if institucion:
        query = """
        SELECT 
            r.nombre_estudiante, r.motivo, r.fecha, r.hora, r.estado, u.institucion, r.evidencia
        FROM registro_academico r
        JOIN usuarios u ON r.usuario_id = u.id
        WHERE u.institucion = %s
        """
        cursor.execute(query, (institucion,))
    else:
        query = """
        SELECT 
            r.nombre_estudiante, r.motivo, r.fecha, r.hora, r.estado, u.institucion, r.evidencia
        FROM registro_academico r
        JOIN usuarios u ON r.usuario_id = u.id
        """
        cursor.execute(query)
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def actualizar_usuario_por_id(usuario_id, nombre, apellido, dni, telefono, correo, institucion, clave):
    """
    Actualiza los datos de un usuario existente en la base de datos según su ID.
    """
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
            print(f"Error al actualizar usuario con ID {usuario_id}: {e}")
            return False
        finally:
            cursor.close()
            conexion.close()
    else:
        print("Error de conexión al intentar actualizar usuario")
        return False

def obtener_incidente_por_nombre(tipo, nombre_institucion):
    """
    Obtiene el incidente más reciente de una institución según el tipo especificado.
    """
    conexion = get_db_connection()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor(dictionary=True)
        if tipo.lower() in ['académico', 'academico']:
            query = """
                SELECT 
                    u.institucion, CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                    u.correo_electronico AS correo, u.telefono AS telefono, ra.id, ra.estado, 
                    'Académico' AS tipo, ra.motivo AS descripcion, ra.comentarios AS comentarios
                FROM registro_academico ra
                LEFT JOIN usuarios u ON ra.usuario_id = u.id
                WHERE u.institucion = %s
                ORDER BY ra.fecha_registro DESC
                LIMIT 1
            """
        else:
            query = """
                SELECT 
                    u.institucion, CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                    u.correo_electronico AS correo, u.telefono AS telefono, ri.id, ri.estado, ri.problema, 
                    'Infraestructura' AS tipo, ri.descripcion_problema AS descripcion, ri.comentarios AS comentarios
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
        print(f"Error al obtener incidente por nombre: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

def obtener_todas_las_evidencias_por_institucion(institucion=None):
    """
    Recupera todas las evidencias (académicas e infraestructurales) filtradas por institución si se especifica.
    """
    conexion = get_db_connection()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor(dictionary=True)
        resultados = []
        if institucion:
            cursor.execute("""
                SELECT 
                    'Académico' AS tipo, r.nombre_estudiante, r.motivo, r.fecha, r.hora, r.estado, 
                    u.institucion, r.evidencia
                FROM registro_academico r
                JOIN usuarios u ON r.usuario_id = u.id
                WHERE u.institucion = %s
            """, (institucion,))
        else:
            cursor.execute("""
                SELECT 
                    'Académico' AS tipo, r.nombre_estudiante, r.motivo, r.fecha, r.hora, r.estado, 
                    u.institucion, r.evidencia
                FROM registro_academico r
                JOIN usuarios u ON r.usuario_id = u.id
            """)
        resultados += cursor.fetchall()

        if institucion:
            cursor.execute("""
                SELECT 
                    'Infraestructura' AS tipo, '' AS nombre_estudiante, r.descripcion_problema AS motivo, 
                    DATE(r.fecha_registro) AS fecha, TIME(r.fecha_registro) AS hora, r.estado, 
                    u.institucion, r.imagen_problema AS evidencia
                FROM registro_infraestructura r
                JOIN usuarios u ON r.usuario_id = u.id
                WHERE u.institucion = %s
            """, (institucion,))
        else:
            cursor.execute("""
                SELECT 
                    'Infraestructura' AS tipo, '' AS nombre_estudiante, r.descripcion_problema AS motivo, 
                    DATE(r.fecha_registro) AS fecha, TIME(r.fecha_registro) AS hora, r.estado, 
                    u.institucion, r.imagen_problema AS evidencia
                FROM registro_infraestructura r
                JOIN usuarios u ON r.usuario_id = u.id
            """)
        resultados += cursor.fetchall()
        return resultados
    except Exception as e:
        print(f"Error al obtener todas las evidencias: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

def actualizar_incidencia_por_nombre(institucion, tipo, estado, descripcion, correo, comentarios):
    """
    Actualiza el incidente más reciente de una institución según el tipo y datos proporcionados.
    """
    conexion = get_db_connection()
    if not conexion:
        print("Error: No se pudo conectar a la base de datos")
        return False
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE correo_electronico = %s", (correo,))
        resultado = cursor.fetchone()
        if not resultado:
            print("Error: No se encontró el usuario con ese correo")
            return False
        usuario_id = resultado[0]

        if tipo.lower() == 'infraestructura':
            cursor.execute("""
                SELECT ri.id FROM registro_infraestructura ri
                JOIN usuarios u ON ri.usuario_id = u.id
                WHERE u.institucion = %s
                ORDER BY ri.fecha_registro DESC
                LIMIT 1
            """, (institucion,))
        else:
            cursor.execute("""
                SELECT ra.id FROM registro_academico ra
                JOIN usuarios u ON ra.usuario_id = u.id
                WHERE u.institucion = %s
                ORDER BY ra.fecha_registro DESC
                LIMIT 1
            """, (institucion,))
        incidente = cursor.fetchone()
        if not incidente:
            print("Error: No se encontró el incidente con esa institución")
            return False
        incidente_id = incidente[0]

        if tipo.lower() == 'infraestructura':
            sql = """
                UPDATE registro_infraestructura
                SET estado = %s, descripcion_problema = %s, usuario_id = %s, comentarios = %s
                WHERE id = %s
            """
        else:
            sql = """
                UPDATE registro_academico
                SET estado = %s, motivo = %s, usuario_id = %s, comentarios = %s
                WHERE id = %s
            """
        cursor.execute(sql, (estado, descripcion, usuario_id, comentarios, incidente_id))
        conexion.commit()
        return True
    except Error as e:
        print(f"Error al actualizar incidente: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def actualizar_incidencia_por_id(incidente_id, tipo_incidente, estado, descripcion, motivo, correo, comentarios, tipo_problema): #    CAMBIAR TITULO OCLUMNA
    """
    Actualiza un incidente específico según su ID, tipo y datos proporcionados.
    """
    conexion = get_db_connection()
    if not conexion:
        print("Error: No se pudo conectar a la base de datos")
        return False
    try:
        cursor = conexion.cursor()

        # Obtener usuario
        cursor.execute("SELECT id FROM usuarios WHERE correo_electronico = %s", (correo,))
        resultado = cursor.fetchone()
        if not resultado:
            print("Error: No se encontró el usuario con ese correo")
            return False
        usuario_id = resultado[0]

        # Verificar existencia del incidente
        if tipo_incidente.lower() == 'infraestructura':
            cursor.execute("SELECT id FROM registro_infraestructura WHERE id = %s", (incidente_id,))
        else:
            cursor.execute("SELECT id FROM registro_academico WHERE id = %s", (incidente_id,))
        incidente = cursor.fetchone()
        if not incidente:
            print("Error: No se encontró el incidente con ese ID")
            return False

        # Actualizar incidente según el tipo
        if tipo_incidente.lower() == 'infraestructura':
            sql = """
                UPDATE registro_infraestructura
                SET estado = %s, descripcion_problema = %s, usuario_id = %s, comentarios = %s, problema = %s
                WHERE id = %s
            """
            cursor.execute(sql, (estado, descripcion, usuario_id, comentarios, tipo_problema, incidente_id))
        else:
            sql = """
                UPDATE registro_academico
                SET estado = %s, motivo = %s, usuario_id = %s, comentarios = %s
                WHERE id = %s
            """
            cursor.execute(sql, (estado, motivo, usuario_id, comentarios, incidente_id))

        conexion.commit()
        return True
    except Error as e:
        print(f"Error al actualizar incidente: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def obtener_registros_infraestructura():
    """
    Recupera todos los registros de infraestructura ordenados por fecha de registro en orden descendente.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM registro_infraestructura ORDER BY fecha_registro DESC")
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

def obtener_registros_academico(usuario_id):
    """
    Obtiene los registros académicos asociados a un usuario específico, ordenados por fecha descendente.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre_estudiante, motivo AS descripcion, fecha, hora, estado, comentarios
            FROM registro_academico
            WHERE usuario_id = %s
            ORDER BY fecha DESC
        """, (usuario_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener registros académicos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_metricas_usuario(usuario_id, conn):
    """
    Calcula las métricas de incidentes (totales, resueltos, en proceso) para un usuario específico.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM registro_infraestructura WHERE usuario_id = %s", (usuario_id,))
        infra_total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM registro_academico WHERE usuario_id = %s", (usuario_id,))
        academico_total = cursor.fetchone()[0]
        total_incidentes = infra_total + academico_total

        cursor.execute("SELECT COUNT(*) FROM registro_infraestructura WHERE estado = 'Resuelto' AND usuario_id = %s", (usuario_id,))
        infra_resueltos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM registro_academico WHERE estado = 'Resuelto' AND usuario_id = %s", (usuario_id,))
        academico_resueltos = cursor.fetchone()[0]
        resueltos = infra_resueltos + academico_resueltos

        cursor.execute("SELECT COUNT(*) FROM registro_infraestructura WHERE estado = 'En Proceso' AND usuario_id = %s", (usuario_id,))
        infra_en_proceso = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM registro_academico WHERE estado = 'En Proceso' AND usuario_id = %s", (usuario_id,))
        academico_en_proceso = cursor.fetchone()[0]
        en_proceso = infra_en_proceso + academico_en_proceso

        return {
            "total_incidentes": total_incidentes,
            "resueltos": resueltos,
            "en_proceso": en_proceso
        }
    except Error as err:
        print(f"Error al calcular métricas de usuario: {err}")
        return {"total_incidentes": 0, "resueltos": 0, "en_proceso": 0}
    finally:
        cursor.close()