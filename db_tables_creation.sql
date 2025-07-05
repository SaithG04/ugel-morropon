-- Creating the `usuarios` table
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    dni VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(20),
    correo_electronico VARCHAR(100) NOT NULL UNIQUE,
    institucion VARCHAR(100),
    clave VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Creating the `registro_academico` table
CREATE TABLE registro_academico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_estudiante VARCHAR(200) NOT NULL,
    motivo TEXT NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado ENUM('Resuelto', 'En proceso', 'Pendiente') NOT NULL,
    evidencia VARCHAR(255),
    usuario_id INT NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    comentarios TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Creating the `registro_infraestructura` table
CREATE TABLE registro_infraestructura (
    id INT AUTO_INCREMENT PRIMARY KEY,
    problema VARCHAR(200) NOT NULL,
    descripcion_problema TEXT NOT NULL,
    imagen_problema VARCHAR(255),
    seguimiento TEXT,
    estado ENUM('Resuelto', 'En proceso', 'Pendiente') NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT NOT NULL,
    tipo VARCHAR(100),
    comentarios TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Inserting a default user
INSERT INTO usuarios (nombre, apellido, dni, telefono, correo_electronico, institucion, clave)
VALUES ('Admin', 'Default', '12345678', '987654321', 'admin@gmail.com', 'UGEL Admin', 'priuge450');