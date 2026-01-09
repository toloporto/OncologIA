# Script para verificar usuarios en la base de datos
from backend.database import SessionLocal
from backend.models import User

db = SessionLocal()

try:
    users = db.query(User).all()
    
    print("\n" + "="*50)
    print("📋 USUARIOS EN LA BASE DE DATOS")
    print("="*50)
    
    if not users:
        print("❌ No hay usuarios en la base de datos")
    else:
        for user in users:
            print(f"\n✅ Usuario encontrado:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Nombre: {user.full_name}")
            print(f"   Activo: {user.is_active}")
            print(f"   Creado: {user.created_at}")
    
    print("\n" + "="*50)
    print(f"Total de usuarios: {len(users)}")
    print("="*50 + "\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
