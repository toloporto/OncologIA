# patch_transformers.py
import re

file_path = r"C:\Users\antol\venv\Lib\site-packages\transformers\utils\generic.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la función _is_tensorflow
pattern = r'def _is_tensorflow\(x\):\s*\n\s*import tensorflow as tf\s*\n\s*return isinstance\(x, tf\.Tensor\)'

replacement = '''def _is_tensorflow(x):
    import tensorflow as tf
    # Múltiples intentos para detectar tensores de TensorFlow
    try:
        return isinstance(x, tf.Tensor)
    except AttributeError:
        try:
            return isinstance(x, tf.python.framework.ops.Tensor)
        except:
            try:
                return hasattr(x, 'numpy') and callable(getattr(x, 'numpy', None))
            except:
                return type(x).__name__ in ['Tensor', 'EagerTensor', 'ResourceVariable']'''

if re.search(pattern, content):
    new_content = re.sub(pattern, replacement, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Parche aplicado correctamente a transformers/utils/generic.py")
else:
    print("⚠️  No se encontró el patrón. Buscando manualmente...")
    # Buscar cualquier definición de _is_tensorflow
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '_is_tensorflow' in line and 'def ' in line:
            print(f"   Encontrada en línea {i+1}: {line}")