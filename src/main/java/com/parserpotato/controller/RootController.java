package com.parserpotato.controller;

import io.swagger.v3.oas.annotations.Hidden;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * Root controller for the application
 */
@RestController
@Hidden // Hide from Swagger UI
public class RootController {

    @GetMapping("/")
    public Map<String, String> root() {
        return Map.of(
                "message", "Welcome to Parser Potato API",
                "docs_url", "/swagger-ui/",
                "api_docs", "/docs",
                "health_check", "/api/health");
    }
}
