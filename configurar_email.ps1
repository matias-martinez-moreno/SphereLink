# Script para configurar email en desarrollo local
# Ejecuta este script ANTES de iniciar el servidor Django

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACIÓN DE EMAIL - SPHERELINK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Solicitar email
$email = Read-Host "Ingresa tu email (ej: tu_email@gmail.com)"

# Solicitar contraseña de aplicación
Write-Host ""
Write-Host "IMPORTANTE: Para Gmail necesitas una 'App Password'" -ForegroundColor Yellow
Write-Host "1. Ve a: https://myaccount.google.com/apppasswords" -ForegroundColor Yellow
Write-Host "2. Genera una contraseña de aplicación" -ForegroundColor Yellow
Write-Host "3. Copia la contraseña de 16 caracteres" -ForegroundColor Yellow
Write-Host ""
$password = Read-Host "Ingresa tu App Password (16 caracteres)" -AsSecureString

# Convertir SecureString a texto plano
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Configurar variables de entorno
$env:EMAIL_HOST_USER = $email
$env:EMAIL_HOST_PASSWORD = $plainPassword
$env:EMAIL_HOST = "smtp.gmail.com"
$env:EMAIL_PORT = "587"

Write-Host ""
Write-Host "✅ Variables de entorno configuradas!" -ForegroundColor Green
Write-Host ""
Write-Host "📧 Email: $email" -ForegroundColor Cyan
Write-Host "📧 Servidor: smtp.gmail.com:587" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "   - Estas variables solo duran mientras esta ventana esté abierta" -ForegroundColor Yellow
Write-Host "   - Debes ejecutar 'python manage.py runserver' en ESTA MISMA ventana" -ForegroundColor Yellow
Write-Host "   - O ejecuta este script cada vez que abras una nueva terminal" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Enter para continuar..." -ForegroundColor Gray
Read-Host

