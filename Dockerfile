# --- Bygg frontend (Vue) ---
FROM node:18-alpine AS frontend

# Sett arbeidskatalog til /frontend for Vue-prosjektet
WORKDIR /frontend

# Kopier kun package.json og package-lock.json
COPY package.json package-lock.json /frontend/

# Installer npm avhengigheter for frontend
RUN npm install

# Kopier frontend-komponenter og App.vue
COPY src/components /frontend/src/components
COPY src/App.vue /frontend/src/App.vue
COPY src/main.js /frontend/src/main.js

# Bygg Vue-prosjektet
RUN npm run build

# Kopier bygget frontend til backend
COPY --from=frontend /frontend/dist /app/frontend
