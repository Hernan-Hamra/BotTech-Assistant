
-- Tabla para almacenar los datos de los usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultima_conexion TIMESTAMP WITH TIME ZONE
);

-- Tabla para el catálogo de productos
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    "Codigo" VARCHAR(50) UNIQUE NOT NULL,
    "Categoria" VARCHAR(255),
    "Producto" VARCHAR(255) NOT NULL,
    "Fabricante" VARCHAR(255),
    "Nro. de Parte" VARCHAR(255),
    "Moneda" VARCHAR(10),
    "Precio sin IVA" DECIMAL(10, 2),
    "%IVA" DECIMAL(10, 2),
    "Imp. Int." DECIMAL(10, 2),
    "Precio Final U$D" DECIMAL(10, 2),
    "Stock" VARCHAR(50)
);

-- Tabla para guardar el historial de interacciones
CREATE TABLE historial_conversaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    mensaje_usuario TEXT NOT NULL,
    respuesta_ia TEXT NOT NULL,
    fecha_mensaje TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_usuario
        FOREIGN KEY(usuario_id) 
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);

-- Tabla para registrar los documentos generados (PDFs)
CREATE TABLE documentos_generados (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    tipo_documento VARCHAR(50) NOT NULL, -- 'Presupuesto', 'Proforma'
    ruta_archivo VARCHAR(1024) NOT NULL,
    referencia_externa_id VARCHAR(255),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuario
        FOREIGN KEY(usuario_id) 
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);

-- Mensaje final para confirmar que el script se ejecutó
\echo ">>> Esquema de tablas creado exitosamente en la base de datos bot_db <<<"
