# syntax=docker/dockerfile:1
FROM node:20 AS build
ARG NPM_TOKEN
ENV NPM_TOKEN=$NPM_TOKEN
WORKDIR /app
COPY . .
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
RUN npm install
RUN npm run build
RUN apt-get update && apt-get install -y curl vim procps
RUN rm -f .npmrc

FROM node:20
WORKDIR /app
COPY --from=build /app /app
ENV NODE_ENV=production
EXPOSE 3000
CMD npm start
