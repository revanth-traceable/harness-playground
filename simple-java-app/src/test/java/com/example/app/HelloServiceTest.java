package com.example.app;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class HelloServiceTest {
    
    @Test
    public void testGetMessage() {
        HelloService service = new HelloService();
        String message = service.getMessage();
        assertNotNull(message);
        assertTrue(message.contains("Hello"));
    }
    
    @Test
    public void testGetPersonalizedMessage() {
        HelloService service = new HelloService();
        String message = service.getPersonalizedMessage("DevOps");
        assertNotNull(message);
        assertTrue(message.contains("Hello DevOps"));
    }
    
    @Test
    public void testGetPersonalizedMessageWithEmptyName() {
        HelloService service = new HelloService();
        String message = service.getPersonalizedMessage("");
        assertNotNull(message);
        assertEquals(service.getMessage(), message);
    }
    
    @Test
    public void testGetPersonalizedMessageWithNullName() {
        HelloService service = new HelloService();
        String message = service.getPersonalizedMessage(null);
        assertNotNull(message);
        assertEquals(service.getMessage(), message);
    }
}
