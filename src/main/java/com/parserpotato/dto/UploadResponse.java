package com.parserpotato.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

/**
 * Response DTO for file upload operations
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UploadResponse {

    private String message;
    private int recordsProcessed;
    @Builder.Default
    private int successRowsCount = 0;
    @Builder.Default
    private int skippedRowsCount = 0;
    @Builder.Default
    private int customersCreated = 0;
    @Builder.Default
    private int productsCreated = 0;
    @Builder.Default
    private int ordersCreated = 0;
    @Builder.Default
    private int orderItemsCreated = 0;
    @Builder.Default
    private List<String> errors = new ArrayList<>();
}
