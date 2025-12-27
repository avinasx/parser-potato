package com.parserpotato.service;

import com.parserpotato.dto.*;
import com.parserpotato.model.*;
import com.parserpotato.repository.*;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.*;

/**
 * Service for validating and loading data into the database
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class DataLoaderService {

    private final CustomerRepository customerRepository;
    private final ProductRepository productRepository;
    private final OrderRepository orderRepository;
    private final OrderItemRepository orderItemRepository;
    private final Validator validator;

    private final List<String> errors = new ArrayList<>();
    private int currentRow = 0;

    /**
     * Identify table type based on record fields
     */
    public String identifyTableType(Map<String, String> record) {
        Set<String> fields = record.keySet();

        // Check for order_item (must check before order since both have order_id)
        if (fields.contains("product_id") && fields.contains("quantity") &&
                fields.contains("unit_price") && fields.contains("subtotal")) {
            return "order_item";
        }

        // Check for customer
        if (fields.contains("customer_id") && fields.contains("email") &&
                !fields.contains("order_id") && !fields.contains("product_id")) {
            return "customer";
        }

        // Check for product
        if (fields.contains("product_id") && fields.contains("price") &&
                !fields.contains("order_id")) {
            return "product";
        }

        // Check for order
        if (fields.contains("order_id") && fields.contains("customer_id") &&
                fields.contains("order_date")) {
            return "order";
        }

        return "unknown";
    }

    /**
     * Validate and categorize records by table type
     */
    public Map<String, List<Object>> validateAndCategorize(List<Map<String, String>> records) {
        Map<String, List<Object>> categorized = new HashMap<>();
        categorized.put("customers", new ArrayList<>());
        categorized.put("products", new ArrayList<>());
        categorized.put("orders", new ArrayList<>());
        categorized.put("order_items", new ArrayList<>());

        errors.clear();
        currentRow = 0;

        for (Map<String, String> record : records) {
            currentRow++;
            try {
                String tableType = identifyTableType(record);

                switch (tableType) {
                    case "customer":
                        CustomerDTO customerDTO = mapToCustomerDTO(record);
                        if (validateDTO(customerDTO, currentRow)) {
                            categorized.get("customers").add(customerDTO);
                        }
                        break;

                    case "product":
                        ProductDTO productDTO = mapToProductDTO(record);
                        if (validateDTO(productDTO, currentRow)) {
                            categorized.get("products").add(productDTO);
                        }
                        break;

                    case "order":
                        OrderDTO orderDTO = mapToOrderDTO(record);
                        if (validateDTO(orderDTO, currentRow)) {
                            categorized.get("orders").add(orderDTO);
                        }
                        break;

                    case "order_item":
                        OrderItemDTO orderItemDTO = mapToOrderItemDTO(record);
                        if (validateDTO(orderItemDTO, currentRow)) {
                            categorized.get("order_items").add(orderItemDTO);
                        }
                        break;

                    default:
                        errors.add("Row " + currentRow + ": Unable to identify table type");
                }
            } catch (Exception e) {
                errors.add("Row " + currentRow + ": " + e.getMessage());
            }
        }

        return categorized;
    }

    /**
     * Validate DTO using Bean Validation
     */
    private <T> boolean validateDTO(T dto, int rowNum) {
        Set<ConstraintViolation<T>> violations = validator.validate(dto);

        if (!violations.isEmpty()) {
            for (ConstraintViolation<T> violation : violations) {
                errors.add("Row " + rowNum + ": " + violation.getMessage());
            }
            return false;
        }
        return true;
    }

    /**
     * Map record to CustomerDTO
     */
    private CustomerDTO mapToCustomerDTO(Map<String, String> record) {
        CustomerDTO dto = new CustomerDTO();
        dto.setCustomerId(record.get("customer_id"));
        dto.setName(record.get("name"));
        dto.setEmail(record.get("email"));
        dto.setPhone(record.get("phone"));
        dto.setAddress(record.get("address"));
        return dto;
    }

    /**
     * Map record to ProductDTO
     */
    private ProductDTO mapToProductDTO(Map<String, String> record) {
        ProductDTO dto = new ProductDTO();
        dto.setProductId(record.get("product_id"));
        dto.setName(record.get("name"));
        dto.setDescription(record.get("description"));
        dto.setPrice(parseDouble(record.get("price"), "price"));
        dto.setCategory(record.get("category"));
        dto.setStockQuantity(parseInt(record.get("stock_quantity"), 0));
        return dto;
    }

    /**
     * Map record to OrderDTO
     */
    private OrderDTO mapToOrderDTO(Map<String, String> record) {
        OrderDTO dto = new OrderDTO();
        dto.setOrderId(record.get("order_id"));
        dto.setCustomerId(record.get("customer_id"));
        dto.setOrderDate(parseDateTime(record.get("order_date")));
        dto.setStatus(record.get("status") != null ? record.get("status").toLowerCase() : null);
        dto.setTotalAmount(parseDouble(record.get("total_amount"), "total_amount"));
        return dto;
    }

    /**
     * Map record to OrderItemDTO
     */
    private OrderItemDTO mapToOrderItemDTO(Map<String, String> record) {
        OrderItemDTO dto = new OrderItemDTO();
        dto.setOrderId(record.get("order_id"));
        dto.setProductId(record.get("product_id"));
        dto.setQuantity(parseInt(record.get("quantity"), null));
        dto.setUnitPrice(parseDouble(record.get("unit_price"), "unit_price"));
        dto.setSubtotal(parseDouble(record.get("subtotal"), "subtotal"));
        return dto;
    }

    /**
     * Parse double value
     */
    private Double parseDouble(String value, String fieldName) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        try {
            return Double.parseDouble(value.trim());
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid " + fieldName + ": " + value);
        }
    }

    /**
     * Parse integer value
     */
    private Integer parseInt(String value, Integer defaultValue) {
        if (value == null || value.trim().isEmpty()) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid integer value: " + value);
        }
    }

    /**
     * Parse date time value
     */
    private LocalDateTime parseDateTime(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        try {
            // Try common formats
            DateTimeFormatter[] formatters = {
                    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"),
                    DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss"),
                    DateTimeFormatter.ISO_DATE_TIME
            };

            for (DateTimeFormatter formatter : formatters) {
                try {
                    return LocalDateTime.parse(value.trim(), formatter);
                } catch (DateTimeParseException ignored) {
                }
            }
            throw new IllegalArgumentException("Unable to parse date: " + value);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid date format: " + value);
        }
    }

    /**
     * Verify foreign key relationships
     */
    @Transactional(readOnly = true)
    public boolean verifyRelationships(Map<String, List<Object>> categorized) {
        // Get existing customer IDs
        Set<String> existingCustomerIds = new HashSet<>();
        customerRepository.findAll().forEach(c -> existingCustomerIds.add(c.getCustomerId()));

        // Add newly added customers
        categorized.get("customers").forEach(c -> {
            CustomerDTO dto = (CustomerDTO) c;
            existingCustomerIds.add(dto.getCustomerId());
        });

        // Get existing product IDs
        Set<String> existingProductIds = new HashSet<>();
        productRepository.findAll().forEach(p -> existingProductIds.add(p.getProductId()));

        // Add newly added products
        categorized.get("products").forEach(p -> {
            ProductDTO dto = (ProductDTO) p;
            existingProductIds.add(dto.getProductId());
        });

        // Get existing order IDs
        Set<String> existingOrderIds = new HashSet<>();
        orderRepository.findAll().forEach(o -> existingOrderIds.add(o.getOrderId()));

        // Add newly added orders
        categorized.get("orders").forEach(o -> {
            OrderDTO dto = (OrderDTO) o;
            existingOrderIds.add(dto.getOrderId());
        });

        // Verify orders reference existing customers
        for (Object obj : categorized.get("orders")) {
            OrderDTO dto = (OrderDTO) obj;
            if (!existingCustomerIds.contains(dto.getCustomerId())) {
                errors.add("Order " + dto.getOrderId() + " references non-existent customer: " + dto.getCustomerId());
            }
        }

        // Verify order items reference existing orders and products
        for (Object obj : categorized.get("order_items")) {
            OrderItemDTO dto = (OrderItemDTO) obj;
            if (!existingOrderIds.contains(dto.getOrderId())) {
                errors.add("OrderItem references non-existent order: " + dto.getOrderId());
            }
            if (!existingProductIds.contains(dto.getProductId())) {
                errors.add("OrderItem references non-existent product: " + dto.getProductId());
            }
        }

        return errors.isEmpty();
    }

    /**
     * Load data in batch mode
     */
    @Transactional
    public int[] loadDataBatch(Map<String, List<Object>> categorized) {
        int customersCount = 0;
        int productsCount = 0;
        int ordersCount = 0;
        int orderItemsCount = 0;

        // Insert customers
        List<Customer> customersToSave = new ArrayList<>();
        for (Object obj : categorized.get("customers")) {
            CustomerDTO dto = (CustomerDTO) obj;
            if (!customerRepository.existsByCustomerId(dto.getCustomerId())) {
                Customer customer = new Customer();
                customer.setCustomerId(dto.getCustomerId());
                customer.setName(dto.getName());
                customer.setEmail(dto.getEmail());
                customer.setPhone(dto.getPhone());
                customer.setAddress(dto.getAddress());
                customersToSave.add(customer);
            }
        }
        if (!customersToSave.isEmpty()) {
            customerRepository.saveAll(customersToSave);
            customersCount = customersToSave.size();
        }

        // Insert products
        List<Product> productsToSave = new ArrayList<>();
        for (Object obj : categorized.get("products")) {
            ProductDTO dto = (ProductDTO) obj;
            if (!productRepository.existsByProductId(dto.getProductId())) {
                Product product = new Product();
                product.setProductId(dto.getProductId());
                product.setName(dto.getName());
                product.setDescription(dto.getDescription());
                product.setPrice(dto.getPrice());
                product.setCategory(dto.getCategory());
                product.setStockQuantity(dto.getStockQuantity());
                productsToSave.add(product);
            }
        }
        if (!productsToSave.isEmpty()) {
            productRepository.saveAll(productsToSave);
            productsCount = productsToSave.size();
        }

        // Insert orders
        List<Order> ordersToSave = new ArrayList<>();
        for (Object obj : categorized.get("orders")) {
            OrderDTO dto = (OrderDTO) obj;
            if (!orderRepository.existsByOrderId(dto.getOrderId())) {
                Order order = new Order();
                order.setOrderId(dto.getOrderId());
                order.setCustomerId(dto.getCustomerId());
                order.setOrderDate(dto.getOrderDate());
                order.setStatus(dto.getStatus());
                order.setTotalAmount(dto.getTotalAmount());
                ordersToSave.add(order);
            }
        }
        if (!ordersToSave.isEmpty()) {
            orderRepository.saveAll(ordersToSave);
            ordersCount = ordersToSave.size();
        }

        // Insert order items
        List<OrderItem> orderItemsToSave = new ArrayList<>();
        for (Object obj : categorized.get("order_items")) {
            OrderItemDTO dto = (OrderItemDTO) obj;
            OrderItem orderItem = new OrderItem();
            orderItem.setOrderId(dto.getOrderId());
            orderItem.setProductId(dto.getProductId());
            orderItem.setQuantity(dto.getQuantity());
            orderItem.setUnitPrice(dto.getUnitPrice());
            orderItem.setSubtotal(dto.getSubtotal());
            orderItemsToSave.add(orderItem);
        }
        if (!orderItemsToSave.isEmpty()) {
            orderItemRepository.saveAll(orderItemsToSave);
            orderItemsCount = orderItemsToSave.size();
        }

        return new int[] { customersCount, productsCount, ordersCount, orderItemsCount };
    }

    public List<String> getErrors() {
        return new ArrayList<>(errors);
    }

    public void clearErrors() {
        errors.clear();
        currentRow = 0;
    }
}
