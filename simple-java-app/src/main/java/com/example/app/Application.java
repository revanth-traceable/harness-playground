package com.example.app;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Simple Java application for DevSecOps demonstration
 */
public class Application {
    private static final Logger logger = LoggerFactory.getLogger(Application.class);

    public static void main(String[] args) {
        logger.info("Starting DevSecOps Demo Application");
        
        HelloService service = new HelloService();
        String message = service.getMessage();
        
        logger.info("Message: {}", message);
        System.out.println(message);
        
        logger.info("Application finished successfully");
    }
}
