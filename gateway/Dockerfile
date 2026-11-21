# Build from the repository root:  docker build -f gateway/Dockerfile .
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY gateway/package*.json ./
RUN npm ci --omit=dev
COPY gateway/src ./src
COPY --from=web /web/dist ./public
ENV FRONTEND_DIST=/app/public NODE_ENV=production
EXPOSE 8080
CMD ["node", "src/index.js"]
