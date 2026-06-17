import requests  #damit kann Python HTTP Requests an externe APIs machen
from datetime import datetime  
from flask import Flask, jsonify, request # Flask laden, jsonify für JSON Antworten, request für Daten vom Frontend
from flask_cors import CORS # CORS erlaubt unserem Frontend mit dem Backend zu reden. Ohne das blockiert der Browser die Verbindung
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity 

app = Flask(__name__)
CORS(app) #starten Flask und aktivieren CORS

# JWT Konfiguration 
app.config['JWT_SECRET_KEY'] = 'breathe-bubble-secret-key'
jwt = JWTManager(app)

# Testuser
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

# PUT - User Passwort updaten
@app.route('/users/<username>', methods=['PUT'])
@jwt_required()
def update_user(username):
    current_user = get_jwt_identity()
    
    # User kann nur sein eigenes Profil updaten
    if current_user != username:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    new_password = data.get('password')
    
    # User in der Liste suchen und updaten
    for user in users:
        if user['username'] == username:
            user['password'] = new_password
            return jsonify({"message": "Password updated", "username": username})
    
    return jsonify({"error": "User not found"}), 404
    
# DELETE - eine Location löschen
@app.route('/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    for location in locations:
        if location['id'] == id:
            locations.remove(location)
            return jsonify({"message": "Deleted"})
    return jsonify({"error": "Not found"}), 404

# POST - Login Endpoint
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

# POST - Sign Up Endpoint
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Prüfen ob Username schon existiert
    for user in users:
        if user['username'] == username:
            return jsonify({"error": "Username already exists"}), 400

    # Neuen User erstellen und zur Liste hinzufügen
    new_user = {
        "id": len(users) + 1,
        "username": username,
        "password": password
    }
    users.append(new_user)

    # Direkt einloggen nach Sign Up → Token erstellen
    token = create_access_token(identity=username)
    return jsonify({"token": token}), 201

# GET - geschützter Endpoint zum Testen ob Login funktioniert
# @jwt_required() bedeutet: nur mit gültigem Token zugänglich
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # get_jwt_identity holt den Username aus dem Token
    current_user = get_jwt_identity()
    return jsonify({"logged_in_as": current_user})

# Favorites Liste - speichert Favorites pro User
favorites = []

# GET - alle Favorites des eingeloggten Users holen
@app.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    # get_jwt_identity holt den Username aus dem Token
    current_user = get_jwt_identity()
    # Nur Favorites dieses Users zurückgeben
    user_favorites = [f for f in favorites if f['username'] == current_user]
    return jsonify(user_favorites)

# POST - Location zu Favorites hinzufügen
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

# DELETE - Favorite löschen
@app.route('/favorites/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_favorite(id):
    current_user = get_jwt_identity()
    for favorite in favorites:
        if favorite['id'] == id and favorite['username'] == current_user:
            favorites.remove(favorite)
            return jsonify({"message": "Deleted"})
    return jsonify({"error": "Not found"}), 404

#AB DA Open-Meteo API ENDPOINTS
# Aktuelles Wetter in Wien von Open-Meteo API holen
def get_weather():
    try:
        response = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude': 48.2082,
                'longitude': 16.3738,
                'current_weather': 'true'
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            weather = data['current_weather']
            return {
                'temperature': weather['temperature'],
                'weathercode': weather['weathercode'],
                'windspeed': weather['windspeed']
            }
    except:
        pass
    # Fallback wenn API nicht erreichbar
    return {'temperature': 15, 'weathercode': 0, 'windspeed': 10}

#AB DA OVERPASS API ENDPOINTS
# Crowd Level basierend auf Typ UND Tageszeit berechnen
# Crowd Level basierend auf Typ, Uhrzeit UND Wetter berechnen
def calculate_crowd_level(loc_type='park'):
    hour = datetime.now().hour
    weather = get_weather()
    code = weather['weathercode']
    temp = weather['temperature']

    # Wetter Modifier - wie sehr beeinflusst das Wetter den Crowd Level
    if code >= 51:  # Regen oder schlimmer
        if loc_type == 'park':
            weather_modifier = -30  # Park wird viel leerer
        elif loc_type == 'cafe':
            weather_modifier = +20  # Café wird voller
        elif loc_type == 'library':
            weather_modifier = +15  # Bibliothek wird voller
    elif code >= 1:  # Bewölkt
        if loc_type == 'park':
            weather_modifier = -10
        elif loc_type == 'cafe':
            weather_modifier = +5
        elif loc_type == 'library':
            weather_modifier = +5
    else:  # Sonnig
        if loc_type == 'park':
            weather_modifier = +20  # Park wird voller bei Sonne
        elif loc_type == 'cafe':
            weather_modifier = +10
        elif loc_type == 'library':
            weather_modifier = -10  # Bibliothek leerer bei Sonne

    # Temperatur Modifier
    if temp < 5:    # sehr kalt → alle Orte leerer
        weather_modifier -= 20
    elif temp > 25: # sehr warm → Parks voller
        if loc_type == 'park':
            weather_modifier += 15

    # Basis Crowd Level nach Uhrzeit
    if loc_type == 'park':
        if 6 <= hour < 9:     base = 10
        elif 9 <= hour < 11:  base = 30
        elif 11 <= hour < 14: base = 55
        elif 14 <= hour < 17: base = 40
        elif 17 <= hour < 20: base = 65
        else:                  base = 15
    elif loc_type == 'library':
        if 6 <= hour < 9:     base = 5
        elif 9 <= hour < 11:  base = 35
        elif 11 <= hour < 14: base = 60
        elif 14 <= hour < 17: base = 70
        elif 17 <= hour < 20: base = 45
        else:                  base = 5
    elif loc_type == 'cafe':
        if 6 <= hour < 9:     base = 40
        elif 9 <= hour < 11:  base = 70
        elif 11 <= hour < 14: base = 90
        elif 14 <= hour < 17: base = 60
        elif 17 <= hour < 20: base = 80
        else:                  base = 25
    else:
        base = 50

    # Basis + Wetter Modifier kombinieren
    # max(0, min(100, ...)) stellt sicher dass der Wert zwischen 0 und 100 bleibt
    return max(0, min(100, base + weather_modifier))

# Overpass API - echte Locations aus Wien holen
@app.route('/external-locations', methods=['GET'])
def get_external_locations():
    query = """
    [out:json][timeout:10];
    (
      node["leisure"="park"]["name"](48.1,16.2,48.3,16.5);
      node["amenity"="cafe"]["name"](48.1,16.2,48.3,16.5);
      node["amenity"="library"]["name"](48.1,16.2,48.3,16.5);
    );
    out 20;
    """
    try:
        response = requests.get(
            'https://overpass-api.de/api/interpreter',
            params={'data': query},
            timeout=5,
            headers={'User-Agent': 'BreatheBubble/1.0 (university project)'}
        )
        if response.status_code == 200:
            data = response.json()
            result = []
            for element in data['elements']:
                if 'name' in element.get('tags', {}):
                    tags = element['tags']
                    if tags.get('leisure') == 'park':
                        loc_type = 'park'
                    elif tags.get('amenity') == 'cafe':
                        loc_type = 'cafe'
                    else:
                        loc_type = 'library'
                    result.append({
                        "id": element['id'],
                        "name": tags['name'],
                        "type": loc_type,
                        "crowd_level": calculate_crowd_level(loc_type),
                        "lat": element['lat'],
                        "lng": element['lon']
                    })
            if result:
                return jsonify(result)
    except Exception as e:
        print("Overpass Fehler:", e)

    # Fallback: wenn API nicht erreichbar → hardcoded Testdaten
    fallback_locations = [
        {"id": 1, "name": "Stadtpark", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.2063, "lng": 16.3806},
        {"id": 2, "name": "Volksgarten", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.2066, "lng": 16.3616},
        {"id": 3, "name": "Burggarten", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.2033, "lng": 16.3672},
        {"id": 4, "name": "Prater", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.2167, "lng": 16.4000},
        {"id": 5, "name": "Donaupark", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.2367, "lng": 16.4000},
        {"id": 6, "name": "Augarten", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.2233, "lng": 16.3733},
        {"id": 7, "name": "Türkenschanzpark", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.2333, "lng": 16.3333},
        {"id": 8, "name": "Lainzer Tiergarten", "type": "park", "crowd_level": calculate_crowd_level("park"), "lat": 48.1833, "lng": 16.2500},
        {"id": 9, "name": "Bibliothek Wien", "type": "library", "crowd_level": calculate_crowd_level("library"), "lat": 48.2093, "lng": 16.3723},
        {"id": 10, "name": "Nationalbibliothek", "type": "library", "crowd_level": calculate_crowd_level("library"), "lat": 48.2047, "lng": 16.3664},
        {"id": 11, "name": "Universitätsbibliothek Wien", "type": "library", "crowd_level": calculate_crowd_level("library"), "lat": 48.2128, "lng": 16.3560},
        {"id": 12, "name": "Café Central", "type": "cafe", "crowd_level": calculate_crowd_level("cafe"), "lat": 48.2099, "lng": 16.3674},
        {"id": 13, "name": "Café Hawelka", "type": "cafe", "crowd_level": calculate_crowd_level("cafe"), "lat": 48.2081, "lng": 16.3689},
        {"id": 14, "name": "Café Landtmann", "type": "cafe", "crowd_level": calculate_crowd_level("cafe"), "lat": 48.2100, "lng": 16.3600},
        {"id": 15, "name": "Café Schwarzenberg", "type": "cafe", "crowd_level": calculate_crowd_level("cafe"), "lat": 48.2033, "lng": 16.3772},
    ]
    return jsonify(fallback_locations)

# NEU: Recommendations basierend auf Crowd Level und Typ generieren
@app.route('/recommendations/<int:location_id>', methods=['GET'])
def get_recommendations(location_id):
    # Crowd Level und Typ aus den external locations holen
    loc_type = request.args.get('type', 'park')
    crowd_level = int(request.args.get('crowd_level', 50))
    hour = datetime.now().hour

    recommendations = []

    # Empfehlungen basierend auf Crowd Level
    if crowd_level >= 67:  # Crowded
        recommendations.append("🎧 Take headphones with you")
        recommendations.append("⏰ Try visiting early morning for a quieter experience")
        if loc_type == 'park':
            recommendations.append("🌙 Best time to visit: after 8 PM")
        elif loc_type == 'cafe':
            recommendations.append("🌙 Best time to visit: after 7 PM")
        elif loc_type == 'library':
            recommendations.append("🌅 Best time to visit: before 10 AM")

    elif crowd_level >= 34:  # Medium
        recommendations.append("📍 Moderately busy right now")
        if loc_type == 'park':
            recommendations.append("🌅 Morning visits are usually quieter")
        elif loc_type == 'cafe':
            recommendations.append("💻 Good spot for remote work right now")

    else:  # Quiet
        recommendations.append("✅ Great time to visit!")
        recommendations.append("😌 Enjoy the quiet atmosphere")
        if loc_type == 'park':
            recommendations.append("🌿 Perfect for a relaxing walk")
        elif loc_type == 'library':
            recommendations.append("📚 Perfect for studying right now")
        elif loc_type == 'cafe':
            recommendations.append("☕ Perfect for a quiet coffee")

    # Tageszeit basierte Empfehlungen
    if 11 <= hour < 14:
        recommendations.append("🍽️ Lunchtime — expect more visitors soon")
    elif 17 <= hour < 19:
        recommendations.append("🏃 After-work rush — busier than usual")

    return jsonify({"recommendations": recommendations})

# Ratings Liste - speichert Bewertungen pro Location
ratings = []

# POST - Bewertung abgeben
# Nur eingeloggte User können bewerten
@app.route('/ratings/<int:location_id>', methods=['POST'])
@jwt_required()
def add_rating(location_id):
    current_user = get_jwt_identity()
    data = request.json
    
    rating = {
        "id": len(ratings) + 1,
        "username": current_user,
        "location_id": location_id,
        "accuracy": data.get('accuracy'),  # 1-5 Sterne - wie genau war die Prediction?
        "comment": data.get('comment', '')
    }
    ratings.append(rating)
    return jsonify(rating), 201

# GET - alle Bewertungen einer Location holen
@app.route('/ratings/<int:location_id>', methods=['GET'])
def get_ratings(location_id): # Alle Bewertungen für eine bestimmte Location holen
    location_ratings = [r for r in ratings if r['location_id'] == location_id] # Alle Bewertungen für diese Location filtern
    
    # Durchschnitt berechnen
    if location_ratings:
        avg = sum(r['accuracy'] for r in location_ratings) / len(location_ratings) # Durchschnittliche Accuracy Bewertung berechnen
        avg = round(avg, 1) # auf 1 Nachkommastelle runden
    else:
        avg = None # wenn es noch keine Bewertungen gibt, ist der Durchschnitt None
    
    return jsonify({
        "ratings": location_ratings, # alle Bewertungen als Liste zurückgeben
        "average": avg, 
        "count": len(location_ratings) # Anzahl der Bewertungen zurückgeben
    })
# Ist der Standard Code um Flask zu starten. Das Backend startet sich selbst — unabhängig vom Frontend.
if __name__ == '__main__': 
    app.run(debug=True)

