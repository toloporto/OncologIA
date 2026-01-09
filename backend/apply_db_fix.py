import sqlite3
import os

db_path = "psico.db"

if not os.path.exists(db_path):
    db_path = os.path.join("backend", "psico.db")

print(f"🔍 Intentando conectar a la base de datos en: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Intentar añadir la columna soap_report
    print("🛠️ Añadiendo columna 'soap_report' a la tabla 'session_logs'...")
    try:
        cursor.execute("ALTER TABLE session_logs ADD COLUMN soap_report TEXT")
        conn.commit()
        print("✅ Columna añadida con éxito.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ La columna ya existe.")
        else:
            print(f"❌ Error al alterar la tabla: {e}")
            
    conn.close()
    print("🏁 Proceso completado.")

except Exception as e:
    print(f"❌ Error general: {e}")
