package com.parserpotato.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

/**
 * Service for parsing CSV and JSON files with streaming support
 */
@Service
@Slf4j
public class FileParserService {

    @Value("${app.chunk-size:1000}")
    private int chunkSize;

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * Detect file type from filename
     */
    public String detectFileType(String filename) {
        if (filename == null || filename.isEmpty()) {
            throw new IllegalArgumentException("Filename cannot be null or empty");
        }

        String lowerCaseFilename = filename.toLowerCase();
        if (lowerCaseFilename.endsWith(".csv")) {
            return "csv";
        } else if (lowerCaseFilename.endsWith(".json")) {
            return "json";
        } else {
            throw new IllegalArgumentException(
                    "Unsupported file type. Only CSV and JSON files are supported.");
        }
    }

    /**
     * Parse CSV file in streaming mode
     * Returns a stream of maps representing each record
     */
    public Stream<Map<String, String>> parseCsvStream(MultipartFile file) throws IOException {
        log.info("Parsing CSV file: {}", file.getOriginalFilename());

        BufferedReader reader = new BufferedReader(
                new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8));

        CSVParser csvParser = new CSVParser(reader, CSVFormat.DEFAULT
                .builder()
                .setHeader()
                .setSkipHeaderRecord(true)
                .setTrim(true)
                .setIgnoreEmptyLines(true)
                .build());

        return StreamSupport.stream(csvParser.spliterator(), false)
                .map(this::csvRecordToMap)
                .onClose(() -> {
                    try {
                        csvParser.close();
                        reader.close();
                    } catch (IOException e) {
                        log.error("Error closing CSV parser", e);
                    }
                });
    }

    /**
     * Convert CSVRecord to Map
     */
    private Map<String, String> csvRecordToMap(CSVRecord record) {
        Map<String, String> map = new HashMap<>();
        record.toMap().forEach((key, value) -> {
            if (key != null && !key.trim().isEmpty()) {
                map.put(key.trim(), value != null && !value.trim().isEmpty() ? value.trim() : null);
            }
        });
        return map;
    }

    /**
     * Parse JSON file in streaming mode
     * Supports both JSON arrays and NDJSON (newline-delimited JSON)
     */
    public Stream<Map<String, String>> parseJsonStream(MultipartFile file) throws IOException {
        log.info("Parsing JSON file: {}", file.getOriginalFilename());

        BufferedReader reader = new BufferedReader(
                new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8));

        // Try to parse as JSON array first
        try {
            JsonNode rootNode = objectMapper.readTree(file.getInputStream());

            if (rootNode.isArray()) {
                // JSON array format
                List<Map<String, String>> records = new ArrayList<>();
                for (JsonNode node : rootNode) {
                    records.add(jsonNodeToMap(node));
                }
                return records.stream();
            } else if (rootNode.isObject()) {
                // Single JSON object
                return Stream.of(jsonNodeToMap(rootNode));
            } else {
                throw new IllegalArgumentException(
                        "JSON must be an array of objects or a single object");
            }
        } catch (IOException e) {
            // Try parsing as NDJSON (newline-delimited JSON)
            log.info("Attempting to parse as NDJSON format");
            return parseNdjsonStream(reader);
        }
    }

    /**
     * Parse NDJSON (newline-delimited JSON) format
     */
    private Stream<Map<String, String>> parseNdjsonStream(BufferedReader reader) {
        return reader.lines()
                .filter(line -> line != null && !line.trim().isEmpty())
                .map(line -> {
                    try {
                        JsonNode node = objectMapper.readTree(line);
                        return jsonNodeToMap(node);
                    } catch (IOException e) {
                        log.error("Error parsing JSON line: {}", line, e);
                        throw new RuntimeException(
                                "Invalid JSON line: " + line.substring(0, Math.min(50, line.length())), e);
                    }
                })
                .onClose(() -> {
                    try {
                        reader.close();
                    } catch (IOException e) {
                        log.error("Error closing NDJSON reader", e);
                    }
                });
    }

    /**
     * Convert JsonNode to Map<String, String>
     */
    private Map<String, String> jsonNodeToMap(JsonNode node) {
        Map<String, String> map = new HashMap<>();
        Iterator<String> fieldNames = node.fieldNames();

        while (fieldNames.hasNext()) {
            String key = fieldNames.next();
            JsonNode value = node.get(key);

            if (value.isNull()) {
                map.put(key, null);
            } else if (value.isTextual()) {
                map.put(key, value.asText());
            } else {
                map.put(key, value.toString());
            }
        }
        return map;
    }

    /**
     * Parse file based on its type
     */
    public Stream<Map<String, String>> parseFile(MultipartFile file) throws IOException {
        String fileType = detectFileType(file.getOriginalFilename());

        if ("csv".equals(fileType)) {
            return parseCsvStream(file);
        } else if ("json".equals(fileType)) {
            return parseJsonStream(file);
        } else {
            throw new IllegalArgumentException("Unsupported file type: " + fileType);
        }
    }

    /**
     * Chunk records into batches for efficient processing
     */
    public <T> Stream<List<T>> chunkStream(Stream<T> stream, int chunkSize) {
        Iterator<T> iterator = stream.iterator();
        List<List<T>> chunks = new ArrayList<>();

        while (iterator.hasNext()) {
            List<T> chunk = new ArrayList<>();
            for (int i = 0; i < chunkSize && iterator.hasNext(); i++) {
                chunk.add(iterator.next());
            }
            chunks.add(chunk);
        }

        return chunks.stream();
    }

    public int getChunkSize() {
        return chunkSize;
    }
}
