"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, FavoritePlanets, FavoriteCharacters #Hay que importar las columnas.
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)
#1)Crear las rutas y sus respectivos métodos.
#2)All_user es un array de objetos por lo que hay que serializarlo con un for/map(usuario por usuario) y almacenarno en un array vacío.
#3)Agregamos al body el array con los usuarios serializados.
@app.route('/users', methods=['GET'])
def get_users():
    all_users = User.query.all() #query.all() me trae todos los usuarios del objeto User.
    all_users_serialize = [] #almacenamos los usuarios ya serializados en un array vacío ya que "all_users" es un array de objetos.
    for user in all_users: #Recorremos cada usuario de "all_users" con un bucle for.
        all_users_serialize.append(user.serialize()) #Agregamos cada usuario serializado a "all_users_serialize" con el método append()
    response_body = {'msg': 'ok',
        'data': all_users_serialize #Agregamos los usuarios al body.
    }

    return jsonify(response_body), 200 #Retornamos el body y un statuscode 200 (ok).

@app.route('/user/<int:id>', methods=['GET'])
def get_single_user(id): #Le pasamos el id ya que estamos solicitando información de un solo usuario.
    single_user = User.query.get(id) #query.get(id) me trae un usuario específico de la tabla User.
    if single_user is None:
        return jsonify({'msg': f'El usuario con id {id} no existe'}), 404 #StatusCode: Error del cliente.
    return jsonify ({
        'msg':'ok',
        'data': single_user.serialize()
    }), 200

@app.route('/user/<int:id>/favorites', methods=['GET'])
def get_favorites(id):
    favorite_planets = FavoritePlanets.query.filter_by(user_id = id).all() #Devuelve todos los resultados que coinciden en forma de lista.
    favorite_characters = FavoriteCharacters.query.filter_by(user_id = id). all()
    favorite_planets_serialize = []
    for fav in favorite_planets:
        favorite_planets_serialize.append(fav.planet_relationship.serialize())
    favorite_characters_serialize = []
    for fav in favorite_characters:
        favorite_characters_serialize.append(fav.character_relationship.serialize())
    
    return jsonify({'msg': 'ok',
                    'user_data': favorite_planets[0].user_relationship.serialize(),
                    'favorite_planets': favorite_planets_serialize,
                    'favorite_characters': favorite_characters_serialize}), 200

@app.route('/user', methods=['POST'])
def add_user():
    body = request.get_json(silent=True) #Obtenemos los datos de la solicitud y los guardamos en "body".
    if body is None: #Condicionales para saber si el usuario llenó los campos.
        return jsonify({'msg': 'Debes envíar información en el body'}), 400 #StatusCode: Error del cliente.
    if 'name'  not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'email' not in body:
        return jsonify({'msg': 'El campo email es obligatorio'}), 400
    if 'password' not in body:
        return jsonify({'msg': 'El campo password es obligatorio'}), 400
#Hacemos una consulta a la base de datos para buscar si ya existe un usuario con el nombre proporcionado.
#first() devuelve la primera coincidencia que encuentre. Si no encuentra ninguna, devuelve None.
#filter_by sirve para verificar la existencia de múltiples campos en una sola consulta para condiciones simples de igualdad, sin necesidad de escribir ==.
    existing_email = User.query.filter_by(email=body['email']).first()
    if existing_email:
        return jsonify({'msg': 'El email ingresado ya existe, por favor, ingresa otro'}), 400

    new_user = User() #Instanciamos el nuevo objeto "User".
    new_user.name = body['name'] # Asignamos el valor de 'name' al atributo name del objeto new_user.
    new_user.email = body['email']
    new_user.password = body['password'] #Hay que configurar el serializador para no serializar las contraseñas.
    
    db.session.add(new_user) #Agregamos el nuevo usuario.
    db.session.commit() #Guarda el nuevo usuario.

    return jsonify({'msg': 'Usuario creado satisfactoriamente', #Retornamos un mensaje.
                    'data': new_user.serialize()}), 201 #Serializamos el nuevo usuario(new_user).

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    body = request.get_json(silent=True)
    user = User.query.get(id)
    if user is None:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    if body is None:
        return jsonify({'msg': 'Debes enviar inforamción en el body'}), 400
    if 'name' not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'email' not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'password' not in body:
        return jsonify({'msg': 'El campo password es obligatorio'}), 400
    
    existing_email = User.query.filter_by(email=body['email']).first()
    if existing_email and existing_email.id != id:
        return jsonify({'msg': 'El email ingresado ya existe, porfavor, ingresa otro'}), 400
    
    user.name = body.get('name', user.name)
    user.email = body.get('email', user.email)
    user.password = body.get('password', user.password) #Hay que configurar el serializador para no serializar las contraseñas.

    db.session.commit()

    return jsonify({'msg': 'Usuario actualizado exitosamente',
                    'data': user.serialize()}), 200

@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if user is None:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    db.session.delete(user)
    db.session.commit()

    return jsonify({'msg': 'Usuario eliminado exitosamente',}), 204

@app.route('/favorite/planets/<int:planet_id>/<int:user_id>', methods=['POST'])
def add_favorite_planet(planet_id, user_id):
    body = request.get_json(silent=True)
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'msg': 'Usuario no encontrado'}),404
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({'msg': 'Planeta no encontrado'}), 404
    
    existing_favorite = FavoritePlanets.query.filter_by(user_id = user_id, planet_id = planet_id).first()
    if existing_favorite:
        return jsonify({'msg': 'El planeta seleccionado ya está en favoritos'}), 400
    
    new_favorite = FavoritePlanets(user_id = user_id, planet_id = planet_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({'msg': 'Planeta agregado exitosamente'}), 200

@app.route('/favorite/characters/<int:character_id>/<int:user_id>', methods=['POST'])
def add_favorite_character(character_id, user_id):
    body = request.get_json(silent=True)
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'msg': 'Usuario no encontrado'}),404
    character = Character.query.get(character_id)
    if character is None:
        return jsonify({'msg': 'Personaje no encontrado'}), 404
     #Buscar la entrada de favoritos que relaciona al usuario con el planeta
    existing_favorite = FavoriteCharacters.query.filter_by(user_id = user_id, character_id = character_id).first()
    if existing_favorite:
        return jsonify({'msg': 'El Personaje seleccionado ya está en favoritos'}), 400
    
    new_favorite = FavoriteCharacters(user_id = user_id, character_id = character_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({'msg': 'Personaje agregado exitosamente'}), 200

@app.route('/favorite/planet/<int:planet_id>/<int:user_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id, user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({'msg': 'Planeta no encontrado'}), 404
    #Buscar la entrada de favoritos que relaciona al usuario con el planeta
    favorite = FavoritePlanets.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    #Verificar si la entrada de favoritos existe
    if favorite is None:
        return jsonify({'msg': 'Favorito no encontrado'}), 404
    #Eliminar la entrada de favoritos
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({'msg': 'Planeta eliminado de Favoritos exitosamente'}), 204

@app.route('/favorite/character/<int:character_id>/<int:user_id>', methods=['DELETE'])
def delete_favorite_character(character_id, user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    character = Character.query.get(character_id)
    if character is None:
        return jsonify({'msg': 'Personaje no encontrado'}), 404
    
    favorite = FavoriteCharacters.query.filter_by(user_id=user_id, character_id=character_id).first()
    
    if favorite is None:
        return jsonify({'msg': 'Favorito no encontrado'}), 404
   
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({'msg': 'Personaje eliminado de Favoritos exitosamente'}), 204
    
@app.route('/planets', methods=['GET']) #Definimos la ruta para obtener los planetas.
def get_planets(): #Definimos la función que se ejecutará.
    all_planets = Planet.query.all() #Accedemos al objeto "Planet" y lo traemos.
    all_planets_serialize = [] #Definimos un array vacío donde guardaremos todos los objetos planet(all_planets)
    for planet in all_planets: #Recorremos cada "planet" del array de objetos "all_planets".
        all_planets_serialize.append(planet.serialize()) #Serializamos cada planeta y lo almacenamos en nuestro array vacío con el método append()
        response_body = { #Agregamos un mensaje y el array de planetas ya serializados en una variable.
            'msg': 'ok',
            'data': all_planets_serialize
        }
    
    return jsonify(response_body), 200 #Retornamos nuestro diccionario(ya serializado) y lo convertimos en formato JSON(jsonify).
    
@app.route('/planet/<int:id>', methods=['GET'])
def single_planet(id):
    single_planet = Planet.query.get(id) #query.get(id): Nos deja traer un planeta por el id del array de objetos Planet
    if single_planet is None: #Condicional para saber si ese planeta existe.
        return jsonify ({'msg': f'El planeta con id {id} no existe'}), 404 #Si el planeta no existe retornamos un mensaje, siempre en formato "jsonify".
    residents_serialize = [] #Definimos un array donde guardaremos cada objeto(character).
    for resident in single_planet.residents: #Iteramos cada personaje de la llave que relaciona los personajes con los planetas(residents).
        residents_serialize.append(resident.serialize()) #Agregamos a nuestro array cada personaje(resident) y lo serializamos.
    data = single_planet.serialize() #Serializamos el planeta.
    data['residents'] = residents_serialize
#Asignamos el valor de residents_serialize a la llave 'residents' en el diccionario "data".
#Puede ser cualquier variable y llave ya que lo que lo víncula es el serialize() de single_planet (planet=single_planet.serialize()).

    return jsonify ({ #Retornamos un jsonify con un mensaje y la data(objeto).
        'msg':'ok',
        'data': data #data es nuestro planeta. Ya serializado.
    }), 200 #StatusCode: Ok

@app.route('/planets', methods=['POST'])
def add_planets():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({'msg': 'Debes enviar información en el body'}), 400
    if 'name' not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'population' not in body:
        return jsonify({'msg': 'El campo population es obligatorio'}), 400
    if 'diameter' not in body:
        return jsonify({'msg': 'El campo diameter es obligatorio'}), 400
    if 'climated' not in body:
        return jsonify({'msg': 'El campo climated es obligatorio'}), 400
    if 'terrain' not in body:
        return jsonify({'msg': 'El campo terrain es obligatorio'}), 400
    
    existing_name = Planet.query.filter_by(name=body['name']).first()
    if existing_name:
        return jsonify({'msg': 'El name ingresado ya existe, por favor, ingresa otro'}), 400
    
    new_planet = Planet() 
    new_planet.name = body['name']
    new_planet.population = body['population']
    new_planet.diameter = body['diameter']
    new_planet.climated = body['climated']
    new_planet.terrain = body['terrain']

    db.session.add(new_planet)
    db.session.commit()

    return jsonify({
        'msg': 'Planeta creado satisfactoriamente',
        'data': new_planet.serialize()}), 201

@app.route('/planet/<int:id>', methods=['PUT'])
def update_planet(id):
    body = request.get_json(silent=True) #Obtenemos el "json" del cuerpo de la solicitud.
    planet = Planet.query.get(id) #Obtenemos el planeta por su id de la tabla Planet.
    if planet is None: #Condicionales para saber la existencia de los planetas y de los campos requeridos.
        return jsonify({'msg': 'Planeta no encontrado'}), 404
    if body is None:
        return jsonify({'msg': 'Debes enviar información en el body'}), 400
    if 'name' not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'population' not in body:
        return jsonify({'msg': 'El campo population es obligatorio'}), 400
    if 'diameter' not in body:
        return jsonify({'msg': 'El campo diameter es obligatorio'}), 400
    if 'climated' not in body:
        return jsonify({'msg': 'El campo climated es obligatorio'}), 400
    if 'terrain' not in body:
        return jsonify({'msg': 'El campo terrain es obligatorio'}), 400
#Verificamos si name existe en los registros actuales.
    existing_name = Planet.query.filter_by(name=body['name']).first()
    #funciona=?
    if existing_name and existing_name.id != id: #Aseguramos que el planeta que ya tiene el nombre no es el mismo planeta que estamos actualizando.
        return jsonify({'msg': 'El name ingresado ya existe, por favor, ingresa otro'}), 400
#No instanciamos planet ya que no estamos creando un nuevo objeto sino actualizando uno existente.
    planet.name = body.get('name', planet.name) #body.get('name'): Intentamos obtener el valor asociado a la llave 'name' del body
    planet.population = body.get('population',planet.population) #(planet.name): Si 'name' no está presente en body, se usa el valor actual de planet.name
    planet.diameter = body.get('diameter', planet.diameter)
    planet.climated = body.get('climated', planet.climated)
    planet.terrain = body.get('terrain', planet.terrain)

    db.session.commit() #Solo necesitamos guardarlo.
#db.session.add() Solo se usa cuando vamos a agregar un nuevo registro.
    return jsonify ({'msg': 'Planeta actualizado existosamente',
                     'data': planet.serialize()}), 200

@app.route('/planet/<int:id>', methods=['DELETE'])
def delete_planet(id):
    planet = Planet.query.get(id) #Buscamos el planeta por su id en la tabla "Planet".
    if planet is None: #Si no existe ese planeta devolvemos el jsonify con un mensaje y un status code.
        return jsonify({'msg': 'Planeta no encontrado'}), 404
    #Los siguientes pasos son para poder eliminar un planeta aunque este, tenga una relación.
    # Primero, eliminamos o actualizamos los personajes asociados
    #characters = Character.query.filter_by(planet_id=id).all()
    #for character in characters:
     #   db.session.delete(character)  # Eliminamos los personajes asociados

    #serialize_planet = planet.serialize() Podemos serializar o no, dependiendo de si queremos mostrar más detalles del recurso eliminado. 
    
    db.session.delete(planet) #Eliminamos el planeta.
    db.session.commit() #Guardamos los cambios.
    
    return jsonify({'msg': 'Planeta eliminado existosamente'}),204 #No Content: el recurso se ha eliminado correctamente

@app.route('/characters', methods=['GET'])
def get_characters():
    all_characters = Character.query.all()
    all_characters_serialize = [] 
    for character in all_characters:
        all_characters_serialize.append(character.serialize())

    return ({
        'msg': 'ok',
        'data': all_characters_serialize
    }), 200

@app.route('/character/<int:id>', methods=['GET'])
def get_single_character(id):
    single_character = Character.query.get(id)
    if single_character is None:
        return jsonify({'msg': f'El character con id {id} no existe'}), 404
    
    data = single_character.serialize() #Serializamos el personaje y almacenamos en variable.
#Asignamos la llave 'data' al diccionario "character" y su valor es un diccionario contenido en single_character(planet_relationship).
#es decir, la relación entre character y planet(un planeta) serializado.
    data['planet'] = single_character.planet_relationship.serialize()

    
    return jsonify({'msg': 'ok',
                    'data': data}), 200

@app.route('/characters', methods=['POST'])
def add_characters():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({'msg': 'Deber enviar información en el body'}), 400
    if 'name' not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'specie' not in body:
        return jsonify({'msg': 'El campo specie es obligatorio'}), 400
    if 'gender' not in body:
        return jsonify({'msg': 'El campo gender es obligatorio'}), 400
    if 'age' not in body:
        return jsonify({'msg': 'El campo age es obligatorio'}), 400
    if 'height' not in body:
        return jsonify({'msg': 'El campo height es obligatorio'}), 400
    if 'weight' not in body:
        return jsonify({'msg': 'El campo weight es obligatorio'}), 400
    
    existing_name = Character.query.filter_by(name=body['name']).first()
    if existing_name:
        return jsonify({'msg': 'El name ingresado ya existe, por favor, ingresa otro'}), 400
    
    new_character = Character()
    new_character.name = body['name']
    new_character.specie = body['specie']
    new_character.gender = body['gender']
    new_character.age = body['age']
    new_character.height = body['height']
    new_character.weight = body['weight']

    db.session.add(new_character)
    db.session.commit()

    return jsonify({'msg': 'Personaje creado satisfactoriamente',
                    'data': new_character.serialize()}), 201 #Created: Nuevo recurso se ha creado exitosamente.

@app.route('/character/<int:id>', methods=['PUT'])
def update_character(id):
     #Obtenemos los datos JSON del cuerpo de la solicitud.
    body = request.get_json(silent=True)
     #Obtenemos el objeto Character basado en el ID proporcionado.
    character = Character.query.get(id)
    #Verificamos si el personaje existe
    if character is None:
        return jsonify({'msg': 'Character no encontrado'}), 404
    if body is None:
        return jsonify({'msg': 'Debes enviar información en el body'}), 400
    if 'name' not in body:
        return jsonify({'msg': 'El campo name es obligatorio'}), 400
    if 'specie' not in body:
        return jsonify({'msg': 'El campo specie es obligatorio'}), 400
    if 'gender' not in body:
        return jsonify({'msg': 'El campo gender es obligatorio'}), 400
    if 'age' not in body:
        return jsonify({'msg': 'El campo age es obligatorio'}), 400
    if 'height' not in body:
        return jsonify({'msg': 'El campo height es obligatorio'}), 400
    if 'weight' not in body:
        return jsonify({'msg': 'El campo weight es obligatorio'}), 400
    
    existing_name = Character.query.filter_by(name=body['name']).first()
    if existing_name and existing_name.id != id:
        return jsonify({'msg': 'El name ingresado ya existe, por favor, ingresa otro'}), 400
    #Actualizamos los atributos del personaje con los datos proporcionados.
    character.name = body.get('name', character.name)
    character.specie = body.get('specie', character.specie)
    character.gender = body.get('gender', character.gender)
    character.age = body.get('age', character.age)
    character.height = body.get('height', character.height)
    character.weight = body.get('weight', character.weight)
    #Guardamos los cambios en la base de datos.
    db.session.commit()
    #Devolvemos el objeto actualizado y serializado
    return jsonify({'msg': 'Personaje actualizado exitosamente',
                    'data': character.serialize()}), 200

@app.route('/character/<int:id>', methods=['DELETE'])
def delete_character(id):
    character = Character.query.get(id)
    if character is None:
        return jsonify({'msg': 'Personaje no encontrado'}), 404
    
    db.session.delete(character)
    db.session.commit()

    return jsonify({'msg': 'Personaje eliminado exitosamente',}), 204

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
#Preguntar: orden de objetos (relación characters/planet) en postman aparece el objeto planet en medio del objeto character.