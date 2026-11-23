-- schema.sql
-- IT Ticket Support System, Ceres Solutions

-- DS-01: Ticket Table
CREATE TABLE ds_01 (
    ticket_id VARCHAR(50) PRIMARY KEY,
    employee_email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'Open'
        CHECK (status IN ('Open', 'Assigned', 'Resolved')),
    priority VARCHAR(20) NOT NULL DEFAULT 'Medium'
        CHECK (priority IN ('Low', 'Medium', 'High')),
    equipment VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    internal_note TEXT
);

CREATE INDEX idx_ds_01_equipment ON ds_01(equipment);

-- DS-02: Login Table
CREATE TABLE ds_02 (
    technician_email VARCHAR(255) PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL
);

-- DS-03: Status Lookup Table
CREATE TABLE ds_03 (
    ticket_id VARCHAR(50) PRIMARY KEY,
    employee_email VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('Open', 'Assigned', 'Resolved')),
    FOREIGN KEY (ticket_id)
        REFERENCES ds_01(ticket_id)
        ON DELETE CASCADE
);