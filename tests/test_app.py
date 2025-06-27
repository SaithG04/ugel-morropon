# test/test_app.py
from flask_testing import TestCase
from app import app, get_db_connection
from unittest.mock import patch, MagicMock, ANY
from io import BytesIO
from mysql.connector import Error

class TestApp(TestCase):
    def create_app(self):
        """
        Configura la aplicación Flask para el entorno de pruebas.
        - Activa el modo de testing para deshabilitar ciertas características de producción.
        - Establece una clave secreta ficticia para las sesiones durante las pruebas.
        Retorna la instancia de la aplicación configurada.
        """
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app

    def setUp(self):
        """
        Prepara el entorno antes de cada prueba.
        - Crea un cliente de prueba para simular solicitudes HTTP.
        - Establece un contexto de aplicación para que las sesiones y otras funcionalidades funcionen.
        - Reinicia las variables globales `intentos_fallidos` y `bloqueado` en `app` para evitar interferencias entre pruebas.
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
        - Elimina el contexto de la aplicación para evitar efectos secundarios entre pruebas.
        """
        self.app_context.pop()

    @patch('app.get_db_connection')
    def test_login_success_admin(self, mock_db_connection):
        """
        Prueba el inicio de sesión exitoso para un usuario administrador.
        - Simula una conexión a la base de datos para evitar interacciones reales con ella.
        - Envía una solicitud POST al endpoint raíz ('/') con credenciales de administrador válidas.
        - Verifica que:
          - El código de estado sea 200 (éxito).
          - La respuesta contenga 'Dashboard', indicando una redirección al dashboard del administrador.
          - La sesión contenga la información del usuario administrador correctamente configurada.
        Este test asegura que la autenticación y la redirección funcionan para el administrador.
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
        - Simula la conexión a la base de datos y las funciones de autenticación y obtención de datos.
        - Configura mocks para que `verificar_credenciales` devuelva True y `obtener_datos_usuario`
          devuelva un diccionario con datos de un usuario regular.
        - Envía una solicitud POST al endpoint raíz ('/') con credenciales válidas.
        - Verifica que:
          - El código de estado sea 200.
          - La respuesta contenga 'Dashboard', indicando redirección al dashboard correspondiente.
          - La sesión contenga la información del usuario correctamente.
        Este test valida que los usuarios no administradores puedan autenticarse y acceder a su área.
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
        Prueba el comportamiento del sistema cuando un usuario está bloqueado por intentos fallidos.
        - Simula una conexión a la base de datos.
        - Modifica directamente las variables globales `intentos_fallidos` y `bloqueado` en `app`
          para simular un estado de bloqueo.
        - Envía una solicitud POST con credenciales (no importa si son correct подошелas, ya que está bloqueado).
        - Verifica que:
          - El código de estado sea 200 (la página de login se renderiza).
          - La respuesta contenga un mensaje de 'Demasiados intentos fallidos'.
        Este test asegura que el sistema maneje correctamente el bloqueo por seguridad.
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

    @patch('app.get_db_connection')
    def test_api_metricas(self, mock_db_connection):
        """
        Prueba el endpoint '/api/metricas' para obtener métricas del dashboard.
        - Simula una conexión a la base de datos y configura un cursor mock para devolver valores específicos.
        - Configura `fetchone` para devolver tuplas simulando el conteo de incidentes totales, resueltos,
          en proceso e instituciones.
        - Envía una solicitud GET al endpoint '/api/metricas'.
        - Verifica que:
          - El código de estado sea 200.
          - La respuesta JSON contenga las métricas esperadas.
        Este test asegura que las métricas se calculen y devuelvan correctamente en formato JSON.
        """
        # Simular conexión y resultados de la base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simular resultados de las consultas SQL
        mock_cursor.fetchone.side_effect = [
            (100,),  # total_incidentes
            (50,),   # resueltos
            (30,),   # en_proceso
            (10,)    # instituciones
        ]

        # Simular solicitud GET
        response = self.client.get('/api/metricas')
        
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            'total_incidentes': 100,
            'resueltos': 50,
            'en_proceso': 30,
            'instituciones': 10
        })

    def test_logout(self):
        """
        Prueba la funcionalidad de cierre de sesión en el endpoint '/logout'.
        - Configura manualmente una sesión con un usuario simulado antes de la solicitud.
        - Envía una solicitud GET a '/logout' con redirección activada.
        - Verifica que:
          - El código de estado sea 200.
          - La sesión se haya limpiado (no contenga 'usuario').
          - La respuesta contenga 'Acceso al Sistema', indicando redirección a la página de login.
        Este test asegura que el logout elimine la sesión y redirija al usuario correctamente.
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
        Prueba el guardado exitoso de un incidente académico en '/guardar_incidente'.
        - Simula una conexión a la base de datos y la función `guardar_registro_academico`.
        - Configura una sesión con un usuario no administrador.
        - Simula la función `allowed_file` para aceptar el archivo.
        - Envía una solicitud POST con datos de formulario y un archivo simulado (JPEG).
        - Verifica que:
        - El código de estado sea 302 (redirección).
        - La redirección sea a '/incidente-colegios'.
        - La sesión contenga el mensaje flash de éxito.
        - La función `guardar_registro_academico` se haya llamado con los parámetros correctos.
        - Sigue la redirección manualmente para verificar el template.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = True
        with patch('app.allowed_file', return_value=True):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'nombre_estudiante': 'Pedro Perez',
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
                print("Mensajes flash en la sesión:", flashes)
                self.assertTrue(any('Registro académico guardado exitosamente' in msg for category, msg in flashes),
                            f"Mensaje flash esperado no encontrado. Flashes: {flashes}")

            # Verificar que se llamó a guardar_registro_academico
            mock_guardar_registro.assert_called_once_with(
                'Pedro Perez',
                'Falta de asistencia',
                '2025-06-27',
                '10:00',
                'Pendiente',
                ANY
            )

            # Seguir la redirección manualmente para verificar el template
            response_redirect = self.client.get('/incidente-colegios', follow_redirects=True)
            print("Respuesta HTML tras redirección:", response_redirect.data.decode('utf-8'))
            self.assertEqual(response_redirect.status_code, 200)
            self.assertIn(b'Registrar Incidente', response_redirect.data)

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_academico')
    def test_guardar_incidente_failure(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el guardado fallido de un incidente académico en '/guardar_incidente'.
        - Simula una conexión a la base de datos y un fallo en `guardar_registro_academico`.
        - Configura una sesión con un usuario no administrador.
        - Simula la función `allowed_file` para aceptar el archivo.
        - Envía una solicitud POST con datos de formulario y un archivo simulado (JPEG).
        - Verifica que:
        - El código de estado sea 302 (redirección).
        - La redirección sea a '/incidente-colegios'.
        - La sesión contenga el mensaje flash de error.
        - La función `guardar_registro_academico` se haya llamado con los parámetros correctos.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = False
        with patch('app.allowed_file', return_value=True):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'nombre_estudiante': 'Pedro Perez',
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
                print("Mensajes flash en la sesión:", flashes)
                self.assertTrue(any('Error al guardar el registro académico' in msg for category, msg in flashes),
                            f"Mensaje flash esperado no encontrado. Flashes: {flashes}")
            
            mock_guardar_registro.assert_called_once_with(
                'Pedro Perez',
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
        Prueba el guardado de un incidente académico sin archivo en '/guardar_incidente'.
        - Simula una conexión a la base de datos y la función `guardar_registro_academico`.
        - Configura una sesión con un usuario no administrador.
        - Envía una solicitud POST con datos de formulario sin archivo.
        - Verifica que:
        - El código de estado sea 302 (redirección).
        - La redirección sea a '/incidente-colegios'.
        - La sesión contenga el mensaje flash de éxito.
        - La función `guardar_registro_academico` se haya llamado con evidencia_url=None.
        """
        mock_db_connection.return_value = MagicMock()
        mock_guardar_registro.return_value = True
        with patch('app.allowed_file', return_value=False):
            with self.client.session_transaction() as session:
                session['usuario'] = {'id': 1, 'correo': 'juan@example.com', 'nombre': 'Juan', 'apellido': 'Perez'}
            data = {
                'nombre_estudiante': 'Pedro Perez',
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
                print("Mensajes flash en la sesión:", flashes)
                self.assertTrue(any('Registro académico guardado exitosamente' in msg for category, msg in flashes),
                            f"Mensaje flash esperado no encontrado. Flashes: {flashes}")
            
            mock_guardar_registro.assert_called_once_with(
                'Pedro Perez',
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
        Prueba el guardado exitoso de un incidente de infraestructura.
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
                'Fuga de agua', 'Fuga en el baño principal', ANY, 'Enviado a mantenimiento', 'Pendiente', True
            )

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_infraestructura')
    def test_guardar_incidencia_colegios_success_with_file(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el guardado exitoso de un incidente de infraestructura con archivo.
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
                'Techo roto', 'Filtración en aula', ANY, 'Reportado', 'Pendiente', 'on'
            )

    @patch('app.get_db_connection')
    @patch('app.guardar_registro_infraestructura')
    def test_guardar_incidencia_colegios_failure(self, mock_guardar_registro, mock_db_connection):
        """
        Prueba el guardado fallido de un incidente de infraestructura.
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
        Prueba el manejo de errores en /api/incidentes cuando falla la base de datos.
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
        Prueba el endpoint /filtrar_estado con un estado inválido.
        """
        response = self.client.post('/filtrar_estado', json={'estado': 'Invalido'})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Estado inválido', response.json['error'])

    @patch('app.obtener_todos_los_usuarios')
    @patch('app.get_db_connection')
    def test_api_usuarios(self, mock_db_connection, mock_obtener_todos_los_usuarios):
        """
        Prueba el endpoint /api/usuarios para obtener todos los usuarios.
        """
        mock_db_connection.return_value = MagicMock()
        mock_obtener_todos_los_usuarios.return_value = [
            {'id': 1, 'nombre': 'Juan', 'apellido': 'Perez', 'correo_electronico': 'juan@example.com'}
        ]
        
        response = self.client.get('/api/usuarios')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [
            {'id': 1, 'nombre': 'Juan', 'apellido': 'Perez', 'correo_electronico': 'juan@example.com'}
        ])

    @patch('app.obtener_registros_filtrados_por_institucion')
    def test_api_evidencias_sin_registros(self, mock_obtener_registros):
        """
        Prueba el endpoint /api/evidencias sin registros.
        """
        mock_obtener_registros.return_value = []
        
        response = self.client.post('/api/evidencias', json={'institucion': 'Colegio XYZ'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_guardar_infraestructura_no_session(self):
        """
        Prueba el guardado de infraestructura sin sesión activa.
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