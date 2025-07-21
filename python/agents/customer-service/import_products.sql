
-- Paso 1: Borrar la tabla anterior si existe, para empezar de cero.
DROP TABLE IF EXISTS productos;

-- Paso 2: Crear la tabla con la estructura aprobada.
CREATE TABLE productos (
    codigo VARCHAR(50) PRIMARY KEY,
    categoria VARCHAR(255),
    producto TEXT,
    fabricante VARCHAR(255),
    nro_de_parte VARCHAR(255),
    moneda VARCHAR(10),
    precio_sin_iva DECIMAL(12, 2),
    porc_iva DECIMAL(5, 2),
    imp_int DECIMAL(10, 2),
    precio_final_usd DECIMAL(12, 2),
    stock VARCHAR(50)
);

-- Paso 3: Crear una tabla temporal para la carga inicial.
CREATE TEMP TABLE productos_temp (
    codigo TEXT,
    categoria TEXT,
    producto TEXT,
    fabricante TEXT,
    nro_de_parte TEXT,
    moneda TEXT,
    precio_sin_iva TEXT,
    porc_iva TEXT,
    imp_int TEXT,
    precio_final_usd TEXT,
    stock TEXT
);

-- Paso 4: Copiar los datos del CSV DEDUPLICADO a la tabla temporal.
\copy productos_temp FROM '/home/hernan/proyectos_bots/adk-samples/python/agents/customer-service/customer_service/data/Lista_de_Precios_Deduplicada.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8', QUOTE '"');

-- Paso 5: Insertar y transformar los datos de la tabla temporal a la tabla final.
INSERT INTO productos (
    codigo,
    categoria,
    producto,
    fabricante,
    nro_de_parte,
    moneda,
    precio_sin_iva,
    porc_iva,
    imp_int,
    precio_final_usd,
    stock
)
SELECT
    codigo,
    categoria,
    producto,
    fabricante,
    nro_de_parte,
    moneda,
    CAST(REPLACE(precio_sin_iva, ',', '.') AS DECIMAL(12, 2)),
    CAST(REPLACE(porc_iva, ',', '.') AS DECIMAL(5, 2)),
    CAST(REPLACE(imp_int, ',', '.') AS DECIMAL(10, 2)),
    CAST(REPLACE(precio_final_usd, ',', '.') AS DECIMAL(12, 2)),
    NULLIF(stock, '')
FROM productos_temp;

-- Paso 6: Eliminar la tabla temporal.
DROP TABLE productos_temp;

-- Mensaje de confirmación
\echo ''
\echo '*** ¡Proceso completado! ***'
\echo 'La tabla de productos fue creada y los datos cargados.'
\echo ''
