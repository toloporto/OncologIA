# ⚛️ OrthoWeb3 - Frontend

Este es el frontend de la aplicación OrthoWeb3, construido con **React** y **Vite**. Proporciona la interfaz de usuario para que los profesionales dentales suban imágenes, vean los resultados del análisis de IA y gestionen los datos de los pacientes.

## ✨ Características

- **Carga de Imágenes**: Interfaz intuitiva para subir imágenes dentales para su análisis.
- **Visualización de Resultados**: Muestra el diagnóstico de la IA, la confianza y las recomendaciones de tratamiento.
- **Integración con Wallet Web3**: Se conecta con wallets como MetaMask para gestionar la identidad del paciente y la propiedad de los datos (NFTs).
- **Diseño Responsivo**: Adaptado para su uso en diferentes dispositivos.

## 🛠️ Tecnologías Utilizadas

- **React**: Biblioteca principal para construir la interfaz de usuario.
- **Vite**: Herramienta de desarrollo y construcción ultrarrápida.
- **Ethers.js**: Para interactuar con la blockchain de Polygon y los Smart Contracts.
- **Tailwind CSS / Chakra UI / Material-UI**: (Elige el que estés usando) para el diseño y los componentes.
- **Axios / Fetch**: Para realizar peticiones a la API del backend.

## 🚀 Puesta en Marcha

### 1. Prerrequisitos

- Node.js (v18 o superior)
- npm, yarn o pnpm

### 2. Instalación

```bash
# Navega a la carpeta del frontend
cd frontend

# Instala las dependencias
npm install
```

### 3. Ejecutar en Modo Desarrollo

Asegúrate de que el backend (`ortho_api_real.py`) se esté ejecutando en `http://localhost:8004`.

```bash
# Inicia el servidor de desarrollo de Vite
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

### 4. Construir para Producción

Este comando genera los archivos estáticos optimizados en la carpeta `dist/`.

```bash
npm run build
```

Estos archivos son los que Nginx servirá en el entorno de producción de Docker.
