#!/bin /bash
#! Scrip para iniciar tpdps los microservicios del proyecto
#! Activa eñ emtornp virtual y ejecuta cada sercivio en segundo plano

#! Definimos el directorio base del proyecto

PROJECT_DIR="$(pwd)"
VEN_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"

#! Creamos un directorio para los logs si no existe
mkdir -p "$LOG_DIR"

#!Verificamos si el entorno virutal existe

if [ ! -d "$VENV_DIR" ]; then 
echo "Error: No se encontró el entorno virtual en $VENV_DIR" 
exit 1
fi

#!Activamos el entorno virtual
source "$VENV_DIR/bin/activate"

#!Verifica,ps si los puertos están ocupados
chechk_port(){
    local port=$1
    if lsof -i :$sport > /dev/null; then
    echo "Error: El puerto $port ya esta en uso"
    exit 1
    fi
}

chechk_port 5000
chechk_port 5001
chechk_port 5002
chechk_port 5003

# Funcion para iniciar un servicio

start_service(){
    local service_dir=$1
    local service_name=$2
    local port=$3
    echo "Iniciando $service_name en el puerto $port..."
    cd "$PROJECT_DIR/$service_dir" || exit 1
    python app.py > "$LOG_DIR/$service_name.log" 2>&1 &
   echo "$!" > "$LOG_DIR"/$service_name.pid"
   cd "$PROJECT_DIR"
}

#Iniciamos cada microservicio

start_service "api_gateway" "api_gateway" 5000
start_service "auth_service"