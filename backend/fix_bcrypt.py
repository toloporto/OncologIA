# Script para arreglar el problema de bcrypt
import subprocess
import sys

print("🔧 Arreglando problema de bcrypt...\n")

commands = [
    ("Desinstalando bcrypt antiguo...", ["pip", "uninstall", "-y", "bcrypt"]),
    ("Instalando bcrypt 4.0.1 (compatible)...", ["pip", "install", "bcrypt==4.0.1"]),
    ("Reinstalando passlib...", ["pip", "install", "--upgrade", "passlib[bcrypt]"]),
]

for description, cmd in commands:
    print(f"⏳ {description}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Completado")
        else:
            print(f"   ⚠️ {result.stderr}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n✅ Proceso completado!")
print("\nAhora ejecuta:")
print("  python create_test_user.py")
