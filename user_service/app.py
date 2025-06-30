from flask import Flask, jsonify, request

# Creamos una instancia de la aplicación Flask
app = Flask(__name__)

# Lista en memoria para almacenar usuarios(Simula base ded datos)
# Cada usuario tiene un id, username y email
users = [
    {"id": 1, "username": "user1", "email": "user1@example.com"},
]

# Ruta para listar todos los usuarios (GET /users)
@app.route('/users', methods=['GET'])
def get_users():
    # Devolvemos la lista compelta de usuarios en formato JSON
    return jsonify({"users": users})

# Ruta para obtener un usuario por ID (GET /users/<id>)
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Buscamos el usuario por ID
    user = next((u for u in users if u['id'] == user_id), None)
    # Si no se encuentra el usuario, devolvemos un error 404 (not found)
    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404
    # Si se encuentra, devolvemos el usuario
    return jsonify({"user": user})
    
# Ruta para crear un nuevo usuario (POST /users)
@app.route('/users', methods=['POST'])
def create_user():
    # Validamos que la solicitud tenga un cuerpo JSON y contenga "username" y "email"
    if not request.is_json or 'username' not in request.json or 'email' not in request.json:
        # Si faltan datos, devolvemos un error 400 (bad request)
        return jsonify({"error": "Username y email requeridos"}), 400
    # Creamos un nuevo usuario con un ID incremental
    new_user = {
        "id": len(users) + 1,
        "username": request.json['username'],
        "email": request.json['email']
    }
    # Añadimos el nuevo usuario a la lista
    users.append(new_user)
    # Devolvemos el usuario creado con un código de estado 201 (created)
    return jsonify({"user": new_user}), 201

# Ruta para actualizar un usuario por ID (PUT /users/<id>)
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # Buscamos el usuario por ID proporcionado
    user = next((u for u in users if u['id'] == user_id), None)
    if user is None:
        # Si no se encuentra el usuario, devolvemos un error 404 (not found)
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Actualizamos los campos del usuario con los datos proporcionados
    if request.is_json:
        user['username'] = request.json.get('username', user['username'])
        user['email'] = request.json.get('email', user['email'])
    
    # Devolvemos el usuario actualizado
    return jsonify({"user": user})

# Ruta para eliminar un usuario por ID (DELETE /users/<id>)
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Declaramos la lista de usuarios global para poder modificarla
    global users
    # Buscamos el usuario por ID proporcionado
    user = next((u for u in users if u['id'] == user_id), None)
    if user is None:
        # Si no se encuentra el usuario, devolvemos un error 404 (not found)
        return jsonify({"error": "Usuario no encontrado"}), 404
    # Eliminamos el usuario de la lista
    users = [u for u in users if u['id'] != user_id]
    # Devolvemos un mensaje de éxito
    return jsonify({"message": "Usuario eliminado"})

# Iniciamos el servidor en el puerto 5002 en modo debug
if __name__ == '__main__':
    app.run(port=5002, debug=True)