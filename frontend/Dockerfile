# Frontend Dockerfile - Development
# Note: Frontend Developer agent should refine this when initializing the Svelte project

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files (will be created by Frontend Developer agent)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Default command (development with hot reload)
CMD ["npm", "run", "dev", "--", "--host"]
