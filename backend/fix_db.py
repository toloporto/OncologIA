# fix_db.py - Script para crear base de datos con hash bcrypt válido
import sqlite3
import bcrypt
import uuid
import os

# 1. CONTRASEÑA CORRECTA
PASSWORD = b"Psycho2025!"

# 2. Generar hash BCrypt VÁLIDO (usando bcrypt directamente, no passlib)
print("Generando hash bcrypt válido...")
hashed_password = bcrypt.hashpw(PASSWORD, bcrypt.gensalt(rounds=12))
hashed_password_str = hashed_password.decode('utf-8')
print(f"Hash generado: {hashed_password_str[:60]}...")

# 3. Crear/Conectar a la base de datos
db_path = "psico.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Base de datos anterior eliminada: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 4. Crear tabla 'users' (ajusta según tu esquema real)
cursor.execute('''
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1
)
''')

# 5. Insertar usuario de prueba con el hash VÁLIDO
user_id = str(uuid.uuid4())
cursor.execute(
    'INSERT INTO users (id, email, hashed_password, full_name, is_active) VALUES (?, ?, ?, ?, ?)',
    (user_id, 'test@psych.com', hashed_password_str, 'Usuario Demo', 1)
)

conn.commit()
conn.close()
print("✅ Base de datos 'psico.db' creada con usuario de prueba y hash bcrypt VÁLIDO.")
print(f"   Email: test@psych.com")
print(f"   Password: {PASSWORD.decode('utf-8')}")

# 6. Verificación rápida del hash
print("\n🔍 Verificando hash...")
test_check = bcrypt.checkpw(PASSWORD, hashed_password)
print(f"   Verificación con bcrypt.checkpw: {'✅ ÉXITO' if test_check else '❌ FALLO'}")