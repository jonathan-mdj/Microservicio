# task_service/database.py
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

class DatabaseConfig:
    """Configuración centralizada de la base de datos"""
    
    # Configuración de la base de datos MySQL
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'task_management',
        'user': 'task_admin',
        'password': '',
        'port': 3306,
        'auth_plugin': 'mysql_native_password'
    }

    @staticmethod
    def get_connection():
        """Obtener conexión a la base de datos MySQL"""
        try:
            connection = mysql.connector.connect(**DatabaseConfig.DB_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error conectando a MySQL: {e}")
            return None

    @staticmethod
    def test_connection():
        """Probar la conexión a la base de datos"""
        connection = DatabaseConfig.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                print("Conexión a MySQL exitosa")
                return True
            except Error as e:
                print(f"Error probando conexión: {e}")
                return False
        return False

    @staticmethod
    def initialize_database():
        """Inicializar la base de datos con tablas y datos iniciales"""
        connection = DatabaseConfig.get_connection()
        if not connection:
            print("No se pudo conectar a la base de datos")
            return False

        cursor = connection.cursor()
        
        try:
            print("Inicializando base de datos...")
            
            # Crear tabla de roles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(50) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de permisos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS permisos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    role_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            """)
            
            # Crear tabla de relación roles-permisos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles_permisos (
                    role_id INT NOT NULL,
                    permiso_id INT NOT NULL,
                    PRIMARY KEY (role_id, permiso_id),
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                    FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
                )
            """)
            
            # Crear tabla de TASKS
            cursor.execute("""
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
                )
            """)
            
            # Crear índices para optimización
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_is_alive ON tasks(is_alive)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            
            # Insertar datos iniciales
            DatabaseConfig._insert_initial_data(cursor)
            
            connection.commit()
            print("Base de datos inicializada correctamente")
            return True
            
        except Error as e:
            print(f"Error inicializando base de datos: {e}")
            connection.rollback()
            return False
        
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _insert_initial_data(cursor):
        """Insertar datos iniciales en las tablas"""
        from auth import hash_password
        
        # Insertar roles iniciales
        cursor.execute("""
            INSERT IGNORE INTO roles (nombre) VALUES 
            ('admin'), ('user'), ('manager')
        """)
        
        # Insertar permisos iniciales
        permisos = [
            'create_user', 'read_user', 'update_user', 'delete_user',
            'create_role', 'read_role', 'update_role', 'delete_role',
            'create_permission', 'read_permission', 'update_permission', 'delete_permission',
            'create_task', 'read_task', 'update_task', 'delete_task',
            'read_all_tasks', 'manage_tasks'
        ]
        
        for permiso in permisos:
            cursor.execute("INSERT IGNORE INTO permisos (nombre) VALUES (%s)", (permiso,))
        
        # Crear usuario admin inicial
        admin_password = hash_password('admin123')
        cursor.execute("""
            INSERT IGNORE INTO users (username, password, email, role_id) 
            VALUES ('admin', %s, 'admin@taskmanager.com', 
                   (SELECT id FROM roles WHERE nombre = 'admin'))
        """, (admin_password,))
        
        # Crear usuario de prueba normal
        user_password = hash_password('user123')
        cursor.execute("""
            INSERT IGNORE INTO users (username, password, email, role_id) 
            VALUES ('testuser', %s, 'user@taskmanager.com', 
                   (SELECT id FROM roles WHERE nombre = 'user'))
        """, (user_password,))
        
        print("Datos iniciales insertados:")
        print("Usuario admin: admin / admin123")
        print("Usuario test: testuser / user123")

# Función auxiliar para usar en app.py
def get_db_connection():
    """Función auxiliar para obtener conexión - compatible con código existente"""
    return DatabaseConfig.get_connection()

def init_db():
    """Función auxiliar para inicializar DB - compatible con código existente"""
    return DatabaseConfig.initialize_database()