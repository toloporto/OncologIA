# Stage 1: Build de la aplicación React con Vite
FROM node:18-alpine AS builder

WORKDIR /app

# Copiamos los archivos de dependencias
COPY package.json package-lock.json ./

# Instalamos dependencias
RUN npm ci --production=false

# Copiamos el código fuente
COPY . .

# Construimos la aplicación para producción
RUN npm run build

# Stage 2: Servir la aplicación con nginx
FROM nginx:alpine

# Copiamos los archivos construidos desde el stage anterior
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiamos la configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponemos el puerto 80
EXPOSE 80

# nginx se ejecuta automáticamente en el foreground
CMD ["nginx", "-g", "daemon off;"]
