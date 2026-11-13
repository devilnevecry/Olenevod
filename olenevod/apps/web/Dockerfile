# Dockerfile для витрины Olenevod (Next.js 15).
FROM node:22-alpine
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || true
COPY . .
RUN npm run build || true
EXPOSE 3000
CMD ["npm", "start"]
