package com.parserpotato.controller;

import com.parserpotato.dto.UploadResponse;
import com.parserpotato.service.DataLoaderService;
import com.parserpotato.service.FileParserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * REST controller for file upload operations
 */
@RestController
@RequestMapping("/api")
@Slf4j
@Tag(name = "File Upload", description = "API for uploading and processing CSV/JSON files")
public class UploadController {

    @Autowired
    private FileParserService fileParserService;

    @Autowired
    private DataLoaderService dataLoaderService;

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Upload and process CSV/JSON file", description = "Upload a CSV or JSON file to parse and insert data into the database. "
            +
            "Supports customers, products, orders, and order items data. " +
            "Maximum file size: 1GB")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "File processed successfully", content = @Content(schema = @Schema(implementation = UploadResponse.class))),
            @ApiResponse(responseCode = "400", description = "Invalid file format or validation errors"),
            @ApiResponse(responseCode = "413", description = "File size exceeds maximum allowed size (1GB)"),
            @ApiResponse(responseCode = "500", description = "Internal server error during file processing")
    })
    public ResponseEntity<UploadResponse> uploadFile(
            @Parameter(description = "CSV or JSON file to upload", required = true, content = @Content(mediaType = MediaType.MULTIPART_FORM_DATA_VALUE)) @RequestParam("file") MultipartFile file) {
        log.info("Received file upload request: {}", file.getOriginalFilename());

        try {
            // Validate file
            if (file.isEmpty()) {
                return ResponseEntity.badRequest()
                        .body(UploadResponse.builder()
                                .message("File is empty")
                                .build());
            }

            // Parse file and process in chunks
            Stream<Map<String, String>> recordStream = fileParserService.parseFile(file);

            int totalRecordsProcessed = 0;
            int totalSuccessRows = 0;
            int totalSkippedRows = 0;
            int totalCustomers = 0;
            int totalProducts = 0;
            int totalOrders = 0;
            int totalOrderItems = 0;

            // Process in chunks
            List<Map<String, String>> allRecords = recordStream.collect(Collectors.toList());
            int chunkSize = fileParserService.getChunkSize();

            for (int i = 0; i < allRecords.size(); i += chunkSize) {
                int end = Math.min(i + chunkSize, allRecords.size());
                List<Map<String, String>> chunk = allRecords.subList(i, end);

                dataLoaderService.clearErrors();

                // Validate and categorize
                Map<String, List<Object>> categorized = dataLoaderService.validateAndCategorize(chunk);

                // Verify relationships
                dataLoaderService.verifyRelationships(categorized);

                // Load data
                try {
                    int[] counts = dataLoaderService.loadDataBatch(categorized);
                    totalCustomers += counts[0];
                    totalProducts += counts[1];
                    totalOrders += counts[2];
                    totalOrderItems += counts[3];

                    int chunkSuccess = counts[0] + counts[1] + counts[2] + counts[3];
                    totalSuccessRows += chunkSuccess;
                    totalSkippedRows += (chunk.size() - chunkSuccess);
                } catch (Exception e) {
                    log.error("Error loading data batch", e);
                    totalSkippedRows += chunk.size();
                }

                totalRecordsProcessed += chunk.size();
            }

            List<String> allErrors = dataLoaderService.getErrors();

            UploadResponse response = UploadResponse.builder()
                    .message("File processed successfully")
                    .recordsProcessed(totalRecordsProcessed)
                    .successRowsCount(totalSuccessRows)
                    .skippedRowsCount(totalSkippedRows)
                    .customersCreated(totalCustomers)
                    .productsCreated(totalProducts)
                    .ordersCreated(totalOrders)
                    .orderItemsCreated(totalOrderItems)
                    .errors(allErrors.size() > 100 ? allErrors.subList(0, 100) : allErrors)
                    .build();

            log.info("File processing completed: {} records processed, {} success, {} skipped",
                    totalRecordsProcessed, totalSuccessRows, totalSkippedRows);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Error processing file", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(UploadResponse.builder()
                            .message("Error processing file: " + e.getMessage())
                            .errors(List.of(e.getMessage()))
                            .build());
        }
    }

    @GetMapping("/health")
    @Operation(summary = "Health check", description = "Check if the service is running")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of("status", "healthy"));
    }
}
