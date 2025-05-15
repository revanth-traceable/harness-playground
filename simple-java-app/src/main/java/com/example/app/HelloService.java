package com.example.app;

/**
 * Service class that provides a greeting message
 */
public class HelloService {
    
    /**
     * Returns a greeting message
     * @return String greeting message
     */
    public String getMessage() {
        return "Hello from DevSecOps Demo Application!";
    }
    
    /**
     * Returns a personalized greeting
     * @param name The name to greet
     * @return String personalized greeting
     */
    public String getPersonalizedMessage(String name) {
        if (name == null || name.trim().isEmpty()) {
            return getMessage();
        }
        return "Hello " + name + " from DevSecOps Demo Application!";
    }
}
