from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Lista en memoria para almacenar usuarios
users = [
    {"id": 1, "username": "user1", "password": "pass1"},
    {"id": 2, "username": "user2", "password": "pass2"}
]

@app.route('/register', methods=['POST'])
def register():
    # Validar que la solicitud tenga un cuerpo json y contenga 'username'
    if not request.json or 'username' not in request.json or 'password' not in request.json:
        # si faltan datos, devolver un error 400(Bad request)
        return jsonify({"error": "Invalid requests, Missing username and password"}), 400
    
    # Generamos un nuevo ID basado en la longitud de la lista de usuarios
    user_id = len(users) + 1
    # Creamos nuevo usuario con los datos
    new_user = {
        "id": user_id,
        "username": request.json['username'],
        "password": request.json['password']
    }
    # Agregamos el usuario a la lista, aqui tendria que enviarlo a la BD
    users.append(new_user)
    return jsonify({"message":"User registered successfully","user":new_user}), 201

# Ruta para autenticar un usuario
@app.route('/login', methods=['POST'])
def login():
    # Validamos que la solicitud tenga un cuerpo JSON y contenga 'username' y 'password'
    if not request.json or 'username' not in request.json or 'password' not in request.json:
        # si faltan datos, devolvemos un error 400 (Bad Request)
        return jsonify({"error": "Username y password requeridos"}), 400

    # Buscamos un usuario que coincida con el username y password proporcionados
    user = next((u for u in users if u['username'] == request.json['username'] and u['password'] == request.json['password']), None)

    # Si no encontramos al usuario, devolvemos un error 401 (Unauthorized)
    if user is None:
        return jsonify({"error": "Credenciales invalidas"}), 401
    
    # Si las credenciales son correctas, devolvemos un mensaje de exito y un token simulado
    return jsonify({"mensaje": "Login exitoso", "token": f"token_{user['id']}"})

# Iniciamos el servidor en el puerto 5001 en modo debug
if __name__ == '__main__':
    app.run(port=5001, debug=True)