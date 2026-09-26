FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG APP_VERSION=dev
ENV VITE_APP_VERSION=$APP_VERSION
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.28-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
