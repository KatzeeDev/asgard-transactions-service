CREATE TABLE IF NOT EXISTS transactions (
    -- PRIMARY KEY: Application-generated ID instead of AUTO_INCREMENT
    -- Format: "TXN_YYYYMMDD_HHMMSS_TYPE_RANDOM"
    -- Example: "TXN_20250109_143052_AUTH_a3f9k2p8"
    -- Benefits: sortable by timestamp, human-readable, unique, non-sequential
    transaction_id VARCHAR(48) PRIMARY KEY,

    -- Transaction type defines the operation being performed
    -- AUTH: Initial authorization (reserves funds)
    -- CAPTURE: Captures previously authorized funds
    -- REFUND: Returns money to the customer
    type ENUM('AUTH', 'CAPTURE', 'REFUND') NOT NULL,

    -- Current state of the transaction
    -- PENDING: In process or awaiting external confirmation
    -- APPROVED: Successfully completed
    -- DECLINED: Rejected by validation or external system
    status ENUM('PENDING', 'APPROVED', 'DECLINED') NOT NULL DEFAULT 'PENDING',

    -- Transaction amount
    -- DECIMAL(12,2): up to 9,999,999,999.99 (12 total digits, 2 decimals)
    -- Example: 15000.50 represents $15,000.50 CLP
    amount DECIMAL(12,2) NOT NULL,

    -- Currency code following ISO 4217 standard
    -- CLP: Chilean Peso, USD: US Dollar, EUR: Euro
    currency CHAR(3) NOT NULL DEFAULT 'CLP',

    -- Merchant identifier who initiated the transaction
    -- Used for filtering and segmenting transactions by merchant
    merchant_id VARCHAR(64) NOT NULL,

    -- Merchant's unique order/purchase reference
    -- Example: "ORDER_2025_001", "CART_abc123", "INV_XYZ"
    order_reference VARCHAR(128) NOT NULL,

    -- Parent transaction ID for creating transaction chains
    -- NULL for AUTH transactions (they have no parent)
    -- CAPTURE points to its AUTH transaction
    -- REFUND points to its CAPTURE or AUTH transaction
    -- Creates the flow: AUTH -> CAPTURE -> REFUND
    parent_transaction_id VARCHAR(48) NULL,

    -- Flexible metadata in JSON format
    -- Stores additional custom data without schema modifications
    -- Example: {"product": "Laptop", "color": "black", "warranty_years": 2}
    -- NULL if no additional metadata is needed
    metadata JSON NULL,

    -- Audit: creation timestamp (automatically set by MySQL)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Audit: last update timestamp (automatically updated by MySQL)
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Performance indexes for common query patterns
    INDEX idx_merchant (merchant_id),
    INDEX idx_order (order_reference),
    INDEX idx_parent (parent_transaction_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),

    -- Foreign key constraint ensures referential integrity
    -- Prevents CAPTURE/REFUND from referencing non-existent parents
    -- ON DELETE RESTRICT: Cannot delete AUTH if it has child CAPTURE
    FOREIGN KEY (parent_transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
