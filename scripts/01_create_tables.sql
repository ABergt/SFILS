
USE sfils_db;

CREATE TABLE IF NOT EXISTS patron_types (
    patron_type_code INT PRIMARY KEY,
    patron_type_definition VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS libraries (
    library_id INT AUTO_INCREMENT PRIMARY KEY,
    home_library_code VARCHAR(20) NULL UNIQUE,
    home_library_definition VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS age_ranges (
    age_range VARCHAR(50) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS notification_preferences (
    notification_medium_code VARCHAR(10) PRIMARY KEY,
    notification_code_definition VARCHAR(50) NULL
);

CREATE TABLE IF NOT EXISTS library_usage_records (
    record_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    patron_type_code INT NOT NULL,
    checkout_total INT NOT NULL,
    renewal_total INT NOT NULL,

    age_range VARCHAR(50) NULL,
    library_id INT NULL,

    circulation_active_month VARCHAR(20) NULL,
    circulation_active_year SMALLINT NULL,

    notification_medium_code VARCHAR(10) NULL,

    provided_email_address BOOLEAN NOT NULL,
    within_san_francisco_county BOOLEAN NOT NULL,
    year_patron_registered SMALLINT NOT NULL,

    CONSTRAINT fk_usage_patron_type
        FOREIGN KEY (patron_type_code)
        REFERENCES patron_types(patron_type_code),

    CONSTRAINT fk_usage_age_range
        FOREIGN KEY (age_range)
        REFERENCES age_ranges(age_range),

    CONSTRAINT fk_usage_library
        FOREIGN KEY (library_id)
        REFERENCES libraries(library_id),

    CONSTRAINT fk_usage_notification
        FOREIGN KEY (notification_medium_code)
        REFERENCES notification_preferences(notification_medium_code)
);
