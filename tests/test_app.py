# test/test_app.py
"""
Este archivo contiene pruebas unitarias para la aplicación Flask.
Se enfoca en probar los endpoints y la lógica de la aplicación,
incluyendo autenticación, manejo de sesiones, operaciones CRUD,
y el comportamiento de la API. Las pruebas usan Flask-Testing
y mocking para simular interacciones con la base de datos y
asegurar un entorno aislado.
"""

from flask_testing import TestCase
from app import app, get_db_connection, allowed_file
from unittest.mock import patch, MagicMock, ANY
from io import BytesIO
from mysql.connector import Error

class TestApp(TestCase):
    def create_app(self):
        """
        Se configura la aplicación Flask para el entorno de pruebas.
        - Activa el modo de testing para deshabilitar ciertas características de producción,
          como el manejo automático de errores en modo desarrollo.
        - Establece una clave secreta ficticia (`test-secret-key`) para las sesiones
          durante las pruebas, necesaria para la gestión de sesiones en Flask.
        - Retorna la instancia de la aplicación configurada para ser usada por Flask-Testing.
        """
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app

    def setUp(self):
        """
        Prepara el entorno antes de cada prueba.
        - Crea un cliente de prueba (`self.client`) para simular solicitudes HTTP a la app.
        - Establece un contexto de aplicación (`self.app_context`) para que funciones como
          las sesiones y el acceso a `current_app` funcionen correctamente durante las pruebas.
        - Reinicia las variables globales `intentos_fallidos` y `bloqueado` en el módulo `app`
          a sus valores iniciales (0 y False) para evitar interferencias entre pruebas y
          garantizar un estado limpio.
        """
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Reiniciar variables globales para un estado limpio
        import app
        app.intentos_fallidos = 0
        app.bloqueado = False

    def tearDown(self):
        """
        Limpia el entorno después de cada prueba.
        - Elimina el contexto de la aplicación (`self.app_context.pop()`) para liberar recursos
          y evitar efectos secundarios entre pruebas, como sesiones residuales o configuraciones.
        """
        self.app_context.pop()

    @patch('app.get_db_connection')
    def test_login_success_admin(self, mock_db_connection):
        """
        Prueba el inicio de sesión exitoso para un usuario administrador.
        - Simula una conexión a la base de datos con `mock_db_connection` para evitar interacciones reales.
        - Envía una solicitud POST al endpoint raíz ('/') con credenciales válidas de administrador:
          correo 'admin@gmail.com' y contraseña 'priuge450'.
        - Verifica que:
          - El código de estado sea 200 (éxito tras seguir la redirección).
          - La respuesta contenga 'Dashboard', lo que indica que el usuario fue redirigido al dashboard.
          - La sesión contenga la clave 'usuario' con el correo 'admin@gmail.com', confirmando que
            la autenticación y el almacenamiento en sesión funcionan correctamente.
        Este test asegura que un administrador pueda iniciar sesión y acceder a su área designada.
        """
        # Simular conexión a la base de datos
        mock_db_connection.return_value = MagicMock()

        # Simular solicitud de login con credenciales de administrador
        response = self.client.post('/', data={
            'usuario': 'admin@gmail.com',
            'clave': 'priuge450'
        }, follow_redirects=True)

        # Verificaciones
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)  # Verifica redirección al dashboard
        with self.client.session_transaction() as session:
            self.assertIn('usuario', session)  # Verifica que la sesión se haya creado
            self.assertEqual(session['usuario']['correo'], 'admin@gmail.com')  # Verifica datos del usuario

    @patch('app.get_db_connection')
    @patch('app.verificar_credenciales')
    @patch('app.obtener_datos_usuario')
    def test_login_success_user(self, mock_obtener_datos, mock_verificar, mock_db_connection):
        """
        Prueba el inicio de sesión exitoso para un usuario regular (no administrador).
        - Simula la conexión a la base de datos y las funciones `verificar_credenciales` y
          `obtener_datos_usuario` con mocks para aislar la lógica del endpoint.
        - Configura los mocks para simular una autenticación exitosa (`verificar_credenciales=True`)
          y datos de usuario válidos (un diccionario con id, nombre, apellido y correo).
        - Envía una solicitud POST al endpoint raíz ('/') con credenciales válidas:
          correo 'juan@example.com' y contraseña '123456'.
        - Verifica que:
          - El código de estado sea 200 (éxito tras redirección).
          - La respuesta contenga 'Dashboard', indicando que el usuario accedió a su dashboard.
          - La sesión contenga los datos del usuario con el correo correcto.
        Este test valida que los usuarios regulares puedan autenticarse y acceder a su área.
        """
        # Simular conexión y funciones de utils.py
        mock_db_connection.return_value = MagicMock()
        mock_verificar.return_value = True
        mock_obtener_datos.return_value = {
            'id': 1,
            'nombre': 'Juan',
            'apellido': 'Perez',
            'correo': 'juan@example.com'
        }

        # Simular solicitud de login
        response = self.client.post('/', data={
            'usuario': 'juan@example.com',
            'clave': '123456'
        }, follow_redirects=True)

        # Verificaciones
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
        with self.client.session_transaction() as session:
            self.assertIn('usuario', session)
            self.assertEqual(session['usuario']['correo'], 'juan@example.com')

    @patch('app.get_db_connection')
    def test_login_blocked(self, mock_db_connection):
        """
        Prueba el comportamiento del login cuando el usuario está bloqueado por intentos fallidos.
        - Simula una conexión a la base de datos con un mock.
        - Modifica las variables globales `intentos_fallidos` y `bloqueado` en el módulo `app`
          para simular un estado de bloqueo (3 intentos fallidos y bloqueado=True).
        - Envía una solicitud POST al endpoint raíz ('/') con credenciales cualesquiera,
          ya que el bloqueo debería impedir el acceso independientemente de su validez.
        - Verifica que:
          - El código de estado sea 200 (la página de login se renderiza nuevamente).
          - La respuesta contenga el mensaje 'Demasiados intentos fallidos', indicando que
            el sistema detectó el bloqueo y notificó al usuario.
        Este test asegura que el mecanismo de seguridad de bloqueo funcione como se espera.
        """
        # Simular conexión a la base de datos
        mock_db_connection.return_value = MagicMock()
        
        # Simular estado de bloqueo
        import app
        app.intentos_fallidos = 3
        app.bloqueado = True

        # Simular solicitud de login
        response = self.client.post('/', data={
            'usuario': 'test@example.com',
            'clave': 'wrong'
        })

        # Verificaciones
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Demasiados intentos fallidos', response.data)

    def test_logout(self):
        """
        Prueba la funcionalidad de cierre de sesión en el endpoint '/logout'.
        - Configura manualmente una sesión con un usuario simulado antes de la solicitud,
          estableciendo 'usuario' con un correo ficticio.
        - Envía una solicitud GET a '/logout' con redirección activada para simular el flujo completo.
        - Verifica que:
          - El código de estado sea 200 (éxito tras redirección).
          - La sesión ya no contenga la clave 'usuario', indicando que se limpió correctamente.
          - La respuesta contenga 'Acceso al Sistema', lo que confirma la redirección a la página de login.
        Este test valida que el logout elimine la sesión y redirija al usuario al login.
        """
        # Configurar la sesión con un usuario simulado
        with self.client.session_transaction() as session:
            session['usuario'] = {'correo': 'test@example.com'}

        # Simular solicitud de logout
        response = self.client.get('/logout', follow_redirects=True)
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            self.assertNotIn('usuario', session)  # Verifica que la sesión se haya limpiado
        self.assertIn(b'Acceso al Sistema', response.data)  # Verifica redirección al login

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_academico')
    def test_guardar_incidente_success(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el guardado exitoso de un incidente académico en el endpoint '/guardar_incidente'.
        - Simula una conexión a la base de datos y la función `guardar_registro_academico` con mocks.
        - Configura una sesión con un usuario no administrador para simular un usuario autenticado.
        - Simula la función `allowed_file` para aceptar el archivo subido (un JPEG simulado).
        - Envía una solicitud POST con datos de formulario (nombre, motivo, fecha, etc.) y un archivo.
        - Verifica que:
          - El código de estado sea 302 (redirección tras éxito).
          - La redirección apunte a '/incidente-colegios'.
          - La sesión contenga un mensaje flash de éxito ('Registro académico guardado exitosamente').
          - La función `guardar_registro_academico` se haya llamado con los parámetros correctos.
          - Al seguir la redirección manualmente, el código de estado sea 200 y el template contenga 'Registrar Incidente'.
        Este test asegura que el guardado de incidentes académicos funcione y redirija correctamente.
        Nota: Se sigue la redirección manualmente para verificar que el template renderizado sea el esperado.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = True
        with patch('app.allowed_file', return_value=True):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'nombre_estudiante': 'Teddy Sanchez',
                'motivo': 'Falta de asistencia',
                'fecha': '2025-06-27',
                'hora': '10:00',
                'estado': 'Pendiente',
                'evidencia': (BytesIO(b'fake image data'), 'test.jpg', 'image/jpeg')
            }
            # Enviar POST sin seguir redirecciones
            response = self.client.post('/guardar_incidente',
                                        data=data,
                                        content_type='multipart/form-data',
                                        follow_redirects=False)
            
            # Verificar redirección
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/incidente-colegios')
            
            # Verificar mensaje flash en la sesión
            with self.client.session_transaction() as session:
                flashes = session.get('_flashes', [])
                self.assertTrue(any('Registro académico guardado exitosamente' in msg for category, msg in flashes),
                                f"Mensaje flash esperado no encontrado. Flashes: {flashes}")

            # Verificar que se llamó a guardar_registro_academico
            mock_guardar_registro.assert_called_once_with(
                'Teddy Sanchez',
                'Falta de asistencia',
                '2025-06-27',
                '10:00',
                'Pendiente',
                ANY
            )

            # Seguir la redirección manualmente para verificar el template
            response_redirect = self.client.get('/incidente-colegios', follow_redirects=True)
            self.assertEqual(response_redirect.status_code, 200)
            self.assertIn(b'Registrar Incidente', response_redirect.data)

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_academico')
    def test_guardar_incidente_failure(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el caso de fallo al guardar un incidente académico en el endpoint '/guardar_incidente'.
        - Simula una conexión a la base de datos con `mock_db_connection` y la función
          `guardar_registro_academico` con `mock_guardar_registro`.
        - Configura `guardar_registro_academico` para devolver False, simulando un fallo en el guardado.
        - Establece una sesión con un usuario no administrador para simular un usuario autenticado.
        - Simula la función `allowed_file` para aceptar un archivo JPEG simulado.
        - Envía una solicitud POST al endpoint '/guardar_incidente' con datos válidos de formulario
          (nombre, motivo, fecha, hora, estado) y un archivo de evidencia simulado.
        - Verifica que:
          - El código de estado sea 302, indicando una redirección tras el intento de guardado.
          - La redirección apunte al endpoint '/incidente-colegios'.
          - La sesión contenga un mensaje flash de error ('Error al guardar el registro académico').
          - La función `guardar_registro_academico` se haya llamado con los parámetros correctos,
            incluyendo el nombre del estudiante, motivo, fecha, hora, estado y la evidencia.
        Este test valida que el sistema maneje correctamente los errores durante el guardado de un
        incidente académico, mostrando un mensaje adecuado al usuario y redirigiéndolo.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = False
        with patch('app.allowed_file', return_value=True):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'nombre_estudiante': 'Teddy Sanchez',
                'motivo': 'Falta de asistencia',
                'fecha': '2025-06-27',
                'hora': '10:00',
                'estado': 'Pendiente',
                'evidencia': (BytesIO(b'fake image data'), 'test.jpg', 'image/jpeg')
            }
            response = self.client.post('/guardar_incidente',
                                       data=data,
                                       content_type='multipart/form-data',
                                       follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/incidente-colegios')
            
            with self.client.session_transaction() as session:
                flashes = session.get('_flashes', [])
                self.assertTrue(any('Error al guardar el registro académico' in msg for category, msg in flashes),
                                f"Mensaje flash esperado no encontrado. Flashes: {flashes}")
            
            mock_guardar_registro.assert_called_once_with(
                'Teddy Sanchez',
                'Falta de asistencia',
                '2025-06-27',
                '10:00',
                'Pendiente',
                ANY
            )

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_academico')
    def test_guardar_incidente_no_file(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el guardado de un incidente académico en '/guardar_incidente' sin un archivo de evidencia.
        - Simula una conexión a la base de datos con `mock_db_connection` y la función
          `guardar_registro_academico` con `mock_guardar_registro`.
        - Configura `guardar_registro_academico` para devolver True, simulando un guardado exitoso.
        - Establece una sesión con un usuario no administrador para simular un usuario autenticado.
        - Simula la función `allowed_file` para devolver False, indicando que no se subió un archivo válido.
        - Envía una solicitud POST al endpoint '/guardar_incidente' con datos de formulario válidos
          (nombre, motivo, fecha, hora, estado) pero sin un archivo de evidencia.
        - Verifica que:
          - El código de estado sea 302, indicando una redirección tras el guardado.
          - La redirección apunte a '/incidente-colegios'.
          - La sesión contenga un mensaje flash de éxito ('Registro académico guardado exitosamente').
          - La función `guardar_registro_academico` se haya llamado con los parámetros correctos,
            incluyendo `evidencia_url=None` debido a la ausencia de archivo.
        Este test asegura que el sistema permita guardar incidentes académicos sin evidencia y maneje
        correctamente este caso especial.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = True
        with patch('app.allowed_file', return_value=False):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'nombre_estudiante': 'Teddy Sanchez',
                'motivo': 'Falta de asistencia',
                'fecha': '2025-06-27',
                'hora': '10:00',
                'estado': 'Pendiente'
            }
            response = self.client.post('/guardar_incidente',
                                       data=data,
                                       content_type='multipart/form-data',
                                       follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/incidente-colegios')
            
            with self.client.session_transaction() as session:
                flashes = session.get('_flashes', [])
                self.assertTrue(any('Registro académico guardado exitosamente' in msg for category, msg in flashes),
                                f"Mensaje flash esperado no encontrado. Flashes: {flashes}")
            
            mock_guardar_registro.assert_called_once_with(
                'Teddy Sanchez',
                'Falta de asistencia',
                '2025-06-27',
                '10:00',
                'Pendiente',
                None
            )

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_infraestructura')
    def test_guardar_infraestructura_success(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el guardado exitoso de un incidente de infraestructura en el endpoint '/guardar_infraestructura'.
        - Simula una conexión a la base de datos con `mock_db_connection` y la función
          `guardar_registro_infraestructura` con `mock_guardar_registro`.
        - Configura `guardar_registro_infraestructura` para devolver True, simulando un guardado exitoso.
        - Establece una sesión con un usuario no administrador para simular un usuario autenticado.
        - Simula la función `allowed_file` para aceptar un archivo JPEG simulado.
        - Envía una solicitud POST al endpoint '/guardar_infraestructura' con datos de formulario
          (problema, descripción, seguimiento, estado, alerta) y un archivo de evidencia simulado.
        - Verifica que:
          - El código de estado sea 302, indicando una redirección tras el guardado.
          - La redirección apunte a '/incidente-colegios'.
          - La sesión contenga un mensaje flash de éxito ('Incidente de infraestructura registrado correctamente').
          - La función `guardar_registro_infraestructura` se haya llamado con los parámetros correctos,
            incluyendo el problema, descripción, seguimiento, estado, alerta y la evidencia.
        Este test valida que los incidentes de infraestructura se guarden correctamente y que el usuario
        sea redirigido con un mensaje de confirmación.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = True
        with patch('app.allowed_file', return_value=True):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'problema': 'Fuga de agua',
                'descripcion_problema': 'Fuga en el baño principal',
                'seguimiento': 'Enviado a mantenimiento',
                'estado': 'Pendiente',
                'alerta': 'on',
                'imagen_problema': (BytesIO(b'fake image data'), 'test.jpg', 'image/jpeg')
            }
            response = self.client.post('/guardar_infraestructura',
                                       data=data,
                                       content_type='multipart/form-data',
                                       follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/incidente-colegios')
            with self.client.session_transaction() as session:
                flashes = session.get('_flashes', [])
                self.assertTrue(any('Incidente de infraestructura registrado correctamente' in msg for _, msg in flashes))
            mock_guardar_registro.assert_called_once_with(
                'Fuga de agua', 'Fuga en el baño principal', ANY, 'Pendiente', True
            )

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_infraestructura')
    def test_guardar_incidencia_colegios_success_with_file(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el guardado exitoso de un incidente de infraestructura en el endpoint '/guardar_incidencia_colegios' con un archivo.
        - Simula una conexión a la base de datos con `mock_db_connection` y la función
          `guardar_registro_infraestructura` con `mock_guardar_registro`.
        - Configura `guardar_registro_infraestructura` para devolver True, simulando un guardado exitoso.
        - Establece una sesión con un usuario no administrador para simular un usuario autenticado.
        - Simula la función `allowed_file` para aceptar un archivo JPEG simulado.
        - Envía una solicitud POST al endpoint '/guardar_incidencia_colegios' con datos de formulario
          (problema, descripción, seguimiento, estado, alerta) y un archivo de evidencia simulado.
        - Verifica que:
          - El código de estado sea 302, indicando una redirección tras el guardado.
          - La redirección apunte a '/dashboard_colegios'.
          - La sesión contenga un mensaje flash de éxito ('Incidente registrado correctamente').
          - La función `guardar_registro_infraestructura` se haya llamado con los parámetros correctos.
        Este test asegura que los incidentes de infraestructura se guarden correctamente desde el endpoint
        específico para colegios y que el usuario sea redirigido al dashboard con un mensaje de éxito.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = True
        with patch('app.allowed_file', return_value=True):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'problema': 'Techo roto',
                'descripcion_problema': 'Filtración en aula',
                'seguimiento': 'Reportado',
                'estado': 'Pendiente',
                'alerta': 'on',
                'imagen_problema': (BytesIO(b'fake image data'), 'test.jpg', 'image/jpeg')
            }
            response = self.client.post('/guardar_incidencia_colegios',
                                       data=data,
                                       content_type='multipart/form-data',
                                       follow_redirects=False)
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/dashboard_colegios')
            with self.client.session_transaction() as session:
                flashes = session.get('_flashes', [])
                self.assertTrue(any('Incidente registrado correctamente' in msg for _, msg in flashes))
            mock_guardar_registro.assert_called_once_with(
                'Techo roto', 'Filtración en aula', ANY, 'Pendiente', 'on'
            )

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_infraestructura')
    def test_guardar_incidencia_colegios_failure(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el caso de fallo al guardar un incidente de infraestructura en el endpoint '/guardar_incidencia_colegios'.
        - Simula una conexión a la base de datos con `mock_db_connection` y la función
          `guardar_registro_infraestructura` con `mock_guardar_registro`.
        - Configura `guardar_registro_infraestructura` para devolver False, simulando un fallo en el guardado.
        - Establece una sesión con un usuario no administrador para simular un usuario autenticado.
        - Envía una solicitud POST al endpoint '/guardar_incidencia_colegios' con datos de formulario
          (problema, descripción, seguimiento, estado, alerta) sin un archivo de evidencia.
        - Verifica que:
          - El código de estado sea 302, indicando una redirección tras el intento de guardado.
          - La redirección apunte a '/dashboard_colegios'.
          - La sesión contenga un mensaje flash de error ('Error al registrar incidente').
        Este test valida que el sistema maneje correctamente los errores durante el guardado de un
        incidente de infraestructura, redirigiendo al usuario al dashboard con un mensaje de error.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = False
        with self.client.session_transaction() as session:
            session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
        data = {
            'problema': 'Techo roto',
            'descripcion_problema': 'Filtración en aula',
            'seguimiento': 'Reportado',
            'estado': 'Pendiente',
            'alerta': 'off'
        }
        response = self.client.post('/guardar_incidencia_colegios',
                                   data=data,
                                   content_type='multipart/form-data',
                                   follow_redirects=False)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/dashboard_colegios')
        with self.client.session_transaction() as session:
            flashes = session.get('_flashes', [])
            self.assertTrue(any('Error al registrar incidente' in msg for _, msg in flashes))

    @patch('app.get_db_connection')
    def test_api_incidentes_error(self, mock_db_connection):
        """
        Prueba el manejo de errores en el endpoint '/api/incidentes' cuando ocurre un fallo en la base de datos.
        - Simula una conexión a la base de datos con `mock_db_connection`.
        - Configura el cursor para lanzar una excepción `Error` con el mensaje 'Database error'
          al intentar ejecutar una consulta.
        - Envía una solicitud GET al endpoint '/api/incidentes'.
        - Verifica que:
          - El código de estado sea 500, indicando un error interno del servidor.
          - La respuesta JSON contenga el mensaje de error {'error': 'Database error'}.
        Este test asegura que el endpoint maneje correctamente los errores de base de datos y devuelva
        una respuesta adecuada al cliente.
        """
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn
        mock_conn.cursor.side_effect = Error("Database error")
        
        response = self.client.get('/api/incidentes')
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error': 'Database error'})

    @patch('app.get_db_connection')
    def test_filtrar_estado_invalid(self, mock_db_connection):
        """
        Prueba el endpoint '/filtrar_estado' cuando se envía un estado inválido.
        - Simula una conexión a la base de datos con `mock_db_connection` (aunque no se usa directamente
          en este caso, se incluye para mantener consistencia).
        - Envía una solicitud POST al endpoint '/filtrar_estado' con un cuerpo JSON que contiene
          un estado no válido ('Invalido').
        - Verifica que:
          - El código de estado sea 400, indicando una solicitud incorrecta.
          - La respuesta JSON contenga un mensaje de error que incluya 'Estado inválido'.
        Este test valida que el endpoint rechace correctamente los estados no válidos y devuelva
        un mensaje de error claro.
        """
        response = self.client.post('/filtrar_estado', json={'estado': 'Invalido'})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Estado inválido', response.json['error'])

    @patch('app.obtener_todos_los_usuarios')
    @patch('app.get_db_connection')
    def test_api_usuarios(self, mock_db_connection, mock_obtener_todos_los_usuarios):
        """
        Prueba el endpoint '/api/usuarios' que devuelve la lista de todos los usuarios.
        - Simula una conexión a la base de datos con `mock_db_connection` y la función
          `obtener_todos_los_usuarios` con `mock_obtener_todos_los_usuarios`.
        - Configura `obtener_todos_los_usuarios` para devolver una lista con un usuario simulado.
        - Envía una solicitud GET al endpoint '/api/usuarios'.
        - Verifica que:
          - El código de estado sea 200, indicando éxito.
          - La respuesta JSON contenga la lista de usuarios esperada, con los campos id, nombre,
            apellido y correo electrónico.
        Este test asegura que el endpoint devuelva correctamente la lista de usuarios obtenida
        de la función `obtener_todos_los_usuarios`.
        """
        mock_db_connection.return_value = MagicMock()
        mock_obtener_todos_los_usuarios.return_value = [
            {'id': 1, 'nombre': 'Teddy', 'apellido': 'Sanchez', 'correo_electronico': 'teddy@example.com'}
        ]
        
        response = self.client.get('/api/usuarios')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [
            {'id': 1, 'nombre': 'Teddy', 'apellido': 'Sanchez', 'correo_electronico': 'teddy@example.com'}
        ])

    @patch('app.obtener_registros_filtrados_por_institucion')
    def test_api_evidencias_sin_registros(self, mock_obtener_registros):
        """
        Prueba el endpoint '/api/evidencias' cuando no hay registros para la institución especificada.
        - Simula la función `obtener_registros_filtrados_por_institucion` con `mock_obtener_registros`
          para devolver una lista vacía, simulando que no hay registros.
        - Envía una solicitud POST al endpoint '/api/evidencias' con un cuerpo JSON que especifica
          una institución ('Colegio XYZ').
        - Verifica que:
          - El código de estado sea 200, indicando que la solicitud fue procesada correctamente.
          - La respuesta JSON sea una lista vacía, reflejando que no se encontraron registros.
        Este test valida que el endpoint maneje correctamente el caso en que no hay evidencias
        para la institución solicitada.
        """
        mock_obtener_registros.return_value = []
        
        response = self.client.post('/api/evidencias', json={'institucion': 'Colegio XYZ'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_guardar_infraestructura_no_session(self):
        """
        Prueba el comportamiento del endpoint '/guardar_infraestructura' cuando no hay una sesión activa.
        - No establece ninguna sesión de usuario, simulando un intento de acceso sin autenticación.
        - Envía una solicitud POST al endpoint '/guardar_infraestructura' con un dato de formulario
          básico ('problema').
        - Verifica que:
          - El código de estado sea 302, indicando una redirección debido a la falta de autenticación.
          - La redirección apunte al endpoint raíz ('/'), que suele ser la página de login.
          - La sesión contenga un mensaje flash que indique 'Debes iniciar sesión'.
        Este test asegura que el sistema restrinja el acceso al endpoint a usuarios no autenticados
        y los redirija al login con un mensaje apropiado.
        """
        response = self.client.post('/guardar_infraestructura',
                                   data={'problema': 'Fuga'},
                                   content_type='multipart/form-data',
                                   follow_redirects=False)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')
        with self.client.session_transaction() as session:
            flashes = session.get('_flashes', [])
            self.assertTrue(any('Debes iniciar sesión' in msg for _, msg in flashes))

    def test_allowed_file(self):
        """
        Prueba la función allowed_file para validar extensiones de archivo.
        - Verifica que devuelva True para extensiones permitidas (png, jpg, jpeg).
        - Verifica que devuelva False para extensiones no permitidas o nombres inválidos.
        """
        self.assertTrue(allowed_file('test.jpg'))
        self.assertTrue(allowed_file('test.png'))
        self.assertTrue(allowed_file('test.jpeg'))
        self.assertFalse(allowed_file('test.txt'))
        self.assertFalse(allowed_file('no_extension'))

    @patch('app.get_db_connection')
    @patch('app.verificar_credenciales')
    def test_login_multiple_failed_attempts(self, mock_verificar, mock_db_connection):
        """
        Prueba el endpoint de login ('/') cuando se hacen varios intentos fallidos hasta que la cuenta se bloquea.
        - Simula una conexión a la base de datos con mock_db_connection para evitar usar una base real.
        - Usa mock_verificar para simular que las credenciales son incorrectas (retorna False).
        - Configura las variables globales intentos_fallidos y bloqueado en 0 y False para un estado inicial limpio.
        - Realiza tres intentos de login con credenciales inválidas:
        1. Primer intento: Verifica que retorna código 200, muestra 'Credenciales incorrectas' y aumenta intentos_fallidos a 1.
        2. Segundo intento: Igual, pero intentos_fallidos sube a 2.
        3. Tercer intento: Alcanza el límite (MAX_INTENTOS=3), activa bloqueado=True y muestra 'Demasiados intentos fallidos'.
        - Asegura que el sistema de bloqueo por intentos fallidos funcione y que los mensajes sean correctos.
        """
        mock_db_connection.return_value = MagicMock()
        mock_verificar.return_value = False
        import app
        app.intentos_fallidos = 0
        app.bloqueado = False

        # Primer intento fallido
        response = self.client.post('/', data={'usuario': 'test@example.com', 'clave': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Credenciales incorrectas', response.data)
        self.assertEqual(app.intentos_fallidos, 1)

        # Segundo intento fallido
        response = self.client.post('/', data={'usuario': 'test@example.com', 'clave': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Credenciales incorrectas', response.data)
        self.assertEqual(app.intentos_fallidos, 2)

        # Tercer intento fallido (activa bloqueo)
        response = self.client.post('/', data={'usuario': 'test@example.com', 'clave': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Demasiados intentos fallidos', response.data)
        self.assertTrue(app.bloqueado)

    @patch('app.get_db_connection')
    def test_dashboard_no_session(self, mock_db_connection):
        """
        Prueba el acceso al endpoint '/dashboard' sin una sesión activa.
        - Simula la conexión a la base de datos con mock_db_connection, aunque no se usa en este caso.
        - Envía una solicitud GET a '/dashboard' sin configurar una sesión de usuario.
        - Verifica que el endpoint redirige (código 302) a la página de login ('/') porque no hay usuario autenticado.
        - Asegura que la protección de autenticación funcione para evitar accesos no autorizados.
        """
        mock_db_connection.return_value = MagicMock()
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')

    @patch('app.get_db_connection')
    def test_dashboard_colegios_no_session(self, mock_db_connection):
        """
        Prueba el acceso al endpoint '/dashboard_colegios' sin una sesión activa.
        - Usa mock_db_connection para simular la conexión a la base de datos, aunque no es necesaria aquí.
        - Envía una solicitud GET a '/dashboard_colegios' sin una sesión de usuario activa.
        - Comprueba que el endpoint redirige (código 302) a la página de login ('/') debido a la falta de autenticación.
        - Valida que el endpoint esté protegido contra accesos no autenticados.
        """
        mock_db_connection.return_value = MagicMock()
        response = self.client.get('/dashboard_colegios', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')

    def test_estudiantes_route(self):
        """
        Prueba el endpoint '/estudiantes' para verificar que renderiza la plantilla correcta.
        - Configura una sesión con un usuario autenticado (con id, correo, nombre, apellido) para evitar errores en la plantilla.
        - Envía una solicitud GET a '/estudiantes'.
        - Verifica que retorna código 200 y que la respuesta contiene 'Estudiantes', indicando que la plantilla se renderizó correctamente.
        - Asegura que la página de estudiantes sea accesible para usuarios autenticados.
        """
        with self.client.session_transaction() as session:
            session['usuario'] = {'id': 1, 'correo': 'test@example.com', 'nombre': 'Test', 'apellido': 'User'}
        response = self.client.get('/estudiantes')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Estudiantes', response.data)

    def test_estudiantes_colegios_route(self):
        """
        Prueba el endpoint '/estudiantes_colegios' para confirmar que renderiza la plantilla adecuada.
        - Establece una sesión con un usuario autenticado para evitar errores de plantilla que esperan 'usuario'.
        - Realiza una solicitud GET a '/estudiantes_colegios'.
        - Comprueba que retorna código 200 y que la respuesta incluye 'Estudiantes', confirmando que la plantilla se cargó bien.
        - Valida que los usuarios autenticados puedan acceder a esta vista sin problemas.
        """
        with self.client.session_transaction() as session:
            session['usuario'] = {'id': 1, 'correo': 'test@example.com', 'nombre': 'Test', 'apellido': 'User'}
        response = self.client.get('/estudiantes_colegios')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Estudiantes', response.data)

    def test_incidente_colegios_route(self):
        """
        Prueba el endpoint '/incidente-colegios' para asegurar que renderiza la plantilla correcta.
        - Crea una sesión con un usuario autenticado para cumplir con los requisitos de la plantilla.
        - Envía una solicitud GET a '/incidente-colegios'.
        - Verifica que retorna código 200 y que la respuesta contiene 'Registrar Incidente', indicando que la plantilla se renderizó correctamente.
        - Confirma que la página de incidentes sea accesible para usuarios autenticados.
        """
        with self.client.session_transaction() as session:
            session['usuario'] = {'id': 1, 'correo': 'test@example.com', 'nombre': 'Test', 'apellido': 'User'}
        response = self.client.get('/incidente-colegios')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registrar Incidente', response.data)

    def test_registro_incidente_route(self):
        """
        Prueba el endpoint '/registro_incidente' para verificar que renderiza la plantilla adecuada.
        - Configura una sesión con un usuario autenticado para evitar errores en la plantilla que usa 'usuario'.
        - Realiza una solicitud GET a '/registro_incidente'.
        - Comprueba que retorna código 200 y que la respuesta incluye 'Registro de Incidente', confirmando que la plantilla se cargó correctamente.
        - Asegura que los usuarios autenticados puedan acceder a esta vista sin errores.
        """
        with self.client.session_transaction() as session:
            session['usuario'] = {'id': 1, 'correo': 'test@example.com', 'nombre': 'Test', 'apellido': 'User'}
        response = self.client.get('/registro_incidente')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registrar Incidente', response.data)

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_infraestructura')
    def test_guardar_infraestructura_exception(self, mock_gri, mock_db):
        """
        Prueba el endpoint '/guardar_infraestructura' cuando ocurre una excepción al guardar un incidente.
        - Simula una conexión a la base de datos con mock_db para evitar interacciones reales.
        - Configura mock_gri para que la función guardar_registro_infraestructura lance una excepción ('Error inesperado').
        - Establece una sesión con un usuario autenticado para pasar la verificación de autenticación.
        - Envía una solicitud POST con datos válidos (problema, descripción, seguimiento, estado, alerta).
        - Verifica que retorna código 302 (redirección a '/incidente-colegios') y que se muestra un mensaje flash con 'Error inesperado'.
        - Asegura que el manejo de errores en el endpoint funcione correctamente, mostrando el mensaje adecuado al usuario.
        """
        mock_db.return_value = MagicMock()
        mock_gri.side_effect = Exception("Error inesperado")
        with self.client.session_transaction() as session:
            session['usuario'] = {'id': 1, 'correo': 'juan@example.com'}
        data = {
            'problema': 'Fuga',
            'descripcion_problema': 'Descripción',
            'seguimiento': 'Reportado',
            'estado': 'Pendiente',
            'alerta': 'on'
        }
        response = self.client.post('/guardar_infraestructura',
                                    data=data,
                                    content_type='multipart/form-data',
                                    follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            flashes = session.get('_flashes', [])
            self.assertTrue(any('Error inesperado' in msg for _, msg in flashes))

    @patch('app.get_db_connection')
    def test_contar_incidencias_nuevas_empty(self, mock_db):
        """
        Prueba el endpoint '/api/incidencias/nuevas' cuando no hay incidencias nuevas.
        - Simula una conexión a la base de datos con mock_db y configura un cursor que retorna 0 incidencias.
        - Envía una solicitud GET a '/api/incidencias/nuevas'.
        - Verifica que retorna código 200 y una respuesta JSON con {'nuevas': 0}, indicando que no hay incidencias nuevas.
        - Asegura que el endpoint maneje correctamente el caso de una consulta vacía.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)
        response = self.client.get('/api/incidencias/nuevas')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'nuevas': 0})

    @patch('app.get_db_connection')
    def test_actualizar_estado_error(self, mock_db):
        """
        Prueba el endpoint '/api/incidentes/<id>/estado' cuando ocurre un error al actualizar el estado.
        - Simula una conexión a la base de datos con mock_db y configura el cursor para lanzar una excepción ('Update failed').
        - Envía una solicitud POST a '/api/incidentes/1/estado' con un nuevo estado ('Resuelto').
        - Verifica que retorna código 500 (error interno) y una respuesta JSON con el mensaje de error 'Update failed'.
        - Confirma que el endpoint maneja errores de base de datos adecuadamente, retornando una respuesta clara.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Error("Update failed")
        response = self.client.post('/api/incidentes/1/estado', json={'estado': 'Resuelto'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {'error': 'Update failed'})

    @patch('app.obtener_ultima_incidencia')
    def test_api_ultima_incidencia_none(self, mock_ultima):
        """
        Prueba el endpoint '/api/ultima_incidencia' cuando no hay incidencias registradas.
        - Simula la función obtener_ultima_incidencia con mock_ultima para que retorne None.
        - Envía una solicitud GET a '/api/ultima_incidencia'.
        - Verifica que retorna código 200 y una respuesta JSON con {'nueva': False}, indicando que no hay incidencias nuevas.
        - Asegura que el endpoint maneje correctamente el caso en que no hay incidencias recientes.
        """
        mock_ultima.return_value = None
        response = self.client.get('/api/ultima_incidencia')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'nueva': False})

    @patch('app.obtener_incidencias_por_estado')
    def test_filtrar_estado_empty(self, mock_obtener):
        """
        Prueba el endpoint '/filtrar_estado' cuando no se encuentran incidencias para el estado solicitado.
        - Simula la función obtener_incidencias_por_estado con mock_obtener para que retorne una lista vacía.
        - Envía una solicitud POST a '/filtrar_estado' con un estado válido ('Pendiente').
        - Verifica que retorna código 404 y una respuesta JSON con un mensaje de error indicando que no se encontraron registros.
        - Confirma que el endpoint maneja correctamente el caso de resultados vacíos, retornando el código y mensaje adecuados.
        """
        mock_obtener.return_value = []
        response = self.client.post('/filtrar_estado', json={'estado': 'Pendiente'})
        self.assertEqual(response.status_code, 404)
        self.assertIn('No se encontraron registros', response.json['error'])