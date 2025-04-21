# Use golang alpine as the base image
FROM golang:1.22-alpine

# Set working directory
WORKDIR /app

# Copy the Go files from hello-world directory
COPY hello-world/ .

# Build the application
RUN go build -o hello-world .

# Run the binary
CMD ["./hello-world"]
