package com.parserpotato.repository;

import com.parserpotato.model.Order;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repository for Order entity
 */
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    /**
     * Find order by orderId
     */
    Optional<Order> findByOrderId(String orderId);

    /**
     * Check if order exists by orderId
     */
    boolean existsByOrderId(String orderId);
}
