# fix_schema.py - Crear base de datos con esquema COMPLETO
import sqlite3
import bcrypt
import uuid
from datetime import datetime

# 1. CONEXIÓN Y CREACIÓN DE ESQUEMA COMPLETO
conn = sqlite3.connect('psico.db')
cursor = conn.cursor()

# 2. ELIMINAR TABLA SI EXISTE (PARA RECREARLA)
cursor.execute('DROP TABLE IF EXISTS users')

# 3. CREAR TABLA CON ESQUEMA COMPLETO (incluyendo created_at)
cursor.execute('''
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 4. GENERAR HASH BCRYPT VÁLIDO
password = b"Psycho2025!"
hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
hashed_str = hashed.decode('utf-8')

# 5. INSERTAR USUARIO CON FECHA
user_id = str(uuid.uuid4())
current_time = datetime.now().isoformat()

cursor.execute(
    '''INSERT INTO users 
       (id, email, hashed_password, full_name, is_active, created_at) 
       VALUES (?, ?, ?, ?, ?, ?)''',
    (user_id, 'test@psych.com', hashed_str, 'Usuario Demo', 1, current_time)
)

# 6. VERIFICAR
cursor.execute('SELECT * FROM users')
user = cursor.fetchone()
print("✅ Usuario insertado:")
print(f"  ID: {user[0]}")
print(f"  Email: {user[1]}")
print(f"  Hash: {user[2][:60]}...")
print(f"  Nombre: {user[3]}")
print(f"  Activo: {user[4]}")
print(f"  Creado: {user[5]}")

conn.commit()
conn.close()

print("\n✅ Base de datos 'psico.db' creada con esquema COMPLETO.")
print("   Incluye columna 'created_at' que necesita SQLAlchemy.")