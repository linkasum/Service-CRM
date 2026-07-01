-- Инициализация пустой базы (Система учёта для сервисных центров)
-- Запуск: psql -U postgres -d qwencrm -f init_db.sql

-- Роли
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT now()
);

INSERT INTO roles (id, name, description) VALUES 
    (1, 'admin', 'Администратор'),
    (2, 'master', 'Мастер'),
    (3, 'acceptor', 'Приёмщик'),
    (4, 'manager', 'Менеджер')
ON CONFLICT (id) DO NOTHING;

-- Пользователи (создать после roles)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200),
    password_hash VARCHAR(255) NOT NULL,
    role_id INT REFERENCES roles(id),
    phone VARCHAR(50),
    email VARCHAR(100),
    salary_config_id INT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);

-- Создать админа (пароль: admin)
INSERT INTO users (username, full_name, password_hash, role_id, is_active) 
VALUES ('admin', 'Администратор', '$2b$12$LJ3m4ys3GZfnYMz8kVC/NO7F6OqDk6dD7sLwA8vO4t5.6e3aDhDGi', 1, true)
ON CONFLICT (username) DO NOTHING;

-- Salary configs
CREATE TABLE IF NOT EXISTS salary_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    config_type VARCHAR(20) DEFAULT 'formula',
    formula_string TEXT,
    fixed_amount FLOAT,
    period VARCHAR(20) DEFAULT 'per_order',
    description TEXT,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now()
);

INSERT INTO salary_configs (id, name, config_type, formula_string, period, is_active) VALUES
    (33, 'Мастер 40%', 'formula', '({cash_net} + {card_net}) * 0.4', 'per_order', true),
    (31, 'Приёмщик 4000р', 'fixed', NULL, 'per_shift', true)
ON CONFLICT (id) DO NOTHING;

-- Cash shifts
CREATE TABLE IF NOT EXISTS cash_shifts (
    id SERIAL PRIMARY KEY,
    opened_at TIMESTAMP DEFAULT now(),
    closed_at TIMESTAMP,
    opened_by INT REFERENCES users(id),
    closed_by INT,
    initial_amount FLOAT DEFAULT 0,
    final_amount FLOAT DEFAULT 0,
    is_open BOOLEAN DEFAULT true
);

-- Cash transactions
CREATE TABLE IF NOT EXISTS cash_transactions (
    id SERIAL PRIMARY KEY,
    shift_id INT REFERENCES cash_shifts(id),
    order_id INT,
    transaction_type VARCHAR(20) DEFAULT 'income',
    amount FLOAT DEFAULT 0,
    payment_method VARCHAR(20) DEFAULT 'cash',
    comment TEXT,
    created_at TIMESTAMP DEFAULT now(),
    created_by INT REFERENCES users(id)
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(200) NOT NULL DEFAULT '-',
    client_phone VARCHAR(50) NOT NULL DEFAULT '-',
    client_email VARCHAR(100),
    device_model VARCHAR(200) NOT NULL DEFAULT '-',
    device_brand VARCHAR(100),
    device_category VARCHAR(100),
    serial_number VARCHAR(100),
    status VARCHAR(30) DEFAULT 'new',
    master_id INT REFERENCES users(id),
    acceptor_id INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT now(),
    issued_at TIMESTAMP,
    total_cost FLOAT DEFAULT 0,
    parts_cost FLOAT DEFAULT 0,
    work_cost FLOAT DEFAULT 0,
    complaint TEXT,
    appearance TEXT,
    accessories TEXT,
    warranty_days INT,
    is_warranty BOOLEAN DEFAULT false,
    diagnostic_act_text TEXT,
    comment TEXT
);

-- Work schedules
CREATE TABLE IF NOT EXISTS work_schedules (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    date DATE NOT NULL,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT now()
);

-- Working hours
CREATE TABLE IF NOT EXISTS working_hours (
    id SERIAL PRIMARY KEY,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20),
    is_working_day BOOLEAN DEFAULT true,
    start_time TIME DEFAULT '10:00',
    end_time TIME DEFAULT '20:00',
    lunch_start TIME,
    lunch_end TIME,
    description TEXT
);

INSERT INTO working_hours (day_of_week, day_name, is_working_day, start_time, end_time) VALUES
    (1, 'Понедельник', true, '10:00', '20:00'),
    (2, 'Вторник', true, '10:00', '20:00'),
    (3, 'Среда', true, '10:00', '20:00'),
    (4, 'Четверг', true, '10:00', '20:00'),
    (5, 'Пятница', true, '10:00', '20:00'),
    (6, 'Суббота', true, '10:00', '20:00'),
    (7, 'Воскресенье', true, '10:00', '20:00')
ON CONFLICT DO NOTHING;

-- Salary records
CREATE TABLE IF NOT EXISTS salary_records (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    order_id INT REFERENCES orders(id),
    calculated_amount FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'accrued',
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    comment TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Parts
CREATE TABLE IF NOT EXISTS parts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(300) NOT NULL,
    category VARCHAR(100),
    quantity INT DEFAULT 0,
    purchase_price FLOAT DEFAULT 0,
    sale_price FLOAT DEFAULT 0,
    min_quantity INT DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Order parts
CREATE TABLE IF NOT EXISTS order_parts (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    part_id INT REFERENCES parts(id),
    quantity INT DEFAULT 1,
    price_at_order FLOAT DEFAULT 0,
    master_id INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT now()
);

-- Order services
CREATE TABLE IF NOT EXISTS order_services (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    service_id INT,
    service_name VARCHAR(300),
    price_at_order FLOAT DEFAULT 0,
    quantity INT DEFAULT 1,
    comment TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Document templates
CREATE TABLE IF NOT EXISTS document_templates (
    id SERIAL PRIMARY KEY,
    updated_at TIMESTAMP DEFAULT now(),
    type VARCHAR(50) NOT NULL,
    content_template TEXT
);

-- Company settings
CREATE TABLE IF NOT EXISTS company_settings (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(300),
    inn VARCHAR(20),
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(100),
    account VARCHAR(30),
    bik VARCHAR(10),
    bank VARCHAR(300)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_ct_shift ON cash_transactions(shift_id);
CREATE INDEX IF NOT EXISTS idx_ct_order ON cash_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_ct_date ON cash_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_master ON orders(master_id);
CREATE INDEX IF NOT EXISTS idx_sr_user ON salary_records(user_id);
CREATE INDEX IF NOT EXISTS idx_sr_date ON salary_records(period_start);
CREATE INDEX IF NOT EXISTS idx_ws_date ON work_schedules(date);

-- Sequences
SELECT setval('roles_id_seq', COALESCE((SELECT max(id) FROM roles), 1));
SELECT setval('users_id_seq', COALESCE((SELECT max(id) FROM users), 1));
SELECT setval('salary_configs_id_seq', COALESCE((SELECT max(id) FROM salary_configs), 1));
