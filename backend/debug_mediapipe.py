# debug_mediapipe.py
import sys

print("🔍 Diagnóstico de MediaPipe")
print("=" * 50)

# 1. Verificar versión
try:
    import mediapipe as mp
    print(f"✅ MediaPipe importado: versión {mp.__version__}")
    
    # 2. Verificar estructura
    print("\n📁 Estructura de MediaPipe:")
    
    # Intentar diferentes formas de acceder
    methods = [
        ("import mediapipe", "mp"),
        ("from mediapipe.python.solutions import face_mesh", "face_mesh"),
        ("import mediapipe.solutions", "solutions"),
    ]
    
    for import_stmt, var_name in methods:
        try:
            exec(import_stmt)
            print(f"   ✅ {import_stmt}")
        except Exception as e:
            print(f"   ❌ {import_stmt}: {e}")
    
    # 3. Listar atributos disponibles
    print("\n🔧 Atributos disponibles en mediapipe:")
    attrs = [attr for attr in dir(mp) if not attr.startswith('_')]
    print(f"   Total: {len(attrs)}")
    print(f"   Primeros 15: {attrs[:15]}")
    
    # 4. Buscar 'solutions'
    if hasattr(mp, 'solutions'):
        print(f"\n✅ mp.solutions existe")
        print(f"   Atributos en solutions: {[x for x in dir(mp.solutions) if not x.startswith('_')][:10]}")
    else:
        print(f"\n❌ mp.solutions NO existe")
        
        # Buscar en sys.modules
        print(f"\n🔎 Buscando módulos relacionados:")
        for module_name in sys.modules:
            if 'mediapipe' in module_name:
                print(f"   - {module_name}")
                
except ImportError as e:
    print(f"❌ No se puede importar mediapipe: {e}")
    print(f"💡 Instala con: pip install mediapipe")