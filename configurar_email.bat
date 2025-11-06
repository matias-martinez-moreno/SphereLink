@echo off
REM Script para configurar email en desarrollo local (Windows CMD)
REM Ejecuta este script ANTES de iniciar el servidor Django

echo ========================================
echo   CONFIGURACION DE EMAIL - SPHERELINK
echo ========================================
echo.

set /p EMAIL_HOST_USER="Ingresa tu email (ej: tu_email@gmail.com): "
echo.
echo IMPORTANTE: Para Gmail necesitas una 'App Password'
echo 1. Ve a: https://myaccount.google.com/apppasswords
echo 2. Genera una contraseña de aplicacion
echo 3. Copia la contraseña de 16 caracteres
echo.
set /p EMAIL_HOST_PASSWORD="Ingresa tu App Password (16 caracteres): "
set EMAIL_HOST=smtp.gmail.com
set EMAIL_PORT=587

echo.
echo Variables de entorno configuradas!
echo.
echo Email: %EMAIL_HOST_USER%
echo Servidor: %EMAIL_HOST%:%EMAIL_PORT%
echo.
echo IMPORTANTE:
echo    - Estas variables solo duran mientras esta ventana este abierta
echo    - Debes ejecutar 'python manage.py runserver' en ESTA MISMA ventana
echo    - O ejecuta este script cada vez que abras una nueva terminal
echo.
pause

