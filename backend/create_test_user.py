# Script para crear usuario de prueba manualmente
from backend.database import SessionLocal
from backend.models import User
from backend.auth import get_password_hash
import uuid

db = SessionLocal()

try:
    test_email = "test@ortho.com"
    test_password = "test123"
    
    # Verificar si ya existe
    existing = db.query(User).filter(User.email == test_email).first()
    
    if existing:
        print(f"⚠️ El usuario {test_email} ya existe")
        print(f"   ID: {existing.id}")
        print(f"   Nombre: {existing.full_name}")
        
        # Actualizar contraseña por si acaso
        existing.hashed_password = get_password_hash(test_password)
        db.commit()
        print(f"✅ Contraseña actualizada a: {test_password}")
    else:
        # Crear nuevo usuario
        new_user = User(
            id=str(uuid.uuid4()),
            email=test_email,
            hashed_password=get_password_hash(test_password),
            full_name="Usuario de Prueba",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        print(f"✅ Usuario creado exitosamente:")
        print(f"   Email: {test_email}")
        print(f"   Contraseña: {test_password}")
        print(f"   Nombre: Usuario de Prueba")
    
    # Verificar que se puede hacer login
    from backend.auth import verify_password
    user = db.query(User).filter(User.email == test_email).first()
    
    print("\n🔐 Verificando contraseña...")
    if verify_password(test_password, user.hashed_password):
        print("✅ La contraseña es correcta y funciona!")
    else:
        print("❌ ERROR: La contraseña NO coincide")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "="*50)
print("Credenciales para usar:")
print(f"Email: test@ortho.com")
print(f"Contraseña: test123")
print("="*50)
