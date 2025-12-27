package com.parserpotato.repository;

import com.parserpotato.model.Customer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repository for Customer entity
 */
@Repository
public interface CustomerRepository extends JpaRepository<Customer, Long> {

    /**
     * Find customer by customerId
     */
    Optional<Customer> findByCustomerId(String customerId);

    /**
     * Check if customer exists by customerId
     */
    boolean existsByCustomerId(String customerId);
}
