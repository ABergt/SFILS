
USE sfils_db;

SELECT
    COUNT(*) AS total_records,
    SUM(checkout_total) AS total_checkouts,
    SUM(renewal_total) AS total_renewals,
    ROUND(AVG(checkout_total), 2) AS avg_checkouts,
    ROUND(AVG(renewal_total), 2) AS avg_renewals
FROM library_usage_records;


SELECT
    p.patron_type_definition,
    COUNT(*) AS record_count,
    SUM(u.checkout_total) AS total_checkouts,
    SUM(u.renewal_total) AS total_renewals,
    ROUND(AVG(u.checkout_total), 2) AS avg_checkouts
FROM library_usage_records u
JOIN patron_types p
    ON u.patron_type_code = p.patron_type_code
GROUP BY p.patron_type_code, p.patron_type_definition
ORDER BY total_checkouts DESC;


SELECT
    l.home_library_code,
    l.home_library_definition,
    COUNT(*) AS record_count,
    SUM(u.checkout_total) AS total_checkouts,
    SUM(u.renewal_total) AS total_renewals
FROM library_usage_records u
LEFT JOIN libraries l
    ON u.library_id = l.library_id
GROUP BY l.library_id, l.home_library_code, l.home_library_definition
ORDER BY total_checkouts DESC;


SELECT
    age_range,
    COUNT(*) AS record_count,
    SUM(checkout_total) AS total_checkouts,
    SUM(renewal_total) AS total_renewals,
    ROUND(AVG(checkout_total), 2) AS avg_checkouts
FROM library_usage_records
GROUP BY age_range
ORDER BY age_range;


SELECT
    circulation_active_year,
    COUNT(*) AS record_count,
    SUM(checkout_total) AS total_checkouts,
    SUM(renewal_total) AS total_renewals
FROM library_usage_records
GROUP BY circulation_active_year
ORDER BY circulation_active_year;


SELECT
    circulation_active_month,
    COUNT(*) AS record_count,
    SUM(checkout_total) AS total_checkouts,
    SUM(renewal_total) AS total_renewals
FROM library_usage_records
GROUP BY circulation_active_month
ORDER BY circulation_active_month;


SELECT
    n.notification_medium_code,
    n.notification_code_definition,
    COUNT(*) AS record_count
FROM library_usage_records u
LEFT JOIN notification_preferences n
    ON u.notification_medium_code = n.notification_medium_code
GROUP BY
    n.notification_medium_code,
    n.notification_code_definition
ORDER BY record_count DESC;


SELECT
    provided_email_address,
    COUNT(*) AS record_count
FROM library_usage_records
GROUP BY provided_email_address;


SELECT
    within_san_francisco_county,
    COUNT(*) AS record_count
FROM library_usage_records
GROUP BY within_san_francisco_county;


SELECT
    year_patron_registered,
    COUNT(*) AS record_count
FROM library_usage_records
GROUP BY year_patron_registered
ORDER BY year_patron_registered;
