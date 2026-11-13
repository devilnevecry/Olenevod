# Dockerfile для админки Olenevod (Vite React 19).
FROM node:22-alpine
WORKDIR /app
ENV VITE_API_URL=http://localhost:8000
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || true
COPY . .
RUN npm run build || true
EXPOSE 5173
CMD ["npm", "run", "preview", "--", "--host", "--port", "5173"]
