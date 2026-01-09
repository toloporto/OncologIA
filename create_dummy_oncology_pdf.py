# create_dummy_oncology_pdf.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_oncology_protocol():
    filename = "knowledge_base/protocolo_dolor_oncologico.pdf"
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "PROTOCOLO DE MANEJO DEL DOLOR ONCOLÓGICO (OMS)")
    
    # Cuerpo
    c.setFont("Helvetica", 12)
    y_position = height - 80
    
    lines = [
        "1. INTRODUCCIÓN",
        "El dolor es uno de los síntomas más temidos en pacientes oncológicos.",
        "Su manejo adecuado mejora significativamente la calidad de vida.",
        "",
        "2. ESCALERA ANALGÉSICA DE LA OMS",
        "- PELDANO 1 (Dolor Leve, EVA 1-3): No opioides (Paracetamol, AINEs).",
        "- PELDANO 2 (Dolor Moderado, EVA 4-6): Opioides débiles (Tramadol, Codeína) +/- Coadyuvantes.",
        "- PELDANO 3 (Dolor Severo, EVA 7-10): Opioides potentes (Morfina, Fentanilo, Oxicodona).",
        "",
        "3. MANEJO DEL DOLOR IRRUPTIVO",
        "Se define como una exacerbación transitoria del dolor en pacientes con dolor basal controlado.",
        "Tratamiento: Dosis de rescate de opioide de liberación rápida (1/6 de la dosis diaria total).",
        "Ejemplo: Si toma 60mg de Morfina al día, el rescate debe ser de 10mg.",
        "",
        "4. SIGNOS DE TOXICIDAD POR OPIOIDES",
        "- Somnolencia excesiva o sedación.",
        "- Depresión respiratoria (< 8 respiraciones/min).",
        "- Mioclonías (sacudidas musculares).",
        "Ante estos signos: Reducir dosis o administrar Naloxona si hay parada respiratoria.",
        "",
        "5. COADYUVANTES",
        "- Dolor Neuropático: Gabapentina, Pregabalina, Amitriptilina.",
        "- Dolor Óseo: Corticoides, Bifosfonatos.",
        "",
        "FIN DEL PROTOCOLO"
    ]
    
    for line in lines:
        c.drawString(50, y_position, line)
        y_position -= 20
        
    c.save()
    print(f"✅ PDF creado exitosamente: {filename}")

if __name__ == "__main__":
    create_oncology_protocol()
