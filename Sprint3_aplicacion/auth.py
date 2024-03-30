from flask import jsonify, session, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User

def register(data):
    
    # Verifica si todos los campos necesarios están presentes
    if request.headers.get('Content-Type') == 'application/json':
        # Obtener los datos JSON del formulario
        data = request.get_json()
        print("Data received:", data)  # Imprime los datos recibidos desde el cliente
    else:
        # Si la solicitud no es JSON, devolver un error
        print("Invalid Content-Type:", request.headers.get('Content-Type'))  # Imprime el tipo de contenido de la solicitud
        return jsonify({"error": "Invalid Content-Type"}), 400
    
    # Verifica si todos los campos necesarios están presentes
    if "nombre" not in data or "apellidos" not in data or "correo" not in data or "telefono" not in data or "password" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    # Comprueba si el usuario ya existe en la base de datos
    if User.query.filter_by(email=data["correo"]).first():
        return jsonify({"error": "Email already exists"}), 400

    # Crea un nuevo usuario
    new_user = User(
        username=data["nombre"],  # Se utiliza 'nombre' como username
        password=generate_password_hash(data["password"]),
        email=data["correo"],
        phone=data["telefono"]
    )

    # Agrega el nuevo usuario a la base de datos
    db.session.add(new_user)
    db.session.commit()

    #return jsonify({"message": "User registered successfully"}), 201
    # Después de que el usuario se haya registrado correctamente
    session['user_id'] = new_user.id  # Almacena el ID del usuario recién creado en la sesión

    #app.logger.debug("Usuario registrado correctamente. Redirigiendo a /dashboard.")
    return redirect("/dashboard")

def login(data):
    # Verifica si todos los campos necesarios están presentes
    if request.headers.get('Content-Type') == 'application/json':
        data = request.get_json()
    else:
        return jsonify({"error": "Invalid Content-Type"}), 400

    email = data.get('correo')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Si la validación es correcta, puedes iniciar sesión al usuario.
    session['user_id'] = user.id  # Por ejemplo, almacenando el ID del usuario en la sesión.
    #app.logger.debug("Usuario logueado correctamente. Redirigiendo a /dashboard.")
    return redirect("/dashboard")