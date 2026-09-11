# Dockerfile - api service. Final image is 1.83 GB and CI push takes 4 minutes.
FROM node:22

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y build-essential python3 git curl vim
RUN npm install
RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "dist/server.js"]
