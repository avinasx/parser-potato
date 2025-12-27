package com.parserpotato.repository;

import com.parserpotato.model.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repository for Product entity
 */
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    /**
     * Find product by productId
     */
    Optional<Product> findByProductId(String productId);

    /**
     * Check if product exists by productId
     */
    boolean existsByProductId(String productId);
}
