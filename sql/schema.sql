CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    capacity INT NOT NULL,
    tablename VARCHAR(255) NOT NULL,
    active BOOL NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    resource_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    CHECK (end_time > start_time)
);

DROP TRIGGER IF EXISTS customers_before_insert;
DROP TRIGGER IF EXISTS customers_before_update;
DROP TRIGGER IF EXISTS resources_before_insert;
DROP TRIGGER IF EXISTS resources_before_update;
DROP TRIGGER IF EXISTS bookings_before_insert;
DROP TRIGGER IF EXISTS bookings_before_update;

DROP PROCEDURE IF EXISTS list_customers;
DROP PROCEDURE IF EXISTS create_customer;
DROP PROCEDURE IF EXISTS list_resources;
DROP PROCEDURE IF EXISTS create_restaurant_table;
DROP PROCEDURE IF EXISTS list_available_resources;
DROP PROCEDURE IF EXISTS list_bookings;
DROP PROCEDURE IF EXISTS list_bookings_for_resource;
DROP PROCEDURE IF EXISTS create_booking;
DROP PROCEDURE IF EXISTS cancel_booking;

DELIMITER $$

CREATE TRIGGER customers_before_insert
BEFORE INSERT ON customers
FOR EACH ROW
BEGIN
    SET NEW.name = TRIM(NEW.name);
    SET NEW.email = LOWER(TRIM(NEW.email));

    IF CHAR_LENGTH(NEW.name) < 2 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Customer name must be at least 2 characters';
    END IF;

    IF NEW.email NOT LIKE '%@example.com' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only @example.com emails are allowed';
    END IF;
END$$

CREATE TRIGGER customers_before_update
BEFORE UPDATE ON customers
FOR EACH ROW
BEGIN
    SET NEW.name = TRIM(NEW.name);
    SET NEW.email = LOWER(TRIM(NEW.email));

    IF CHAR_LENGTH(NEW.name) < 2 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Customer name must be at least 2 characters';
    END IF;

    IF NEW.email NOT LIKE '%@example.com' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only @example.com emails are allowed';
    END IF;
END$$

CREATE TRIGGER resources_before_insert
BEFORE INSERT ON resources
FOR EACH ROW
BEGIN
    SET NEW.tablename = TRIM(NEW.tablename);

    IF CHAR_LENGTH(NEW.tablename) < 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Table name is required';
    END IF;

    IF NEW.capacity < 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Capacity must be at least 1';
    END IF;
END$$

CREATE TRIGGER resources_before_update
BEFORE UPDATE ON resources
FOR EACH ROW
BEGIN
    SET NEW.tablename = TRIM(NEW.tablename);

    IF CHAR_LENGTH(NEW.tablename) < 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Table name is required';
    END IF;

    IF NEW.capacity < 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Capacity must be at least 1';
    END IF;
END$$

CREATE TRIGGER bookings_before_insert
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    IF NEW.start_time >= NEW.end_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking start_time must be before end_time';
    END IF;
END$$

CREATE TRIGGER bookings_before_update
BEFORE UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF NEW.start_time >= NEW.end_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking start_time must be before end_time';
    END IF;
END$$

CREATE PROCEDURE list_customers()
BEGIN
    SELECT id, name, email
    FROM customers
    ORDER BY id;
END$$

CREATE PROCEDURE create_customer(
    IN p_name VARCHAR(100),
    IN p_email VARCHAR(255)
)
BEGIN
    INSERT INTO customers (name, email)
    VALUES (p_name, p_email);

    SELECT id, name, email
    FROM customers
    WHERE id = LAST_INSERT_ID();
END$$

CREATE PROCEDURE list_resources()
BEGIN
    SELECT id, capacity, tablename, active
    FROM resources
    ORDER BY id;
END$$

CREATE PROCEDURE create_restaurant_table(
    IN p_capacity INT,
    IN p_tablename VARCHAR(255),
    IN p_active BOOLEAN
)
BEGIN
    INSERT INTO resources (capacity, tablename, active)
    VALUES (p_capacity, p_tablename, p_active);

    SELECT id, capacity, tablename, active
    FROM resources
    WHERE id = LAST_INSERT_ID();
END$$

CREATE PROCEDURE list_available_resources(
    IN p_start_time DATETIME,
    IN p_end_time DATETIME
)
BEGIN
    IF p_start_time >= p_end_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking start_time must be before end_time';
    END IF;

    SELECT r.id, r.capacity, r.tablename, r.active
    FROM resources AS r
    WHERE r.active = TRUE
      AND NOT EXISTS (
          SELECT 1
          FROM bookings AS b
          WHERE b.resource_id = r.id
            AND b.start_time < p_end_time
            AND b.end_time > p_start_time
      )
    ORDER BY r.id;
END$$

CREATE PROCEDURE list_bookings()
BEGIN
    SELECT id, customer_id, resource_id, start_time, end_time
    FROM bookings
    ORDER BY start_time, id;
END$$

CREATE PROCEDURE list_bookings_for_resource(IN p_resource_id INT)
BEGIN
    DECLARE v_exists INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_exists
    FROM resources
    WHERE id = p_resource_id;

    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Resource does not exist';
    END IF;

    SELECT id, customer_id, resource_id, start_time, end_time
    FROM bookings
    WHERE resource_id = p_resource_id
    ORDER BY start_time, id;
END$$

CREATE PROCEDURE create_booking(
    IN p_customer_id INT,
    IN p_resource_id INT,
    IN p_start_time DATETIME,
    IN p_end_time DATETIME
)
BEGIN
    DECLARE v_customer_exists INT DEFAULT 0;
    DECLARE v_resource_active BOOLEAN DEFAULT NULL;
    DECLARE v_overlaps INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF p_start_time >= p_end_time THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking start_time must be before end_time';
    END IF;

    START TRANSACTION;

    SELECT COUNT(*)
    INTO v_customer_exists
    FROM customers
    WHERE id = p_customer_id;

    IF v_customer_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Customer does not exist';
    END IF;

    SELECT active
    INTO v_resource_active
    FROM resources
    WHERE id = p_resource_id
    FOR UPDATE;

    IF v_resource_active IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Resource does not exist';
    END IF;

    IF v_resource_active = FALSE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Resource is inactive';
    END IF;

    SELECT COUNT(*)
    INTO v_overlaps
    FROM bookings
    WHERE resource_id = p_resource_id
      AND start_time < p_end_time
      AND end_time > p_start_time;

    IF v_overlaps > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking overlaps an existing booking for this resource';
    END IF;

    INSERT INTO bookings (customer_id, resource_id, start_time, end_time)
    VALUES (p_customer_id, p_resource_id, p_start_time, p_end_time);

    COMMIT;

    SELECT id, customer_id, resource_id, start_time, end_time
    FROM bookings
    WHERE id = LAST_INSERT_ID();
END$$

CREATE PROCEDURE cancel_booking(IN p_booking_id INT)
BEGIN
    IF p_booking_id < 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking id must be at least 1';
    END IF;

    DELETE FROM bookings
    WHERE id = p_booking_id;

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking does not exist';
    END IF;
END$$

DELIMITER ;
