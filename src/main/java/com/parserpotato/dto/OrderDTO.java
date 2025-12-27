package com.parserpotato.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * DTO for Order data validation
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class OrderDTO {

    @NotBlank(message = "Order ID is required")
    @Size(min = 1, max = 50, message = "Order ID must be between 1 and 50 characters")
    private String orderId;

    @NotBlank(message = "Customer ID is required")
    @Size(min = 1, max = 50, message = "Customer ID must be between 1 and 50 characters")
    private String customerId;

    @NotNull(message = "Order date is required")
    private LocalDateTime orderDate;

    @NotBlank(message = "Status is required")
    @Pattern(regexp = "pending|processing|shipped|delivered|cancelled", message = "Status must be one of: pending, processing, shipped, delivered, cancelled")
    private String status;

    @NotNull(message = "Total amount is required")
    @PositiveOrZero(message = "Total amount must be 0 or greater")
    private Double totalAmount;
}
