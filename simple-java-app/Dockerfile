FROM eclipse-temurin:11-jre-alpine

WORKDIR /app

# Copy the JAR file
COPY  simple-java-app/target/devsecops-demo-*-jar-with-dependencies.jar /app/app.jar


USER 1000

# Run the application
CMD ["java", "-jar", "/app/app.jar"]
