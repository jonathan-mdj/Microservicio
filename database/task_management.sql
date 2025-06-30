-- ==================================================
-- CONFIGURACIÓN DE BASE DE DATOS MYSQL
-- Sistema de Gestión de Tareas con JWT
-- ==================================================

-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS task_management;
USE task_management;

-- ==================================================
-- TABLA DE ROLES
-- ==================================================
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================================================
-- TABLA DE PERMISOS
-- ==================================================
CREATE TABLE IF NOT EXISTS permisos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================================================
-- TABLA DE USUARIOS
-- ==================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    role_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- ==================================================
-- TABLA DE RELACIÓN ROLES-PERMISOS
-- ==================================================
CREATE TABLE IF NOT EXISTS roles_permisos (
    role_id INT NOT NULL,
    permiso_id INT NOT NULL,
    PRIMARY KEY (role_id, permiso_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
);

-- ==================================================
-- TABLA DE TASKS (PRINCIPAL)
-- ==================================================
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deadline DATETIME,
    status ENUM('In Progress', 'Revision', 'Completed', 'Paused') DEFAULT 'In Progress',
    is_alive BOOLEAN DEFAULT TRUE,
    created_by INT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ==================================================
-- INSERTAR DATOS INICIALES
-- ==================================================

-- Insertar roles iniciales
INSERT IGNORE INTO roles (nombre) VALUES 
('admin'), 
('user'), 
('manager');

-- Insertar permisos iniciales
INSERT IGNORE INTO permisos (nombre) VALUES 
('create_user'), ('read_user'), ('update_user'), ('delete_user'),
('create_role'), ('read_role'), ('update_role'), ('delete_role'),
('create_permission'), ('read_permission'), ('update_permission'), ('delete_permission'),
('create_task'), ('read_task'), ('update_task'), ('delete_task'),
('read_all_tasks'), ('manage_tasks');

-- Asignar todos los permisos al rol admin
INSERT IGNORE INTO roles_permisos (role_id, permiso_id)
SELECT 
    (SELECT id FROM roles WHERE nombre = 'admin') as role_id,
    p.id as permiso_id
FROM permisos p;

-- Asignar permisos básicos al rol user
INSERT IGNORE INTO roles_permisos (role_id, permiso_id)
SELECT 
    (SELECT id FROM roles WHERE nombre = 'user') as role_id,
    p.id as permiso_id
FROM permisos p 
WHERE p.nombre IN ('read_user', 'create_task', 'read_task', 'update_task', 'delete_task');

-- Asignar permisos de manager
INSERT IGNORE INTO roles_permisos (role_id, permiso_id)
SELECT 
    (SELECT id FROM roles WHERE nombre = 'manager') as role_id,
    p.id as permiso_id
FROM permisos p 
WHERE p.nombre IN ('read_user', 'create_task', 'read_task', 'update_task', 'delete_task', 'read_all_tasks', 'manage_tasks');

-- ==================================================
-- CREAR ÍNDICES PARA OPTIMIZACIÓN
-- ==================================================
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);
CREATE INDEX idx_tasks_deadline ON tasks(deadline);
CREATE INDEX idx_tasks_is_alive ON tasks(is_alive);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- ==================================================
-- VERIFICAR ESTRUCTURA DE TABLAS
-- ==================================================
SHOW TABLES;
DESCRIBE tasks;
DESCRIBE users;
DESCRIBE roles;
DESCRIBE permisos;
DESCRIBE roles_permisos;