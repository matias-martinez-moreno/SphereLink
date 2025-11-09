#!/bin/bash
# Script para cargar datos en EC2
# Limpia la base de datos y carga el fixture

echo "Limpiando base de datos..."
python manage.py flush --noinput

echo "Cargando datos desde data.json..."
python manage.py loaddata data.json

echo "¡Datos cargados exitosamente!"

