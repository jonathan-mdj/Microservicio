#!/bin/bash
# Script para iniciar todos los microservicios del proyecto

PROJECT_DIR="$(pwd)"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"

if [ ! -d "$VENV_DIR" ]; then 
    echo "Error: No se encontró el entorno virtual en $VENV_DIR" 
    echo "Ejecuta: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "Activando entorno virtual..."
source "$VENV_DIR/bin/activate"

check_port(){
    local port=$1
    local service_name=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo "Error: Puerto $port ya está en uso por $service_name"
        echo "Ejecuta: ./stop_services.sh para detener servicios previos"
        return 1
    fi
    return 0
}

echo "Verificando puertos disponibles..."
check_port 4000 "API Gateway" || exit 1
check_port 5001 "Auth Service" || exit 1
check_port 5002 "User Service" || exit 1
check_port 5003 "Task Service" || exit 1

start_service(){
    local service_dir=$1
    local service_name=$2
    local port=$3
    local display_name=$4
    
    echo "Iniciando $display_name en puerto $port..."
    
    if [ ! -d "$PROJECT_DIR/$service_dir" ]; then
        echo "Error: Directorio $service_dir no encontrado"
        return 1
    fi
    
    if [ ! -f "$PROJECT_DIR/$service_dir/app.py" ]; then
        echo "Error: No se encuentra app.py en $service_dir"
        return 1
    fi
    
    cd "$PROJECT_DIR/$service_dir" || exit 1
    
    python app.py > "$LOG_DIR/$service_name.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$LOG_DIR/$service_name.pid"
    
    sleep 2
    if ps -p $pid > /dev/null; then
        echo "$display_name iniciado correctamente (PID: $pid)"
    else
        echo "Error iniciando $display_name"
        echo "Revisa el log: tail -f $LOG_DIR/$service_name.log"
        return 1
    fi
    
    cd "$PROJECT_DIR"
    return 0
}

# Edita start_services.sh y cambia la verificación de MySQL por:
echo "Verificando MySQL..."
if mysql -u task_admin - -e "SELECT 1" > /dev/null 2>&1; then
    echo "MySQL verificado correctamente"
else
    echo "Error: Fallo al conectar con MySQL"
    echo "Prueba ejecutar manualmente:"
    echo "mysql -u task_admin - -e \"SELECT 1\""
    echo "Continuando con el inicio de servicios..."
fi

echo "INICIANDO MICROSERVICIOS"

start_service "auth_service" "auth_service" 5001 "Auth Service" || exit 1
start_service "user_service" "user_service" 5002 "User Service" || exit 1
start_service "task_service" "task_service" 5003 "Task Service" || exit 1
start_service "api_gateway" "api_gateway" 4000 "API Gateway" || exit 1

echo "TODOS LOS SERVICIOS INICIADOS"
echo "URLs de los servicios:"
echo "API Gateway:  http://localhost:4000"
echo "Auth Service: http://localhost:5001"
echo "User Service: http://localhost:5002"
echo "Task Service: http://localhost:5003"
echo ""
echo "Endpoints principales:"
echo "Documentación: http://localhost:4000/"
echo "Health Check:  http://localhost:4000/health"
echo "Login:         http://localhost:4000/login"
echo "Registro:      http://localhost:4000/register"
echo "Tareas:        http://localhost:4000/tasks"
echo ""
echo "Logs:         ls -la $LOG_DIR/"
echo "Ver logs:     tail -f $LOG_DIR/[servicio].log"
echo "Detener:      ./stop_services.sh"