# Proyecto de Microservicios

Un sistema distribuido construido con Flask que implementa una arquitectura de microservicios para gestión de usuarios, autenticación y tareas.

## Arquitectura

El proyecto está compuesto por los siguientes servicios:

- **API Gateway** (Puerto 5000): Punto de entrada único que enruta las peticiones a los microservicios correspondientes
- **Auth Service** (Puerto 5001): Maneja el registro y autenticación de usuarios
- **User Service** (Puerto 5002): Gestiona las operaciones CRUD de usuarios
- **Task Service** (Puerto 5003): Administra las tareas del sistema

## Estructura del Proyecto

```
Microservicio/
├── api_gateway/
│   └── app.py
├── auth_service/
│   └── app.py
├── user_service/
│   └── app.py
├── task_service/
│   ├── app.py
│   └── conexion.py
├── logs/
├── start_services.sh
├── stop_services.sh
└── vent/ (entorno virtual)
```

## Instalación y Configuración

### Prerrequisitos

- Python 3.7+
- MySQL Server
- pip (gestor de paquetes de Python)

### Configuración de la Base de Datos

1. **Crear la base de datos:**
```sql
CREATE DATABASE seguridad;
USE seguridad;
```

2. **Crear la tabla de tareas:**
```sql
CREATE TABLE task (
    id_task INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at DATETIME,
    dead_line DATETIME,
    status VARCHAR(50),
    isalive BOOLEAN DEFAULT TRUE
);
```

3. **Configurar credenciales:**
   - Editar `task_service/conexion.py` con tus credenciales de MySQL:
```python
def conexion():
    return mysql.connector.connect(
        host="localhost",
        user="tu_usuario",
        password="tu_contraseña",
        database="seguridad"
    )
```

### Instalación de Dependencias

1. **Crear y activar entorno virtual:**
```bash
python3 -m venv vent
source vent/Scripts/activate  # En Windows
# source vent/bin/activate    # En Linux/Mac
```

2. **Instalar dependencias:**
```bash
pip install flask requests mysql-connector-python
```

## Uso

### Iniciar los Servicios

**Opción 1: Script automático (recomendado)**
```bash
chmod +x start_services.sh
./start_services.sh
```

**Opción 2: Manual**
```bash
# Terminal 1 - API Gateway
cd api_gateway && python app.py

# Terminal 2 - Auth Service
cd auth_service && python app.py

# Terminal 3 - User Service
cd user_service && python app.py

# Terminal 4 - Task Service
cd task_service && python app.py
```

### Detener los Servicios

```bash
chmod +x stop_services.sh
./stop_services.sh
```

## API Endpoints

### Autenticación (vía API Gateway)

#### Registro de Usuario
```http
POST http://localhost:5000/auth/register
Content-Type: application/json

{
    "username": "nuevo_usuario",
    "password": "mi_contraseña"
}
```

#### Login
```http
POST http://localhost:5000/auth/login
Content-Type: application/json

{
    "username": "usuario_existente",
    "password": "mi_contraseña"
}
```

### Gestión de Usuarios (vía API Gateway)

#### Listar Usuarios
```http
GET http://localhost:5000/user/users
```

#### Obtener Usuario por ID
```http
GET http://localhost:5000/user/users/1
```

#### Crear Usuario
```http
POST http://localhost:5000/user/users
Content-Type: application/json

{
    "username": "nuevo_usuario",
    "email": "usuario@ejemplo.com"
}
```

#### Actualizar Usuario
```http
PUT http://localhost:5000/user/users/1
Content-Type: application/json

{
    "username": "usuario_actualizado",
    "email": "nuevo_email@ejemplo.com"
}
```

#### Eliminar Usuario
```http
DELETE http://localhost:5000/user/users/1
```

### Gestión de Tareas (Acceso Directo)

#### Crear Tarea
```http
POST http://localhost:5003/tasks
Content-Type: application/json

{
    "name": "Mi tarea",
    "description": "Descripción de la tarea",
    "dead_line": "2024-12-31 23:59:59",
    "status": "pendiente",
    "isalive": true
}
```

#### Listar Tareas
```http
GET http://localhost:5003/tasks
```

#### Obtener Tarea por ID
```http
GET http://localhost:5003/tasks/1
```

#### Actualizar Tarea
```http
PUT http://localhost:5003/tasks/1
Content-Type: application/json

{
    "name": "Tarea actualizada",
    "description": "Nueva descripción",
    "dead_line": "2024-12-31 23:59:59",
    "status": "completada",
    "isalive": true
}
```

#### Eliminar Tarea
```http
DELETE http://localhost:5003/tasks/1
```

## Características

- **API Gateway**: Enrutamiento centralizado de peticiones
- **Autenticación**: Sistema de registro y login con tokens simulados
- **Gestión de Usuarios**: CRUD completo para usuarios
- **Gestión de Tareas**: Sistema completo de administración de tareas con persistencia en MySQL
- **Logs**: Sistema de logging para monitoreo
- **Scripts de Control**: Automatización para iniciar/detener servicios

## Logs

Los logs de cada servicio se almacenan en la carpeta `logs/`:
- `api_gateway.log`
- `auth_service.log`
- `user_service.log`
- `task_service.log`

## Consideraciones de Seguridad

**Nota**: Este es un proyecto de demostración. Para producción, considera implementar:

- Autenticación JWT real
- Validación y sanitización de datos
- HTTPS
- Rate limiting
- Manejo seguro de contraseñas (hashing)
- Variables de entorno para configuración sensible

## Tecnologías Utilizadas

- **Python 3**: Lenguaje de programación
- **Flask**: Framework web
- **MySQL**: Base de datos
- **Requests**: Cliente HTTP para comunicación entre servicios

## Solución de Problemas

### Puerto en uso
Si obtienes errores de puerto en uso:
```bash
# Verificar puertos
lsof -i :5000
lsof -i :5001
lsof -i :5002
lsof -i :5003

# Terminar procesos si es necesario
kill -9 <PID>
```

### Error de conexión a MySQL
- Verificar que MySQL esté ejecutándose
- Confirmar credenciales en `conexion.py`
- Verificar que la base de datos `seguridad` exista

### Entorno virtual no encontrado
```bash
python3 -m venv vent
source vent/Scripts/activate
pip install flask requests mysql-connector-python
```

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto es de uso educativo y está disponible bajo la licencia MIT.