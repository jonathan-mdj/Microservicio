# task_service/app.py
from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime, timedelta
from auth import generate_token, token_required, hash_password, check_password
import jwt
import os
import bcrypt
from mysql.connector import Error

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_super_secreta_123')

# --- CONFIGURACIÓN DE BASE DE DATOS MYSQL ---
DB_CONFIG = {
    'host': 'localhost',
    'database': 'task_management',
    'user': 'task_admin',
    'password': '',
    'port': 3306,
    'auth_plugin': 'mysql_native_password'
}

def get_db_connection():
    """Obtener conexión a la base de datos MySQL"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error conectando a MySQL: {e}")
        return None

# --- INICIALIZACIÓN DE BASE DE DATOS ---
def init_db():
    """Crear tablas y datos iniciales"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    try:
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
        
        # Insertar roles iniciales
        cursor.execute("""
            INSERT IGNORE INTO roles (nombre) VALUES 
            ('admin'), ('user'), ('manager')
        """)
        
        # Insertar permisos iniciales
        cursor.execute("""
            INSERT IGNORE INTO permisos (nombre) VALUES 
            ('create_user'), ('read_user'), ('update_user'), ('delete_user'),
            ('create_role'), ('read_role'), ('update_role'), ('delete_role'),
            ('create_permission'), ('read_permission'), ('update_permission'), ('delete_permission'),
            ('create_task'), ('read_task'), ('update_task'), ('delete_task'),
            ('read_all_tasks'), ('manage_tasks')
        """)
        
        admin_password = hash_password('admin123')
        cursor.execute("""
            INSERT IGNORE INTO users (username, password, email, role_id) 
            VALUES ('admin', %s, 'admin@example.com', 
                   (SELECT id FROM roles WHERE nombre = 'admin'))
        """, (admin_password,))
        
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

def get_user_by_username(username):
    """Obtener usuario por username"""
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error obteniendo usuario: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Usuario y contraseña requeridos"}), 400
    
    user = get_user_by_username(data.get('username'))
    
    if user and check_password(user['password'], data.get('password')):
        token = generate_token(user['username'])
        return jsonify({
            "token": token, 
            "message": "Login exitoso",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role_id": user['role_id']
            }
        })
    return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username y password requeridos"}), 400
    
    if len(data['password']) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
    
    hashed_pw = hash_password(data['password'])
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (username, password, email, role_id) VALUES (%s, %s, %s, %s)',
            (data['username'], hashed_pw, data.get('email'), 2)  # 2 = role 'user' por defecto
        )
        connection.commit()
        return jsonify({"message": "Usuario creado exitosamente"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "El usuario ya existe"}), 400
    except Error as e:
        return jsonify({"error": f"Error creando usuario: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/tasks', methods=['GET'])
@token_required
def listar_tasks(current_user):
    """Obtener todas las tareas"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Obtener usuario actual para verificar permisos
        user = get_user_by_username(current_user)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Si es admin o manager, puede ver todas las tareas
        # Si es user normal, solo ve sus propias tareas
        if user['role_id'] == 1:  # admin
            cursor.execute("""
                SELECT t.*, u.username as created_by_username 
                FROM tasks t 
                JOIN users u ON t.created_by = u.id 
                WHERE t.is_alive = TRUE 
                ORDER BY t.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT t.*, u.username as created_by_username 
                FROM tasks t 
                JOIN users u ON t.created_by = u.id 
                WHERE t.created_by = %s AND t.is_alive = TRUE 
                ORDER BY t.created_at DESC
            """, (user['id'],))
        
        tasks = cursor.fetchall()
        return jsonify({
            "tasks": tasks,
            "count": len(tasks)
        })
    except Error as e:
        return jsonify({"error": f"Error obteniendo tareas: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/task', methods=['POST'])
@token_required
def crear_task(current_user):
    """Crear una nueva tarea"""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Nombre de la tarea requerido"}), 400
    
    user = get_user_by_username(current_user)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor()
    try:
        # Parsear deadline si se proporciona
        deadline = None
        if data.get('deadline'):
            try:
                deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return jsonify({"error": "Formato de deadline inválido. Use: YYYY-MM-DD HH:MM:SS"}), 400
        
        cursor.execute("""
            INSERT INTO tasks (name, description, deadline, status, created_by) 
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['name'],
            data.get('description', ''),
            deadline,
            data.get('status', 'In Progress'),
            user['id']
        ))
        
        connection.commit()
        task_id = cursor.lastrowid
        return jsonify({
            "message": "Tarea creada exitosamente",
            "task": {
                "id": task_id,
                "name": data['name'],
                "description": data.get('description', ''),
                "deadline": deadline.isoformat() if deadline else None,
                "status": data.get('status', 'In Progress'),
                "created_by": user['id']
            }
        }), 201
    except Error as e:
        return jsonify({"error": f"Error creando tarea: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/task/<int:task_id>', methods=['GET'])
@token_required
def obtener_task(current_user, task_id):
    """Obtener una tarea específica"""
    user = get_user_by_username(current_user)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.*, u.username as created_by_username 
            FROM tasks t 
            JOIN users u ON t.created_by = u.id 
            WHERE t.id = %s AND t.is_alive = TRUE
        """, (task_id,))
        
        task = cursor.fetchone()
        if not task:
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        # Verificar permisos: admin puede ver todo, users solo sus tareas
        if user['role_id'] != 1 and task['created_by'] != user['id']:
            return jsonify({"error": "No tienes permisos para ver esta tarea"}), 403
        
        return jsonify({"task": task})
    except Error as e:
        return jsonify({"error": f"Error obteniendo tarea: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/task/<int:task_id>', methods=['PUT'])
@token_required
def actualizar_task(current_user, task_id):
    """Actualizar una tarea existente"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos requeridos"}), 400
    
    user = get_user_by_username(current_user)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Verificar que la tarea existe y permisos
        cursor.execute('SELECT * FROM tasks WHERE id = %s AND is_alive = TRUE', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        # Verificar permisos: admin puede editar todo, users solo sus tareas
        if user['role_id'] != 1 and task['created_by'] != user['id']:
            return jsonify({"error": "No tienes permisos para editar esta tarea"}), 403
        
        # Preparar campos para actualizar
        update_fields = []
        values = []
        
        if 'name' in data:
            update_fields.append('name = %s')
            values.append(data['name'])
        
        if 'description' in data:
            update_fields.append('description = %s')
            values.append(data['description'])
        
        if 'deadline' in data:
            if data['deadline']:
                try:
                    deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S')
                    update_fields.append('deadline = %s')
                    values.append(deadline)
                except ValueError:
                    return jsonify({"error": "Formato de deadline inválido. Use: YYYY-MM-DD HH:MM:SS"}), 400
            else:
                update_fields.append('deadline = NULL')
        
        if 'status' in data:
            valid_statuses = ['In Progress', 'Revision', 'Completed', 'Paused']
            if data['status'] not in valid_statuses:
                return jsonify({"error": f"Status inválido. Debe ser uno de: {valid_statuses}"}), 400
            update_fields.append('status = %s')
            values.append(data['status'])
        
        if not update_fields:
            return jsonify({"error": "No hay campos para actualizar"}), 400
        
        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, values)
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "No se pudo actualizar la tarea"}), 400
        
        return jsonify({"message": "Tarea actualizada exitosamente"})
    except Error as e:
        return jsonify({"error": f"Error actualizando tarea: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/task/<int:task_id>', methods=['DELETE'])
@token_required
def eliminar_task(current_user, task_id):
    """Eliminar una tarea (soft delete)"""
    user = get_user_by_username(current_user)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Verificar que la tarea existe y permisos
        cursor.execute('SELECT * FROM tasks WHERE id = %s AND is_alive = TRUE', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        # Verificar permisos: admin puede eliminar todo, users solo sus tareas
        if user['role_id'] != 1 and task['created_by'] != user['id']:
            return jsonify({"error": "No tienes permisos para eliminar esta tarea"}), 403
        
        # Soft delete
        cursor.execute('UPDATE tasks SET is_alive = FALSE WHERE id = %s', (task_id,))
        connection.commit()
        
        return jsonify({"message": "Tarea eliminada exitosamente"})
    except Error as e:
        return jsonify({"error": f"Error eliminando tarea: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/tasks/status/<status>', methods=['GET'])
@token_required
def tasks_por_status(current_user, status):
    """Obtener tareas por status"""
    valid_statuses = ['In Progress', 'Revision', 'Completed', 'Paused']
    if status not in [s.replace(' ', '_').lower() for s in valid_statuses]:
        return jsonify({"error": f"Status inválido. Debe ser uno de: {valid_statuses}"}), 400
    
    # Convertir el status de URL a formato de DB
    status_map = {
        'in_progress': 'In Progress',
        'revision': 'Revision', 
        'completed': 'Completed',
        'paused': 'Paused'
    }
    db_status = status_map.get(status.lower(), status)
    
    user = get_user_by_username(current_user)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        if user['role_id'] == 1:  # admin
            cursor.execute("""
                SELECT t.*, u.username as created_by_username 
                FROM tasks t 
                JOIN users u ON t.created_by = u.id 
                WHERE t.status = %s AND t.is_alive = TRUE 
                ORDER BY t.created_at DESC
            """, (db_status,))
        else:
            cursor.execute("""
                SELECT t.*, u.username as created_by_username 
                FROM tasks t 
                JOIN users u ON t.created_by = u.id 
                WHERE t.status = %s AND t.created_by = %s AND t.is_alive = TRUE 
                ORDER BY t.created_at DESC
            """, (db_status, user['id']))
        
        tasks = cursor.fetchall()
        return jsonify({
            "tasks": tasks,
            "status": db_status,
            "count": len(tasks)
        })
    except Error as e:
        return jsonify({"error": f"Error obteniendo tareas: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/info', methods=['GET'])
@token_required
def info_sistema(current_user):
    """Información general del sistema"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM roles')
        total_roles = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM permisos')
        total_permisos = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM tasks WHERE is_alive = TRUE')
        total_tasks = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM tasks 
            WHERE is_alive = TRUE 
            GROUP BY status
        """)
        tasks_por_status = cursor.fetchall()
        
        return jsonify({
            "sistema": "API de Gestión de Tareas con JWT",
            "usuario_actual": current_user,
            "estadisticas": {
                "total_usuarios": total_users,
                "total_roles": total_roles,
                "total_permisos": total_permisos,
                "total_tareas": total_tasks,
                "tareas_por_status": {item['status']: item['count'] for item in tasks_por_status}
            }
        })
    except Error as e:
        return jsonify({"error": f"Error obteniendo información: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    if init_db():
        print("Iniciando Task Service en puerto 5003...")
        app.run(port=5003, debug=True)
    else:
        print("Error inicializando la base de datos. No se puede iniciar el servicio.")