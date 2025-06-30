#!/bin/bash
# Script para detener todos los microservicios del proyecto

LOG_DIR="$(pwd)/logs"

stop_service() {
    local service_name=$1
    local display_name=$2
    local pid_file="$LOG_DIR/$service_name.pid"
    
    if [ -f "$pid_file" ]; then 
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Deteniendo $display_name (PID: $pid)..."
            kill $pid
            
            sleep 2
            
            if ps -p $pid > /dev/null 2>&1; then
                echo "Forzando cierre de $display_name..."
                kill -9 $pid
            fi
            
            rm "$pid_file"
            echo "$display_name detenido correctamente"
        else
            echo "Error: No se encontró proceso activo para $display_name"
            rm "$pid_file"
        fi
    else
        echo "Error: No se encontró archivo PID para $display_name"
    fi
}

check_ports() {
    echo "Verificando puertos después del cierre..."
    local ports=(4000 5001 5002 5003)
    local services=("API Gateway" "Auth Service" "User Service" "Task Service")
    
    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local service=${services[$i]}
        
        if lsof -i :$port > /dev/null 2>&1; then
            echo "Error: Puerto $port ($service) aún está en uso"
            local pid=$(lsof -ti :$port)
            echo "PID del proceso: $pid"
            echo "Para forzar: kill -9 $pid"
        else
            echo "Puerto $port ($service) liberado"
        fi
    done
}

echo "DETENIENDO MICROSERVICIOS"

stop_service "api_gateway" "API Gateway"
stop_service "task_service" "Task Service"
stop_service "user_service" "User Service"
stop_service "auth_service" "Auth Service"

echo ""
check_ports

echo ""
echo "PROCESO DE CIERRE COMPLETADO"
echo "Logs preservados en: $LOG_DIR/"
echo "Para ver logs: tail -f $LOG_DIR/[servicio].log"
echo "Para reiniciar: ./start_services.sh"