package com.parserpotato.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO for OrderItem data validation
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class OrderItemDTO {

    @NotBlank(message = "Order ID is required")
    @Size(min = 1, max = 50, message = "Order ID must be between 1 and 50 characters")
    private String orderId;

    @NotBlank(message = "Product ID is required")
    @Size(min = 1, max = 50, message = "Product ID must be between 1 and 50 characters")
    private String productId;

    @NotNull(message = "Quantity is required")
    @Positive(message = "Quantity must be greater than 0")
    private Integer quantity;

    @NotNull(message = "Unit price is required")
    @Positive(message = "Unit price must be greater than 0")
    private Double unitPrice;

    @NotNull(message = "Subtotal is required")
    @PositiveOrZero(message = "Subtotal must be 0 or greater")
    private Double subtotal;
}
