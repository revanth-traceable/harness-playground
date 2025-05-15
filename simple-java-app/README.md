# DevSecOps Demo Application

A simple Java application designed for demonstrating various DevSecOps practices including:

- CI/CD Pipelines
- Container Security Scanning
- Artifact Signing
- Code/SAST Scanning
- Maven Cache Optimization
- Kubernetes Deployments

## Requirements

- Java 11+
- Maven 3.6+
- Docker (for container builds)
- Kubernetes cluster (for deployment)
- Helm 3+ (for Kubernetes deployments)

## Building the Application

```bash
mvn clean package
```

This will create two JAR files in the `target` directory:
- `devsecops-demo-1.0-SNAPSHOT.jar`: The regular JAR file
- `devsecops-demo-1.0-SNAPSHOT-jar-with-dependencies.jar`: A "fat" JAR that includes all dependencies

## Running the Application

```bash
java -jar target/devsecops-demo-1.0-SNAPSHOT-jar-with-dependencies.jar
```

## Running Tests

```bash
mvn test
```

## Building Docker Image

```bash
docker build -t devsecops-demo:latest .
```

## Maven Cache

Maven stores downloaded dependencies in a local repository cache, typically located at:

- `~/.m2/repository` (Linux/macOS)
- `C:\Users\<username>\.m2\repository` (Windows)

For CI/CD pipelines, caching this directory between builds can significantly speed up build times by avoiding repeated downloads of dependencies.

## Deploying with Helm

The application includes a Helm chart for easy deployment to Kubernetes.

### Installing the Chart

```bash
# From the root of the project
cd helm
helm install demo devsecops-demo
```

### Using a Custom Values File

```bash
helm install demo devsecops-demo -f devsecops-demo/values-prod.yaml
```

### Upgrading the Deployment

```bash
helm upgrade demo devsecops-demo
```

### Uninstalling the Chart

```bash
helm uninstall demo
```

## Project Structure

```
├── src
│   ├── main
│   │   ├── java
│   │   │   └── com
│   │   │       └── example
│   │   │           └── app
│   │   │               ├── Application.java
│   │   │               └── HelloService.java
│   │   └── resources
│   │       └── logback.xml
│   └── test
│       └── java
│           └── com
│               └── example
│                   └── app
│                       └── HelloServiceTest.java
├── kubernetes
│   └── deployment.yaml
├── helm
│   └── devsecops-demo
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-prod.yaml
│       └── templates
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── ingress.yaml
│           └── ...
├── Dockerfile
└── pom.xml
```
