# create_db_with_schema.py - Crear base de datos que coincide EXACTAMENTE con models.py
import sqlite3
import bcrypt
import uuid
from datetime import datetime

print("🔧 Creando base de datos con esquema COMPLETO...")

# 1. ELIMINAR DB EXISTENTE Y CREAR NUEVA
db_path = "psico.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2. CREAR TABLAS EXACTAMENTE COMO EN models.py
cursor.execute('DROP TABLE IF EXISTS analysis_results')
cursor.execute('DROP TABLE IF EXISTS patients')
cursor.execute('DROP TABLE IF EXISTS users')

# 3. TABLA users (CON created_at)
cursor.execute('''
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP
)
''')

# 4. TABLA patients
cursor.execute('''
CREATE TABLE patients (
    id TEXT PRIMARY KEY,
    did TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP
)
''')

# 5. TABLA analysis_results
cursor.execute('''
CREATE TABLE analysis_results (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    patient_did TEXT,
    timestamp TIMESTAMP,
    predicted_class TEXT,
    confidence REAL,
    image_filename TEXT,
    recommendation TEXT,
    all_confidences_json TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# 6. CREAR ÍNDICES (como en models.py)
cursor.execute('CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)')
cursor.execute('CREATE INDEX IF NOT EXISTS ix_patients_did ON patients (did)')
cursor.execute('CREATE INDEX IF NOT EXISTS ix_analysis_results_patient_did ON analysis_results (patient_did)')

# 7. INSERTAR USUARIO DE PRUEBA CON HASH BCRYPT VÁLIDO
user_id = str(uuid.uuid4())
password = b"Psycho2025!"
hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
hashed_str = hashed.decode('utf-8')
current_time = datetime.now().isoformat()

cursor.execute(
    '''INSERT INTO users (id, email, hashed_password, full_name, is_active, created_at)
       VALUES (?, ?, ?, ?, ?, ?)''',
    (user_id, 'test@psych.com', hashed_str, 'Usuario Demo', 1, current_time)
)

# 8. INSERTAR PACIENTE DE PRUEBA (opcional, para tests de evolución)
patient_id = str(uuid.uuid4())
cursor.execute(
    '''INSERT INTO patients (id, did, full_name, created_at)
       VALUES (?, ?, ?, ?)''',
    (patient_id, 'did:psych:test_patient_001', 'Paciente Demo', current_time)
)

conn.commit()

# 9. VERIFICAR
print("\n✅ ESQUEMA CREADO:")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Tabla 'users':")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

print(f"\n✅ USUARIO DE PRUEBA CREADO:")
print(f"   Email: test@psych.com")
print(f"   Password: Psycho2025!")
print(f"   Hash: {hashed_str[:60]}...")

cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM patients")
patient_count = cursor.fetchone()[0]

print(f"\n📊 ESTADÍSTICAS:")
print(f"   Usuarios: {user_count}")
print(f"   Pacientes: {patient_count}")

conn.close()
print("\n🎉 Base de datos 'psico.db' lista para usar con SQLAlchemy!")