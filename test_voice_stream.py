import os
import sys
import time
import speech_recognition as sr
import numpy as np
import torch

# Añadir el directorio raíz al path para poder importar backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.voice_service import voice_service

def main():
    print("==================================================")
    print("   🎙️  PRUEBA DE CONCEPTO: WHISPER EN TIEMPO REAL")
    print("==================================================")
    print("Inicializando...")

    # 1. Configurar reconocedor para detectar silencios (VAD básico)
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # Sensibilidad del micrófono
    recognizer.pause_threshold = 0.8   # Segundos de silencio para considerar fin de frase
    recognizer.dynamic_energy_threshold = True

    # 2. Configurar micrófono
    try:
        mic = sr.Microphone(sample_rate=16000)
    except Exception as e:
        print(f"❌ Error abriendo micrófono: {e}")
        print("Asegúrate de tener PyAudio instalado.")
        return

    # 3. Precargar modelo
    print("Cargando modelo Whisper (esto puede tardar unos segundos la primera vez)...")
    try:
        voice_service.load_model()
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return

    print("\n✅ SISTEMA LISTO. ¡Habla ahora! (Presiona Ctrl+C para salir)\n")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        
        while True:
            try:
                print("🎧 Escuchando...", end="\r")
                # Escuchar audio (bloquea hasta que detecta silencio)
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                
                print("⏳ Procesando... ", end="\r")
                
                # Convertir raw data a numpy array compatible con Whisper
                # sr devuelve bytes en PCM int16 -> float32
                audio_data = np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0
                
                # Transcribir
                text = voice_service.transcribe_audio(audio_data)
                
                if text:
                    print(f"🗣️  Paciente: {text}")
                
            except KeyboardInterrupt:
                print("\n\n🛑 Prueba finalizada por el usuario.")
                break
            except Exception as e:
                print(f"\n⚠️ Error en bucle: {e}")

if __name__ == "__main__":
    main()
