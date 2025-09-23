CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE task_status AS ENUM ('pending', 'running', 'success', 'cancelled', 'failed');

CREATE TABLE IF NOT EXISTS request_center (
    task_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    n_sample INT NOT NULL,
    disease VARCHAR(100),
    filters VARCHAR(2048),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    queried_data_uri VARCHAR(2048),
    status task_status
);
