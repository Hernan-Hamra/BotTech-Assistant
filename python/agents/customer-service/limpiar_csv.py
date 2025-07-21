
import pandas as pd
import sys

# Obtener las rutas de los archivos desde los argumentos de la lnea de comandos
input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    # Leer el archivo CSV, asegurando que la columna 'Codigo' se trate como texto (str)
    df = pd.read_csv(input_file, delimiter=';', encoding='latin-1', dtype={'Codigo': str})

    # Limpiar espacios en los nombres de las columnas
    df.columns = df.columns.str.strip()

    # Guardar el orden original para desempatar
    df['original_index'] = df.index

    # Crear una columna de preferencia: 1 si tiene stock, 0 si no
    df['tiene_stock'] = df['Stock'].astype(str).str.strip().apply(lambda x: 1 if x not in ['0', '', 'nan'] else 0)

    # Ordenar para que, por cada cdigo, la mejor opcin quede primera:
    # 1. Prioridad por stock (descendente, 1 antes que 0)
    # 2. Prioridad por orden original (ascendente, el que apareci primero)
    df.sort_values(by=['Codigo', 'tiene_stock', 'original_index'], ascending=[True, False, True], inplace=True)

    # Eliminar duplicados de 'Codigo', quedndonos con la primera fila de cada grupo (que ahora es la mejor opcin)
    df_deduplicated = df.drop_duplicates(subset=['Codigo'], keep='first')

    # Restaurar el orden original del archivo
    df_deduplicated = df_deduplicated.sort_values(by='original_index')

    # Eliminar las columnas auxiliares que ya no necesitamos
    df_deduplicated = df_deduplicated.drop(columns=['original_index', 'tiene_stock'])

    # Guardar el resultado en un nuevo archivo CSV con codificacin UTF-8
    df_deduplicated.to_csv(output_file, sep=';', index=False, encoding='utf-8')

    print(f"Limpieza completada. Se guardaron {len(df_deduplicated)} filas nicas en {output_file}")

except Exception as e:
    print(f"Ocurri un error durante la limpieza: {e}", file=sys.stderr)
    sys.exit(1)

