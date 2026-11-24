
USE sfils_db;

CREATE INDEX idx_usage_circulation_period
ON library_usage_records (
    circulation_active_year,
    circulation_active_month
);

CREATE INDEX idx_usage_registration_year
ON library_usage_records (
    year_patron_registered
);
