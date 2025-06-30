# api_gateway/app.py
from flask import Flask, jsonify, request
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

app = Flask(__name__)

# URLs de los microservicios
AUTH_SERVICE_URL = 'http://localhost:5001'
USER_SERVICE_URL = 'http://localhost:5002'
TASK_SERVICE_URL = 'http://localhost:5003'  # Task Service

def proxy_request(service_url, path):
    """Función auxiliar para hacer proxy de requests"""
    url = f"{service_url}/{path}"
    
    headers = {}
    for key, value in request.headers:
        if key.lower() != 'host':
            headers[key] = value
    
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            json=request.get_json() if request.is_json else None,
            headers=headers,
            timeout=30
        )
        
        # Intentar devolver JSON, si no es posible devolver texto
        try:
            return jsonify(resp.json()), resp.status_code
        except ValueError:
            return resp.text, resp.status_code
            
    except ConnectionError:
        return jsonify({"error": "Servicio no disponible"}), 503
    except Timeout:
        return jsonify({"error": "Timeout del servicio"}), 504
    except RequestException as e:
        return jsonify({"error": f"Error en la solicitud: {str(e)}"}), 500


@app.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def auth_proxy(path):
    """Proxy para el servicio de autenticación"""
    return proxy_request(AUTH_SERVICE_URL, path)

@app.route('/user/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user_proxy(path):
    """Proxy para el servicio de usuarios"""
    return proxy_request(USER_SERVICE_URL, path)

# ===========================================
# ========= PROXY PARA TASK SERVICE ========
# ===========================================

# Endpoints de autenticación del Task Service
@app.route('/login', methods=['POST'])
def login_proxy():
    """Proxy directo para login del Task Service"""
    return proxy_request(TASK_SERVICE_URL, 'login')

@app.route('/register', methods=['POST'])
def register_proxy():
    """Proxy directo para registro del Task Service"""
    return proxy_request(TASK_SERVICE_URL, 'register')

# Endpoints principales de tareas
@app.route('/tasks', methods=['GET'])
def get_tasks_proxy():
    """Proxy para obtener todas las tareas"""
    return proxy_request(TASK_SERVICE_URL, 'tasks')

@app.route('/task', methods=['POST'])
def create_task_proxy():
    """Proxy para crear una nueva tarea"""
    return proxy_request(TASK_SERVICE_URL, 'task')

@app.route('/task/<int:task_id>', methods=['GET'])
def get_task_proxy(task_id):
    """Proxy para obtener una tarea específica"""
    return proxy_request(TASK_SERVICE_URL, f'task/{task_id}')

@app.route('/task/<int:task_id>', methods=['PUT'])
def update_task_proxy(task_id):
    """Proxy para actualizar una tarea"""
    return proxy_request(TASK_SERVICE_URL, f'task/{task_id}')

@app.route('/task/<int:task_id>', methods=['DELETE'])
def delete_task_proxy(task_id):
    """Proxy para eliminar una tarea"""
    return proxy_request(TASK_SERVICE_URL, f'task/{task_id}')

# Endpoints adicionales de tareas
@app.route('/tasks/status/<status>', methods=['GET'])
def tasks_by_status_proxy(status):
    """Proxy para obtener tareas por status"""
    return proxy_request(TASK_SERVICE_URL, f'tasks/status/{status}')

# Endpoint de información del sistema
@app.route('/info', methods=['GET'])
def info_proxy():
    """Proxy para información del sistema"""
    return proxy_request(TASK_SERVICE_URL, 'info')

@app.route('/health', methods=['GET'])
def health_check():
    """Verificar el estado de todos los servicios"""
    services = {
        'auth_service': AUTH_SERVICE_URL,
        'user_service': USER_SERVICE_URL,
        'task_service': TASK_SERVICE_URL
    }
    
    status = {}
    for service_name, service_url in services.items():
        try:
            # Intentar hacer ping a cada servicio
            resp = requests.get(f"{service_url}/health", timeout=5)
            status[service_name] = "UP" if resp.status_code == 200 else "DOWN"
        except:
            status[service_name] = "DOWN"
    
    overall_status = "UP" if all(s == "UP" for s in status.values()) else "DEGRADED"
    
    return jsonify({
        "status": overall_status,
        "services": status,
        "gateway_port": 4000,
        "timestamp": str(request.url)
    })

@app.route('/', methods=['GET'])
def root():
    """Documentación básica de la API Gateway"""
    return jsonify({
        "message": "API Gateway para Sistema de Gestión de Tareas con JWT",
        "version": "2.0.0",
        "gateway_port": 4000,
        "services": {
            "auth_service": f"{AUTH_SERVICE_URL} (Puerto 5001)",
            "user_service": f"{USER_SERVICE_URL} (Puerto 5002)", 
            "task_service": f"{TASK_SERVICE_URL} (Puerto 5003)"
        },
        "endpoints": {
            "authentication": {
                "login": "POST /login",
                "register": "POST /register"
            },
            "tasks": {
                "list_all": "GET /tasks",
                "create": "POST /task",
                "get_one": "GET /task/{id}",
                "update": "PUT /task/{id}",
                "delete": "DELETE /task/{id}",
                "by_status": "GET /tasks/status/{status}"
            },
            "system": {
                "health": "GET /health",
                "info": "GET /info (requiere autenticación)"
            }
        },
        "authentication": {
            "type": "JWT Bearer Token",
            "header": "Authorization: Bearer <token>",
            "expiration": "5 minutos",
            "note": "Token requerido para todos los endpoints excepto /login y /register"
        },
        "task_statuses": [
            "In Progress",
            "Revision", 
            "Completed",
            "Paused"
        ]
    })

if __name__ == '__main__':
    print("=" * 50)
    print("INICIANDO API GATEWAY")
    print("=" * 50)
    print("Gateway URL: http://localhost:4000")
    print("Documentación: http://localhost:4000/")
    print("Health Check: http://localhost:4000/health")
    print("=" * 50)
    print("SERVICIOS CONFIGURADOS:")
    print(f"   Auth Service:  {AUTH_SERVICE_URL}")
    print(f"   User Service:  {USER_SERVICE_URL}")
    print(f"   Task Service:  {TASK_SERVICE_URL}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=4000, debug=True)