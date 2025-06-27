"""
Este archivo contiene pruebas unitarias para las funciones de utilidades definidas en `utils.py`.
Se enfoca en probar las interacciones con la base de datos y la lógica de negocio independiente
de la aplicación Flask, como inserción de usuarios, verificación de credenciales, y obtención
de métricas o registros. Usa pytest y mocking para aislar las pruebas de la base de datos real.
"""

import pytest
from unittest.mock import patch, MagicMock
from utils import (
    get_db_connection,
    insertar_usuario,
    verificar_credenciales,
    obtener_datos_usuario,
    guardar_registro_academico,
    obtener_registros_academicos,
    guardar_registro_infraestructura,
    obtener_registros_infraestructura,
    obtener_metricas_dashboard,
    obtener_ultima_incidencia,
    obtener_incidencias_por_estado,
    obtener_todos_los_usuarios,
    obtener_usuario_por_id,
    eliminar_usuario_por_id,
    actualizar_usuario_por_id,
    obtener_instituciones,
    obtener_registros_filtrados_por_institucion,
)
from mysql.connector import Error
from datetime import datetime

@pytest.fixture
def mock_db_connection():
    """
    Fixture que proporciona una conexión y cursor simulados para todas las pruebas.
    - Usa `patch` para simular la función `get_db_connection` del módulo `utils`, evitando
      conexiones reales a la base de datos durante las pruebas.
    - Crea una conexión mock (`mock_connection`) y un cursor mock (`mock_cursor`) que serán
      retornados como una tupla para su uso en las pruebas.
    - El cursor se configura como retorno del método `cursor()` de la conexión mock.
    - Yield asegura que los mocks estén disponibles durante la prueba y se limpien después.
    """
    with patch('utils.get_db_connection') as mock_conn:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        yield mock_connection, mock_cursor

def test_get_db_connection_failure():
    """
    Prueba el fallo de `get_db_connection` cuando no se puede conectar a la base de datos.
    - Usa `patch` para simular que `mysql.connector.connect` lanza una excepción `Error`.
    - Verifica que:
      - La función devuelva None, indicando fallo en la conexión.
      - Se imprime el mensaje de error esperado (mockeado con `print`).
    """
    with patch('mysql.connector.connect', side_effect=Error("Connection failed")):
        with patch('builtins.print') as mocked_print:
            result = get_db_connection()
            assert result is None
            mocked_print.assert_called_with("Error de conexión: Connection failed")

def test_insertar_usuario_success(mock_db_connection):
    """
    Prueba la inserción exitosa de un usuario en la base de datos mediante `insertar_usuario`.
    - Usa el fixture `mock_db_connection` para simular la conexión y el cursor.
    - Llama a `insertar_usuario` con datos válidos.
    - Verifica que:
      - La función devuelva True.
      - El método `execute` del cursor se haya llamado una vez.
      - El método `commit` de la conexión se haya llamado.
    """
    mock_connection, mock_cursor = mock_db_connection
    result = insertar_usuario(
        nombre='Juan',
        apellido='Perez',
        dni='12345678',
        telefono='987654321',
        correo='juan@example.com',
        institucion='Colegio XYZ',
        clave='123456'
    )
    assert result is True
    mock_cursor.execute.assert_called_once()
    mock_connection.commit.assert_called_once()

def test_insertar_usuario_failure_no_connection():
    """
    Prueba el fallo de `insertar_usuario` cuando no hay conexión a la base de datos.
    - Usa `patch` para simular que `get_db_connection` devuelve None.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    with patch('utils.get_db_connection', return_value=None):
        with patch('builtins.print') as mocked_print:
            result = insertar_usuario(
                nombre='Juan',
                apellido='Perez',
                dni='12345678',
                telefono='987654321',
                correo='juan@example.com',
                institucion='Colegio XYZ',
                clave='123456'
            )
            assert result is False
            mocked_print.assert_called_with("❌ No se pudo conectar a la base de datos")

def test_insertar_usuario_db_error(mock_db_connection):
    """
    Prueba el fallo de `insertar_usuario` debido a un error en la base de datos.
    - Configura el cursor para lanzar una excepción `Error` al ejecutar la consulta.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = insertar_usuario(
            nombre='Juan',
            apellido='Perez',
            dni='12345678',
            telefono='987654321',
            correo='juan@example.com',
            institucion='Colegio XYZ',
            clave='123456'
        )
        assert result is False
        mocked_print.assert_called_with("⚠️ Error al insertar usuario: Database error")

def test_verificar_credenciales_success(mock_db_connection):
    """
    Prueba la verificación exitosa de credenciales.
    - Configura el cursor para devolver un registro de usuario válido.
    - Verifica que:
      - La función devuelva True.
      - El método `execute` se llame con la consulta correcta.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = (1, 'Juan', 'Perez', '12345678', '987654321', 'juan@example.com', 'Colegio XYZ', '123456')
    result = verificar_credenciales('juan@example.com', '123456')
    assert result is True
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM usuarios WHERE correo_electronico = %s AND clave = %s",
        ('juan@example.com', '123456')
    )

def test_verificar_credenciales_invalid(mock_db_connection):
    """
    Prueba la verificación de credenciales inválidas.
    - Configura el cursor para devolver None.
    - Verifica que:
      - La función devuelva False.
      - El método `execute` se llame con la consulta correcta.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    result = verificar_credenciales('juan@example.com', 'wrong_password')
    assert result is False
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM usuarios WHERE correo_electronico = %s AND clave = %s",
        ('juan@example.com', 'wrong_password')
    )

def test_verificar_credenciales_db_error(mock_db_connection):
    """
    Prueba el manejo de errores de base de datos en `verificar_credenciales`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = verificar_credenciales('juan@example.com', '123456')
        assert result is False
        mocked_print.assert_called_with("Error al verificar credenciales: Database error")

def test_obtener_datos_usuario_success(mock_db_connection):
    """
    Prueba la obtención exitosa de datos de un usuario.
    - Configura el cursor para devolver un diccionario con datos de usuario.
    - Verifica que:
      - La función devuelva los datos esperados.
      - El método `execute` se llame con la consulta correcta.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': 1,
        'nombre': 'Juan',
        'apellido': 'Perez',
        'correo_electronico': 'juan@example.com'
    }
    result = obtener_datos_usuario('juan@example.com')
    assert result == {
        'id': 1,
        'nombre': 'Juan',
        'apellido': 'Perez',
        'correo_electronico': 'juan@example.com'
    }
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM usuarios WHERE correo_electronico = %s",
        ('juan@example.com',)
    )

def test_obtener_datos_usuario_not_found(mock_db_connection):
    """
    Prueba la obtención de datos de un usuario inexistente.
    - Configura el cursor para devolver None.
    - Verifica que:
      - La función devuelva None.
      - El método `execute` se llame con la consulta correcta.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    result = obtener_datos_usuario('noexist@example.com')
    assert result is None
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM usuarios WHERE correo_electronico = %s",
        ('noexist@example.com',)
    )

def test_guardar_registro_academico_no_connection():
    """
    Prueba el fallo de `guardar_registro_academico` cuando no hay conexión.
    - Usa `patch` para simular que `get_db_connection` devuelve None.
    - Verifica que:
      - La función devuelva False.
    """
    with patch('utils.get_db_connection', return_value=None):
        result = guardar_registro_academico(
            nombre_estudiante='Ana Lopez',
            motivo='Falta de asistencia',
            fecha='2025-06-27',
            hora='10:00',
            estado='Pendiente',
            evidencia_url='/static/uploads/evidencia.jpg'
        )
        assert result is False

def test_guardar_registro_academico_no_session(mock_db_connection):
    """
    Prueba el fallo de `guardar_registro_academico` cuando no hay sesión activa.
    - Simula una sesión vacía con `patch`.
    - Verifica que:
      - La función devuelva False.
    """
    mock_connection, mock_cursor = mock_db_connection
    with patch('utils.session', {}):
        result = guardar_registro_academico(
            nombre_estudiante='Ana Lopez',
            motivo='Falta de asistencia',
            fecha='2025-06-27',
            hora='10:00',
            estado='Pendiente',
            evidencia_url='/static/uploads/evidencia.jpg'
        )
        assert result is False

def test_guardar_registro_academico_db_error(mock_db_connection):
    """
    Prueba el fallo de `guardar_registro_academico` por error de base de datos.
    - Configura el cursor para lanzar una excepción `Error`.
    - Simula una sesión activa.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('utils.session', {'usuario': {'id': 1}}):
        with patch('builtins.print') as mocked_print:
            result = guardar_registro_academico(
                nombre_estudiante='Ana Lopez',
                motivo='Falta de asistencia',
                fecha='2025-06-27',
                hora='10:00',
                estado='Pendiente',
                evidencia_url='/static/uploads/evidencia.jpg'
            )
            assert result is False
            mocked_print.assert_called_with("❌ Error al guardar registro académico: Database error")

def test_obtener_registros_academicos_success(mock_db_connection):
    """
    Prueba la obtención exitosa de registros académicos.
    - Configura el cursor para devolver una lista de registros.
    - Verifica que:
      - La función devuelva la lista esperada.
      - El método `execute` se llame con la consulta correcta.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [
        {'id': 1, 'nombre_estudiante': 'Ana', 'motivo': 'Falta', 'fecha': '2025-06-27'}
    ]
    result = obtener_registros_academicos()
    assert len(result) == 1
    assert result[0]['nombre_estudiante'] == 'Ana'
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM registro_academico ORDER BY fecha_registro DESC"
    )

def test_obtener_registros_academicos_error(mock_db_connection):
    """
    Prueba el manejo de errores en `obtener_registros_academicos`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva una lista vacía.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = obtener_registros_academicos()
        assert result == []
        mocked_print.assert_called_with("❌ Error al obtener registros académicos: Database error")

def test_guardar_registro_infraestructura_success(mock_db_connection):
    """
    Prueba el guardado exitoso de un registro de infraestructura.
    - Simula una sesión activa y configura el cursor para ejecutar la consulta.
    - Verifica que:
      - La función devuelva True.
      - El método `execute` y `commit` se llamen correctamente.
    """
    mock_connection, mock_cursor = mock_db_connection
    with patch('utils.session', {'usuario': {'id': 1}}):
        result = guardar_registro_infraestructura(
            problema='Fuga de agua',
            descripcion_problema='Fuga en aula',
            imagen_url='/static/uploads/test.jpg',
            seguimiento='Reportado',
            estado='Pendiente',
            tipo='on'
        )
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()

def test_guardar_registro_infraestructura_no_connection():
    """
    Prueba el fallo de `guardar_registro_infraestructura` cuando no hay conexión.
    - Usa `patch` para simular que `get_db_connection` devuelve None.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    with patch('utils.get_db_connection', return_value=None):
        with patch('utils.session', {'usuario': {'id': 1}}):
            with patch('builtins.print') as mocked_print:
                result = guardar_registro_infraestructura(
                    problema='Fuga de agua',
                    descripcion_problema='Fuga en aula',
                    imagen_url='/static/uploads/test.jpg',
                    seguimiento='Reportado',
                    estado='Pendiente',
                    tipo='on'
                )
                assert result is False
                mocked_print.assert_called_with("❌ Error: No hay conexión a la base de datos o sesión de usuario no iniciada.")

def test_guardar_registro_infraestructura_db_error(mock_db_connection):
    """
    Prueba el fallo de `guardar_registro_infraestructura` por error de base de datos.
    - Configura el cursor para lanzar una excepción `Error`.
    - Simula una sesión activa.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('utils.session', {'usuario': {'id': 1}}):
        with patch('builtins.print') as mocked_print:
            result = guardar_registro_infraestructura(
                problema='Fuga de agua',
                descripcion_problema='Fuga en aula',
                imagen_url='/static/uploads/test.jpg',
                seguimiento='Reportado',
                estado='Pendiente',
                tipo='on'
            )
            assert result is False
            mocked_print.assert_called_with("❌ Error al guardar registro de infraestructura: Database error")

def test_obtener_registros_infraestructura_success(mock_db_connection):
    """
    Prueba la obtención exitosa de registros de infraestructura.
    - Configura el cursor para devolver una lista de registros.
    - Verifica que:
      - La función devuelva la lista esperada.
      - El método `execute` se llame con la consulta correcta.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [
        {'id': 1, 'problema': 'Fuga', 'fecha_registro': '2025-06-27'}
    ]
    result = obtener_registros_infraestructura()
    assert len(result) == 1
    assert result[0]['problema'] == 'Fuga'
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM registro_infraestructura ORDER BY fecha_registro DESC"
    )

def test_obtener_registros_infraestructura_error(mock_db_connection):
    """
    Prueba el manejo de errores en `obtener_registros_infraestructura`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva una lista vacía.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = obtener_registros_infraestructura()
        assert result == []
        mocked_print.assert_called_with("❌ Error al obtener registros de infraestructura: Database error")

def test_obtener_metricas_dashboard_success(mock_db_connection):
    """
    Prueba el cálculo exitoso de métricas para el dashboard.
    - Configura el cursor para devolver valores simulados para todas las consultas.
    - Verifica que:
      - La función devuelva las métricas esperadas.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.side_effect = [
        {'total': 50},  # total_infra
        {'total': 30},  # total_acad
        {'resueltos': 20},  # resueltos_infra
        {'resueltos': 10},  # resueltos_acad
        {'en_proceso': 15},  # en_proceso_infra
        {'en_proceso': 5},   # en_proceso_acad
        {'total_instituciones': 8}  # total_instituciones
    ]
    result = obtener_metricas_dashboard()
    assert result == {
        'total_incidentes': 80,
        'total_resueltos': 30,
        'total_en_proceso': 20,
        'total_instituciones': 8
    }

def test_obtener_metricas_dashboard_no_connection():
    """
    Prueba el fallo de `obtener_metricas_dashboard` cuando no hay conexión.
    - Usa `patch` para simular que `get_db_connection` devuelve None.
    - Verifica que:
      - La función devuelva un diccionario vacío.
    """
    with patch('utils.get_db_connection', return_value=None):
        result = obtener_metricas_dashboard()
        assert result == {}

def test_obtener_metricas_dashboard_db_error(mock_db_connection):
    """
    Prueba el manejo de errores en `obtener_metricas_dashboard`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva un diccionario vacío.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = obtener_metricas_dashboard()
        assert result == {}
        mocked_print.assert_called_with("❌ Error al obtener métricas: Database error")

def test_obtener_ultima_incidencia_both_records(mock_db_connection):
    """
    Prueba la obtención de la última incidencia cuando hay registros de infraestructura y académicos.
    - Configura el cursor para devolver registros para ambas consultas, con la infraestructura más reciente.
    - Verifica que:
      - La función devuelva el registro de infraestructura.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.side_effect = [
        {'id': 1, 'fecha_registro': datetime(2025, 6, 27, 12, 0, 0)},  # infra
        {'id': 2, 'fecha_registro': datetime(2025, 6, 27, 11, 0, 0)}   # acad
    ]
    result = obtener_ultima_incidencia()
    assert result == {'id': 1, 'fecha_registro': datetime(2025, 6, 27, 12, 0, 0)}
    mock_cursor.execute.assert_any_call(
        "SELECT id, fecha_registro FROM registro_infraestructura ORDER BY fecha_registro DESC LIMIT 1"
    )

def test_obtener_ultima_incidencia_no_records(mock_db_connection):
    """
    Prueba la obtención de la última incidencia cuando no hay registros.
    - Configura el cursor para devolver None para ambas consultas.
    - Verifica que:
      - La función devuelva None.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.side_effect = [None, None]
    result = obtener_ultima_incidencia()
    assert result is None

def test_obtener_ultima_incidencia_error(mock_db_connection):
    """
    Prueba el manejo de errores en `obtener_ultima_incidencia`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva None.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = obtener_ultima_incidencia()
        assert result is None
        mocked_print.assert_called_with("❌ Error al obtener última incidencia: Database error")

def test_obtener_incidencias_por_estado_success(mock_db_connection):
    """
    Prueba la obtención exitosa de incidencias por estado.
    - Configura el cursor para devolver registros simulados para infraestructura y académico.
    - Verifica que:
      - La función devuelva una lista con los registros combinados.
      - Se manejen correctamente los valores nulos con 'Desconocido'.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.side_effect = [
        [{'institucion': None, 'registrado_por': 'Juan Perez', 'correo': 'juan@example.com', 'estado': 'Pendiente', 'tipo': 'Infraestructura'}],
        [{'institucion': 'Colegio XYZ', 'registrado_por': 'Ana Lopez', 'correo': None, 'estado': 'Pendiente', 'tipo': 'Académico'}]
    ]
    result = obtener_incidencias_por_estado('Pendiente')
    assert len(result) == 2
    assert result[0]['institucion'] == 'Desconocido'
    assert result[1]['correo'] == 'Desconocido'
    mock_cursor.execute.assert_any_call(
        """
                SELECT u.institucion, CONCAT(u.nombre, ' ', u.apellido) AS registrado_por,
                       u.correo_electronico AS correo, ri.estado,
                       'Infraestructura' AS tipo
                FROM registro_infraestructura ri
                LEFT JOIN usuarios u ON ri.usuario_id = u.id
                WHERE ri.estado = %s
            """,
        ('Pendiente',)
    )

def test_obtener_incidencias_por_estado_error(mock_db_connection):
    """
    Prueba el manejo de errores en `obtener_incidencias_por_estado`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva una lista vacía.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = obtener_incidencias_por_estado('Pendiente')
        assert result == []
        mocked_print.assert_called_with("❌ Error al obtener incidencias por estado: Database error")

def test_obtener_todos_los_usuarios_success(mock_db_connection):
    """
    Prueba la obtención exitosa de todos los usuarios.
    - Configura el cursor para devolver una lista de usuarios.
    - Verifica que:
      - La función devuelva la lista esperada.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [
        {'id': 1, 'nombre': 'Juan', 'apellido': 'Perez'}
    ]
    result = obtener_todos_los_usuarios()
    assert len(result) == 1
    assert result[0]['nombre'] == 'Juan'

def test_obtener_todos_los_usuarios_error(mock_db_connection):
    """
    Prueba el manejo de errores en `obtener_todos_los_usuarios`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva una lista vacía.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = obtener_todos_los_usuarios()
        assert result == []
        mocked_print.assert_called_with("❌ Error al obtener usuarios: Database error")

def test_obtener_usuario_por_id_success(mock_db_connection):
    """
    Prueba la obtención exitosa de un usuario por ID.
    - Configura el cursor para devolver un usuario.
    - Verifica que:
      - La función devuelva los datos esperados.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {'id': 1, 'nombre': 'Juan'}
    result = obtener_usuario_por_id(1)
    assert result == {'id': 1, 'nombre': 'Juan'}

def test_obtener_usuario_por_id_not_found(mock_db_connection):
    """
    Prueba la obtención de un usuario inexistente por ID.
    - Configura el cursor para devolver None.
    - Verifica que:
      - La función devuelva None.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    result = obtener_usuario_por_id(999)
    assert result is None

def test_eliminar_usuario_por_id_success(mock_db_connection):
    """
    Prueba la eliminación exitosa de un usuario por ID.
    - Configura el cursor para ejecutar la consulta sin errores.
    - Verifica que:
      - La función devuelva True.
      - El método `commit` se llame.
    """
    mock_connection, mock_cursor = mock_db_connection
    result = eliminar_usuario_por_id(1)
    assert result is True
    mock_connection.commit.assert_called_once()

def test_eliminar_usuario_por_id_no_connection():
    """
    Prueba el fallo de `eliminar_usuario_por_id` cuando no hay conexión.
    - Usa `patch` para simular que `get_db_connection` devuelve None.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    with patch('utils.get_db_connection', return_value=None):
        with patch('builtins.print') as mocked_print:
            result = eliminar_usuario_por_id(1)
            assert result is False
            mocked_print.assert_called_with("❌ Error de conexión al intentar eliminar usuario")

def test_eliminar_usuario_por_id_db_error(mock_db_connection):
    """
    Prueba el fallo de `eliminar_usuario_por_id` por error de base de datos.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = eliminar_usuario_por_id(1)
        assert result is False
        mocked_print.assert_called_with("❌ Error al eliminar usuario con ID 1: Database error")

def test_actualizar_usuario_por_id_success(mock_db_connection):
    """
    Prueba la actualización exitosa de un usuario por ID.
    - Configura el cursor para ejecutar la consulta sin errores.
    - Verifica que:
      - La función devuelva True.
      - El método `commit` se llame.
    """
    mock_connection, mock_cursor = mock_db_connection
    result = actualizar_usuario_por_id( 1,
                'Juan',
                'Perez',
                '12345678',
                '987654321',
                'juan@example.com',
                'Colegio XYZ',
                '123456')
    assert result is True
    mock_connection.commit.assert_called_once()

def test_actualizar_usuario_por_id_no_connection():
    """
    Prueba el fallo de `actualizar_usuario_por_id` cuando no hay conexión.
    - Usa `patch` para simular que `get_db_connection` devuelve None.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    with patch('utils.get_db_connection', return_value=None):
        with patch('builtins.print') as mocked_print:
            result = actualizar_usuario_por_id( 1,
                'Juan',
                'Perez',
                '12345678',
                '987654321',
                'juan@example.com',
                'Colegio XYZ',
                '123456')
            assert result is False
            mocked_print.assert_called_with("❌ Error de conexión al intentar actualizar usuario")

def test_actualizar_usuario_por_id_db_error(mock_db_connection):
    """
    Prueba el fallo de `actualizar_usuario_por_id` por error de base de datos.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva False.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = actualizar_usuario_por_id( 1,
                'Juan',
                'Perez',
                '12345678',
                '987654321',
                'juan@example.com',
                'Colegio XYZ',
                '123456')
        assert result is False
        mocked_print.assert_called_with("❌ Error al actualizar usuario con ID 1: Database error")

def test_obtener_instituciones_success(mock_db_connection):
    """
    Prueba la obtención exitosa de instituciones.
    - Configura el cursor para devolver una lista de instituciones.
    - Verifica que:
      - La función devuelva la lista esperada.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [
        {'institucion': 'Colegio XYZ'},
        {'institucion': 'Escuela ABC'}
    ]
    result = obtener_instituciones()
    assert len(result) == 2
    assert result[0]['institucion'] == 'Colegio XYZ'

def test_obtener_instituciones_error(mock_db_connection):
    """
    Prueba el manejo de errores en `obtener_instituciones`.
    - Configura el cursor para lanzar una excepción `Error`.
    - Verifica que:
      - La función devuelva una lista vacía.
      - Se imprime el mensaje de error esperado.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    with patch('builtins.print') as mocked_print:
        result = obtener_instituciones()
        assert result == []
        mocked_print.assert_called_with("Error al obtener instituciones: Database error")