FROM node:lts-slim

# Create app directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./
COPY yarn.lock ./

# Install dependencies
RUN yarn install

# Copy source code
COPY tsconfig.json tsconfig.json
COPY src src
COPY public public

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm","run", "start"] 
