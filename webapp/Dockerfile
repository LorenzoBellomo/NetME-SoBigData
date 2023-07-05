ARG BUILD
FROM node:16.13 as node
WORKDIR /usr/app
COPY ./package.json ./
RUN npm install --force
COPY ./ ./ 
ARG BUILD
ENV BUILD=${BUILD}
RUN echo ${BUILD}
RUN npm run ${BUILD}
FROM nginx:alpine
COPY --from=node /usr/app/dist/app /usr/share/nginx/html
COPY ./app.conf /etc/nginx/conf.d/default.conf