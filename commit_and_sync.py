#!/usr/bin/env python
import subprocess
import sys

def run_command(command):
    """Ejecutar comando y mostrar resultado"""
    print(f"Ejecutando: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def main():
    print("=== COMMIT Y SINCRONIZACIÓN DE RAMAS ===")
    
    # 1. Verificar estado actual
    print("\n1. Verificando estado actual...")
    run_command("git status")
    
    # 2. Agregar todos los cambios
    print("\n2. Agregando todos los cambios...")
    if not run_command("git add ."):
        print("Error al agregar archivos")
        return
    
    # 3. Hacer commit
    print("\n3. Haciendo commit...")
    if not run_command('git commit -m "comments"'):
        print("Error al hacer commit")
        return
    
    # 4. Subir a development
    print("\n4. Subiendo a development...")
    if not run_command("git push origin development"):
        print("Error al subir a development")
        return
    
    # 5. Cambiar a main
    print("\n5. Cambiando a rama main...")
    if not run_command("git checkout main"):
        print("Error al cambiar a main")
        return
    
    # 6. Hacer merge de development a main
    print("\n6. Haciendo merge de development a main...")
    if not run_command("git merge development"):
        print("Error al hacer merge")
        return
    
    # 7. Subir main actualizado
    print("\n7. Subiendo main actualizado...")
    if not run_command("git push origin main"):
        print("Error al subir main")
        return
    
    # 8. Volver a development
    print("\n8. Volviendo a development...")
    if not run_command("git checkout development"):
        print("Error al volver a development")
        return
    
    print("\n✅ ¡Proceso completado exitosamente!")
    print("📋 Resumen:")
    print("- Commit 'comments' creado")
    print("- Cambios subidos a development")
    print("- main sincronizado con development")
    print("- Ambos repositorios remotos actualizados")

if __name__ == "__main__":
    main()
