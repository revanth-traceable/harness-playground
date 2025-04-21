# Use a multi-stage build for a smaller final image
FROM golang:1.22-alpine AS builder

# Set working directory
WORKDIR /app

# Copy the Go source code
COPY . .

# Build the application
RUN go build -o hello-world .

# Create a minimal image for running the application
FROM alpine:latest

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/hello-world .

# Run the binary
CMD ["./hello-world"]
