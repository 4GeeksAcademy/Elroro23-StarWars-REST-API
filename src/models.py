from flask_sqlalchemy import SQLAlchemy
#1) Crear las tablas con las columnas necesarias.
#2) Serializar las columnas necesarias para convertirlas en un diccionario python.
db = SQLAlchemy()
#Definimos la tabla "User" que contiene columnas con todos los datos de registro del usuario además de su PK.
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False) #No se serializa por seguridad.
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    #Nombre de la Columna que contiene la relación(planets_favorites)#1)Tabla a la que hace referencia 2)Columna que lo relaciona.
    planets_favorites = db.relationship('FavoritePlanets', back_populates='user_relationship')
    characters_favorites = db.relationship('FavoriteCharacters', back_populates='user_relationship')
#Para listar las tablas: \dt
#Query para traer todos los registros de una tabla: SELECT * FROM "nombre tabla";
#El método "__repr__" sirve como un print para imprimir en postgreSQL.
    def __repr__(self):
        return f'User {self.name} with email {self.email}'
#El método "serialize" sirve para convertir los objetos en un diccionario python para que pueda ser leído.
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password, #La contraseña no se serializa.
            'is_active': self.is_active
        }
    
class Planet(db.Model):
    __tablename__ = 'planet'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    population = db.Column(db.Integer, unique=False, nullable=False)
    diameter = db.Column(db.Integer, unique=False, nullable=False)
    climated = db.Column(db.String(20), unique=False, nullable=False)
    terrain = db.Column(db.String(20), unique=False, nullable=False)
    residents = db.relationship('Character', back_populates='planet_relationship')
    favorite_by = db.relationship('FavoritePlanets', back_populates='planet_relationship')

    def __repr__(self):
        return f'Planeta {self.name}'
    
    def serialize(self):
        return{
            'id': self.id,
            'name': self.name,
            'population': self.population,
            'diameter': self.diameter,
            'climated': self.climated,
            'terrain': self.terrain
        }
    
class Character(db.Model):
    __tablename__ = 'character'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    specie = db.Column(db.String(20), unique=False, nullable=False)
    gender = db.Column(db.String(20), unique=False,nullable=False)
    age = db.Column(db.Integer, unique=False, nullable=False)
    height = db.Column(db.Integer, unique=False, nullable=False)
    weight = db.Column(db.Integer, unique=False, nullable=False)
    planet_id = db.Column(db.Integer, db.ForeignKey('planet.id'), nullable=False) #FK que se relaciona con "Planet".
#Relación bidireccional:Podemos acceder desde cualquiera de las dos clases a los objetos relacionados de la otra.
    planet_relationship = db.relationship('Planet', back_populates='residents') #Relación bidireccional: Tabla "Planet" columna "residents"(relación).
    favorite_by = db.relationship('FavoriteCharacters', back_populates='character_relationship')
    
    def __repr__(self):
        return f'Personaje {self.name}'
    
    def serialize(self):
        return{
            'id': self.id,
            'name': self.name,
            'specie': self.specie,
            'gender': self.gender,
            'age': self.age,
            'height': self.height,
            'weight': self.weight
        }
    
class FavoritePlanets(db.Model):
    __tablename__ = 'favoriteplanets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_relationship = db.relationship('User', back_populates='planets_favorites')
    planet_id = db.Column(db.Integer, db.ForeignKey('planet.id'), nullable=False)
    planet_relationship = db.relationship('Planet', back_populates='favorite_by')

    def __repr__(self):
        return f'Al usuario {self.user_id} le gusta el planeta {self.planet_id}'
    
    def serialize(self):
        return{
            'id':self.id,
            'user_id': self.user_id,
            'planet_id': self.planet_id
        }
    
class FavoriteCharacters(db.Model):
    __tablename__ = 'favoritecharacters'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_relationship = db.relationship('User', back_populates='characters_favorites')
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    character_relationship = db.relationship('Character', back_populates='favorite_by')

    def __repr__(self):
        return f'Al usuario {self.user_id} le gusta el planeta {self.character_id}'
    
    def serialize(self):
        return{
            'id':self.id,
            'user_id': self.user_id,
            'character_id': self.character_id
        }
 #Recuerda actualizar PSQL: Migrate, updgrate.  