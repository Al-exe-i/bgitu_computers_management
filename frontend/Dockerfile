FROM node:22-alpine AS build
WORKDIR /vue

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /vue/dist /usr/share/nginx/html
COPY --from=build /vue/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /vue/security-headers.conf /etc/nginx/snippets/security-headers.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
