FROM node:20-alpine

WORKDIR /app

# Installer deps
COPY astro-app/package*.json ./
RUN npm install

# Copier le code
COPY astro-app ./

EXPOSE 4321

# identique à ton usage local, mais exposé vers l'extérieur
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
