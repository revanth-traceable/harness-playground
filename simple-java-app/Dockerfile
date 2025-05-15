FROM eclipse-temurin:11-jre-alpine

WORKDIR /app

# Copy the JAR file
COPY  simple-java-app/target/devsecops-demo-*-jar-with-dependencies.jar /app/app.jar

# Use a non-root user with UID 1000
USER 1000

# Run the application
CMD ["java", "-jar", "/app/app.jar"]
