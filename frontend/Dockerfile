FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json ./
RUN npm install

FROM deps AS dev

COPY tsconfig.json tsconfig.node.json vite.config.ts index.html ./
COPY src ./src

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM deps AS build

COPY tsconfig.json tsconfig.node.json vite.config.ts index.html ./
COPY src ./src

RUN npm run build

FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
