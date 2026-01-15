FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build for production
RUN npm run build

# Expose port (Railway uses $PORT)
EXPOSE 3000

# Run production server
CMD ["npm", "start"]
