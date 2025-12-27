package com.parserpotato.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI/Swagger configuration
 */
@Configuration
public class OpenApiConfig {

        @Bean
        public OpenAPI customOpenAPI() {
                return new OpenAPI()
                                .info(new Info()
                                                .title("Parser Potato API")
                                                .version("1.0.0")
                                                .description("""
                                                                REST API for uploading and parsing large CSV/JSON files into a PostgreSQL database.

                                                                ## Documentation

                                                                * <a href="/docs/static/README.md" target="_blank">Project Overview (README)</a>
                                                                * <a href="/docs/static/ARCHITECTURE.md" target="_blank">System Architecture</a>
                                                                * <a href="/docs/static/EFFICIENCY_DESIGN.md" target="_blank">Efficiency & Design</a>
                                                                * <a href="/docs/static/TESTING.md" target="_blank">Testing Guide</a>
                                                                * <a href="/docs/static/IMPLEMENTATION_SUMMARY.md" target="_blank">Implementation Summary</a>

                                                                ## Features
                                                                [Please install PostgreSQL and provide the connection details in .env file]
                                                                * **File Upload**: Upload CSV or JSON files
                                                                * **Streaming Parser**: Process large files without loading them entirely in memory
                                                                * **Data Validation**: Schema and data quality validation
                                                                * **Multi-Table Support**: Automatically map data to related database tables
                                                                * **Batch Processing**: Efficient batch insertion for large datasets
                                                                * **Relationship Validation**: Verify foreign key relationships before insertion

                                                                ## Supported Tables
                                                                * **Customers**: customer_id, name, email, phone, address
                                                                * **Products**: product_id, name, price, description, category, stock_quantity
                                                                * **Orders**: order_id, customer_id, order_date, status, total_amount
                                                                * **Order Items**: order_id, product_id, quantity, unit_price, subtotal

                                                                **Document Version:** 1.0
                                                                **Last Updated:** December 2025
                                                                **Author:** [avinasx](https://github.com/avinasx)
                                                                """)
                                                .contact(new Contact()
                                                                .name("avinasx")
                                                                .url("https://github.com/avinasx")));
        }
}
