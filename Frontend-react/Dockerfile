# ---------- Base Build Stage ----------
FROM node:22-bullseye AS builder

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy source files
COPY . .

# Run the static export
RUN npm run build

# ---------- Static Serving Stage ----------
FROM node:22-alpine AS runner

# Install a lightweight static file server
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy the exported static site from the builder
COPY --from=builder /app/out ./out

# Expose the port used by the static server
EXPOSE 3000

# Run the static server
CMD ["serve", "-s", "out", "-l", "3000"]
