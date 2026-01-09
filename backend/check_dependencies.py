# Script para verificar dependencias
import sys

print("Verificando dependencias...\n")

dependencies = {
    'jose': 'python-jose',
    'passlib': 'passlib',
    'fastapi': 'fastapi',
    'sqlalchemy': 'sqlalchemy'
}

missing = []

for module, package in dependencies.items():
    try:
        __import__(module)
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package} - NO INSTALADO")
        missing.append(package)

if missing:
    print(f"\n⚠️ Faltan {len(missing)} dependencias:")
    print("\nEjecuta este comando para instalarlas:")
    print(f"pip install {' '.join(missing)}")
    if 'python-jose' in missing:
        print("\nPara python-jose, usa:")
        print("pip install python-jose[cryptography]")
    if 'passlib' in missing:
        print("\nPara passlib, usa:")
        print("pip install passlib[bcrypt]")
else:
    print("\n✅ Todas las dependencias están instaladas!")
