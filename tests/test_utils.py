# test/test_utils.py
import pytest
from unittest.mock import patch, MagicMock
from utils import (
    get_db_connection,
    insertar_usuario,
    verificar_credenciales,
    obtener_datos_usuario,
    guardar_registro_academico,
    obtener_metricas_dashboard,
    obtener_registros_academicos,
    obtener_instituciones,
    obtener_registros_filtrados_por_institucion,
    guardar_registro_infraestructura,
    obtener_ultima_incidencia
)
from mysql.connector import Error

@pytest.fixture
def mock_db_connection():
    """
    Fixture que proporciona una conexión y cursor simulados para todas las pruebas.
    - Usa `patch` para simular `get_db_connection` y evitar conexiones reales a la base de datos.
    - Devuelve una tupla con la conexión mock y el cursor mock para ser usados en las pruebas.
    """
    with patch('utils.get_db_connection') as mock_conn:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        yield mock_connection, mock_cursor

def test_insertar_usuario_success(mock_db_connection):
    """
    Prueba la inserción exitosa de un usuario en la base de datos.
    - Usa el fixture `mock_db_connection` para simular la conexión y el cursor.
    - Llama a `insertar_usuario` con datos válidos de un usuario.
    - Verifica que:
      - La función devuelva True, indicando éxito.
      - El método `execute` del cursor se haya llamado una vez con la consulta SQL adecuada.
      - El método `commit` de la conexión se haya llamado para guardar los cambios.
    Este test asegura que el registro de usuarios funcione correctamente en condiciones normales.
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
    mock_cursor.execute.assert_called_once()  # Verifica que se ejecutó la consulta SQL
    mock_connection.commit.assert_called_once()  # Verifica que se guardaron los cambios

def test_insertar_usuario_failure_no_connection():
    """
    Prueba el fallo de `insertar_usuario` cuando no hay conexión a la base de datos.
    - Simula una conexión nula (`None`) usando `patch`.
    - Llama a `insertar_usuario` con datos válidos.
    - Verifica que la función devuelva False, indicando que no pudo realizar la inserción.
    Este test valida la robustez de la función ante fallos de conexión.
    """
    with patch('utils.get_db_connection', return_value=None):
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

def test_verificar_credenciales_success(mock_db_connection):
    """
    Prueba la verificación exitosa de credenciales de un usuario.
    - Simula la conexión y configura el cursor para devolver un registro de usuario válido.
    - Llama a `verificar_credenciales` con un correo y contraseña correctos.
    - Verifica que:
      - La función devuelva True, indicando credenciales válidas.
      - El método `execute` se haya llamado con la consulta SQL correcta y los parámetros adecuados.
    Este test asegura que la autenticación funcione correctamente cuando las credenciales son válidas.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = (1, 'Juan', 'Perez', '12345678', '987654321', 'juan@example.com', 'Colegio XYZ', '123456')

    result = verificar_credenciales('juan@example.com', '123456')
    assert result is True
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM usuarios WHERE correo_electronico = %s AND clave = %s",
        ('juan@example.com', '123456')
    )

def test_obtener_datos_usuario(mock_db_connection):
    """
    Prueba la obtención de datos de un usuario por su correo electrónico.
    - Simula la conexión y configura el cursor para devolver un diccionario con datos del usuario.
    - Llama a `obtener_datos_usuario` con un correo válido.
    - Verifica que:
      - Los datos devueltos coincidan con los esperados.
      - El método `execute` se haya llamado con la consulta SQL correcta.
    Este test valida que la función recupere correctamente la información del usuario.
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

def test_guardar_registro_academico(mock_db_connection):
    """
    Prueba el guardado exitoso de un registro académico.
    - Simula la conexión y la sesión con un usuario autenticado (id=1).
    - Llama a `guardar_registro_academico` con datos válidos de un incidente académico.
    - Verifica que:
      - La función devuelva True, indicando éxito.
      - El método `execute` del cursor se haya llamado una vez.
      - El método `commit` de la conexión se haya llamado para guardar los cambios.
    Este test asegura que los registros académicos se guarden correctamente en la base de datos.
    """
    mock_connection, mock_cursor = mock_db_connection
    with patch('utils.session', {'usuario': {'id': 1}}):
        result = guardar_registro_academico(
            nombre_estudiante='Ana Lopez',
            motivo='Falta de asistencia',
            fecha='2025-06-27',
            hora='10:00',
            estado='Pendiente',
            evidencia_url='/static/uploads/evidencia.jpg'
        )
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()

def test_obtener_metricas_dashboard(mock_db_connection):
    """
    Prueba el cálculo de métricas para el dashboard.
    - Simula la conexión y configura el cursor para devolver valores de conteo simulados.
    - Llama a `obtener_metricas_dashboard`.
    - Verifica que:
      - El resultado sea un diccionario con las métricas esperadas (suma de incidentes, resueltos, etc.).
    Este test valida que las métricas se calculen correctamente basándose en los datos de la base.
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

def test_insertar_usuario_db_error(mock_db_connection):
    """
    Prueba el fallo de insertar_usuario debido a un error de base de datos.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    
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
    mock_cursor.execute.assert_called_once()

def test_verificar_credenciales_invalid(mock_db_connection):
    """
    Prueba la verificación de credenciales inválidas.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    
    result = verificar_credenciales('juan@example.com', 'wrong_password')
    
    assert result is False
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM usuarios WHERE correo_electronico = %s AND clave = %s",
        ('juan@example.com', 'wrong_password')
    )

def test_obtener_registros_academicos(mock_db_connection):
    """
    Prueba la obtención de registros académicos.
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

def test_obtener_instituciones_error(mock_db_connection):
    """
    Prueba el manejo de errores en obtener_instituciones.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = Error("Database error")
    
    result = obtener_instituciones()
    
    assert result == []
    mock_cursor.execute.assert_called_once()

def test_guardar_registro_infraestructura_success(mock_db_connection):
    """
    Prueba el guardado exitoso de un registro de infraestructura.
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

def test_guardar_registro_infraestructura_no_session(mock_db_connection):
    """
    Prueba el guardado de infraestructura sin sesión activa.
    """
    mock_connection, mock_cursor = mock_db_connection
    with patch('utils.session', {}):
        result = guardar_registro_infraestructura(
            problema='Fuga de agua',
            descripcion_problema='Fuga en aula',
            imagen_url=None,
            seguimiento='Reportado',
            estado='Pendiente',
            tipo='off'
        )
        assert result is False

def test_obtener_ultima_incidencia_academica(mock_db_connection):
    """
    Prueba la obtención de la última incidencia (académica).
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchone.side_effect = [
        None,  # Sin resultados para infraestructura
        {'id': 2, 'fecha_registro': '2025-06-27 11:00:00'}  # Resultado para académico
    ]
    
    result = obtener_ultima_incidencia()
    
    assert result == {'id': 2, 'fecha_registro': '2025-06-27 11:00:00'}
    mock_cursor.execute.assert_any_call(
        "SELECT id, fecha_registro FROM registro_academico ORDER BY fecha_registro DESC LIMIT 1"
    )

def test_obtener_registros_filtrados_por_institucion_no_institucion(mock_db_connection):
    """
    Prueba la obtención de registros filtrados por institución sin proporcionar una institución.
    """
    mock_connection, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = []
    
    result = obtener_registros_filtrados_por_institucion(None)
    
    assert result == []
    mock_cursor.execute.assert_called_once()
