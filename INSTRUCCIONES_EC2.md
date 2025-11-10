# Instrucciones para configurar base de datos en EC2

## Opción 1: Usar el comando setup_production_data (RECOMENDADO)

Este comando crea todos los datos necesarios usando `get_or_create`, evitando errores de integridad.

### Si la base de datos está vacía:
```bash
python manage.py migrate
python manage.py setup_production_data
```

### Si la base de datos tiene datos y quieres empezar desde cero:
```bash
python manage.py migrate
python manage.py setup_production_data --flush
```

### Si la base de datos tiene datos y quieres agregar solo lo que falta:
```bash
python manage.py migrate
python manage.py setup_production_data
```

## Opción 2: Usar loaddata con data.json (Puede fallar)

### Si la base de datos está vacía:
```bash
python manage.py migrate
python manage.py loaddata data.json
```

### Si hay datos existentes (limpiar primero):
```bash
python manage.py migrate
python manage.py flush --noinput
python manage.py loaddata data.json
```

## Credenciales por defecto

Después de ejecutar `setup_production_data`, puedes iniciar sesión con:

- **Superadmin**: `superadmin` / `admin123`
- **Staff**: `staff1` / `staff123`
- **Member**: `member1` / `member123`
- **Usuarios adicionales**: `ana.garcia1`, `carlos.rodriguez2`, etc. / `eafit123`

⚠️ **IMPORTANTE**: Cambia las contraseñas después del primer login.

## Resolución de problemas

### Error: UNIQUE constraint failed
- **Solución**: Usa `setup_production_data --flush` para limpiar la base de datos primero
- O usa `setup_production_data` sin `--flush` para agregar solo lo que falta

### Error: No such table
- **Solución**: Ejecuta `python manage.py migrate` primero

### Error: Permission denied
- **Solución**: Asegúrate de tener permisos de escritura en la base de datos

