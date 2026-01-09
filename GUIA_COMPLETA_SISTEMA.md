# 📘 Guía Maestra: OncologIA

**Sistema de Inteligencia Artificial para Psico-Oncología y Cuidados Paliativos.**

---

## 🏗️ 1. Arquitectura del Sistema

El sistema opera bajo una arquitectura híbrida y modular diseñada para la privacidad, la robustez clínica y el aprendizaje continuo.

### Componentes Principales:

1.  **Backend (FastAPI)**: Orquesta la lógica del negocio, gestiona la seguridad (Auth JWT) y expone la API REST.
2.  **Cerebro Clínico (LangChain + Gemini)**:
    - **Analista de Riesgos (Triage)**: Detecta urgencias oncológicas y riesgos de suicidio en tiempo real.
    - **Extractor de Síntomas (ESAS)**: Cuantifica síntomas (Dolor, Fatiga, Náusea) según la escala de Edmonton.
    - **Generador GenAI (SOAP + TCC)**: Redacta informes clínicos y material educativo para pacientes.
3.  **Memoria Adaptativa (ChromaDB + RAG)**:
    - Almacena vectores de conocimiento para recuperación contextual.
    - **Active Learning**: Almacena las correcciones del médico para mejorar la precisión futura (Dynamic Few-Shot).
4.  **Frontend (React + Vite)**: Interfaz moderna optimizada para uso clínico rápido (Color Palette: Teal/Sky Blue).

---

## 🧠 2. Sistema de Aprendizaje Activo (Active Learning)

A diferencia de las IAs estáticas, OncologIA mejora con el uso:

1.  **Diagnóstico Inicial**: La IA analiza el texto del paciente.
2.  **Validación Humana**: El médico revisa el gráfico de síntomas. Si hay un error (ej. confundir fatiga con dolor), lo corrige pulsando el botón ✏️.
3.  **Ingesta Vectorial**: La corrección se guarda automáticamente en `feedback_learning` (ChromaDB).
4.  **Inferencia Adaptativa**: La próxima vez que llegue un caso similar, la IA recuperará esa corrección y la usará como ejemplo ("Few-Shot") para no repetir el error.

---

## 🛡️ 3. Robustez y "Modo Seguro"

El sistema está diseñado para entornos clínicos críticos:

- **Fallo de API / Rate Limits**: Si Google Gemini se satura (Error 429), el sistema entra automáticamente en **MODO SEGURO**.
- **Comportamiento**: En lugar de estrellarse, devuelve datos de demostración o caches locales, mostrando una alerta visual 🔦 en la interfaz. Esto asegura que el médico nunca pierda acceso a la herramienta durante una consulta.

---

## 🚀 4. Guía de Ejecución

### Requisitos Previos

- Python 3.10+
- Node.js 18+
- Google Gemini API Key

### Comandos de Inicio

**Terminal 1: Backend**

```powershell
.\venv\Scripts\Activate.ps1
uvicorn backend.onco_api:app --reload
```

**Terminal 2: Frontend**

```powershell
cd frontend
npm run dev
```

Acceder en: **http://localhost:5173**

---

## 🌐 5. Despliegue y Futuro

- **PWA**: Listo para convertirse en App Móvil.
- **FHIR**: Estructura de datos compatible para integración futura con hospitales.
- **Render.com**: Configurado (`render.yaml`) para despliegue en nube si se requiere acceso remoto.

---

**© 2026 OncologIA Project**
