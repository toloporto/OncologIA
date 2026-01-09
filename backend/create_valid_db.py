# create_valid_db.py
import sqlite3
import bcrypt
import uuid

# Crear base de datos
conn = sqlite3.connect('psico.db')
cursor = conn.cursor()

# Crear tabla users
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1
)
''')

# Generar hash bcrypt VÁLIDO para OrthoWeb3_Demo2024!
password = b"Psycho2025!"
hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
hashed_str = hashed.decode('utf-8')

# Insertar usuario
user_id = str(uuid.uuid4())
cursor.execute(
    'INSERT INTO users (id, email, hashed_password, full_name, is_active) VALUES (?, ?, ?, ?, ?)',
    (user_id, 'test@psych.com', hashed_str, 'Usuario Demo', 1)
)

conn.commit()
conn.close()
print(f"✅ Base de datos creada con hash válido: {hashed_str[:60]}...")