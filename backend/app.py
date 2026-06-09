from flask import Flask, jsonify, request # Flask laden, jsonify für JSON Antworten, request für Daten vom Frontend
from flask_cors import CORS # CORS erlaubt unserem Frontend mit dem Backend zu reden. Ohne das blockiert der Browser die Verbindung.
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity # ★ NEU: JWT für Login System

app = Flask(__name__)
CORS(app) # Wir starten Flask und aktivieren CORS.

# ★ NEU: JWT Konfiguration - das ist der geheime Schlüssel zum Signieren der Tokens
app.config['JWT_SECRET_KEY'] = 'breathe-bubble-secret-key'
jwt = JWTManager(app)

# ★ NEU: Testuser - später würde das aus einer Datenbank kommen
users = [
    {"id": 1, "username": "test", "password": "1234"},
]

locations = [
    {"id": 1, "name": "Stadtpark", "type": "park", "crowd_level": 20, "lat": 48.2063, "lng": 16.3806},
    {"id": 2, "name": "Bibliothek Wien", "type": "library", "crowd_level": 50, "lat": 48.2093, "lng": 16.3723},
    {"id": 3, "name": "Café Central", "type": "cafe", "crowd_level": 75, "lat": 48.2099, "lng": 16.3674},
]

# GET - alle Locations lesen
@app.route('/locations', methods=['GET'])
def get_locations():
    return jsonify(locations) # gibt alle Locations als JSON zurück

# POST - neue Location hinzufügen
@app.route('/locations', methods=['POST'])
def add_location():
    # request.json holt die Daten die das Frontend schickt
    new_location = request.json
    locations.append(new_location)
    return jsonify(new_location), 201

# PUT - eine Location updaten
@app.route('/locations/<int:id>', methods=['PUT'])
def update_location(id):
    # Suche die Location mit dieser ID
    for location in locations:
        if location['id'] == id:
            # Update die Daten mit dem was Frontend schickt
            location.update(request.json)
            return jsonify(location)
    return jsonify({"error": "Not found"}), 404

# DELETE - eine Location löschen
@app.route('/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    for location in locations:
        if location['id'] == id:
            locations.remove(location)
            return jsonify({"message": "Deleted"})
    return jsonify({"error": "Not found"}), 404

# ★ NEU: POST - Login Endpoint
# Frontend schickt Username + Passwort → Backend prüft → gibt Token zurück
@app.route('/login', methods=['POST'])
def login():
    # Daten vom Frontend holen
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # User in der Liste suchen
    for user in users:
        if user['username'] == username and user['password'] == password:
            # Token erstellen und zurückschicken
            token = create_access_token(identity=username)
            return jsonify({"token": token})

    # Wenn User nicht gefunden oder Passwort falsch
    return jsonify({"error": "Wrong username or password"}), 401

# ★ NEU: GET - geschützter Endpoint zum Testen ob Login funktioniert
# @jwt_required() bedeutet: nur mit gültigem Token zugänglich
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # get_jwt_identity holt den Username aus dem Token
    current_user = get_jwt_identity()
    return jsonify({"logged_in_as": current_user})

# ★ NEU: Favorites Liste - speichert Favorites pro User
favorites = []

# ★ NEU: GET - alle Favorites des eingeloggten Users holen
@app.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    # get_jwt_identity holt den Username aus dem Token
    current_user = get_jwt_identity()
    # Nur Favorites dieses Users zurückgeben
    user_favorites = [f for f in favorites if f['username'] == current_user]
    return jsonify(user_favorites)

# ★ NEU: POST - Location zu Favorites hinzufügen
@app.route('/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    current_user = get_jwt_identity()
    data = request.json
    # Favorite Objekt erstellen
    favorite = {
        "id": len(favorites) + 1,
        "username": current_user,
        "location_name": data.get('location_name'),
        "location_type": data.get('location_type'),
        "crowd_level": data.get('crowd_level'),
        "lat": data.get('lat'),
        "lng": data.get('lng')
    }
    favorites.append(favorite)
    return jsonify(favorite), 201

# ★ NEU: DELETE - Favorite löschen
@app.route('/favorites/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_favorite(id):
    current_user = get_jwt_identity()
    for favorite in favorites:
        if favorite['id'] == id and favorite['username'] == current_user:
            favorites.remove(favorite)
            return jsonify({"message": "Deleted"})
    return jsonify({"error": "Not found"}), 404



if __name__ == '__main__':
    app.run(debug=True)