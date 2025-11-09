# Instrucciones para cargar datos en EC2

## Opción 1: Limpiar y cargar (Recomendado)

```bash
# 1. Limpiar la base de datos (elimina todos los datos)
python manage.py flush --noinput

# 2. Cargar los datos
python manage.py loaddata data.json
```

## Opción 2: Usar el script

```bash
# Dar permisos de ejecución
chmod +x load_data.sh

# Ejecutar el script
./load_data.sh
```

## Opción 3: Cargar sin limpiar (puede fallar si hay datos existentes)

```bash
python manage.py loaddata data.json --ignorenonexistent
```

## Notas importantes

- **`flush`** elimina TODOS los datos de la base de datos antes de cargar
- Asegúrate de hacer backup si hay datos importantes
- El flag `--noinput` evita que pida confirmación
- El flag `--ignorenonexistent` ignora campos que no existen en el modelo actual

