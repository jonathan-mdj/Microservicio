#! /bin/bash

LOG_DIR = "${pwd}/logs"

# Función para detener servicios
stop_service() {
    local service_name = $1
    local pid_file = "$LOG_DIR/$service_name.pid"

    if [ -f "$pid_file" ]; then 
        local pid = $(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "Detenido $service_name (PID: $pid)..."
            kill $pid
            rm "$pid_file"
        else
            echo "No se encontró un proceso activo para $service_name"
            rm "$pid_file"
        fi
    else
    echo "No se encontró el archivo PID para $service_name"
}

# Detener cada mircroservicio
stop_service "api_gateway"
stop_service "auth_service"
stop_service "user_service"

echo "Todos los servicios se han detenido"