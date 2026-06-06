from flask import Flask, jsonify #laden Flask - Wie ein import — wir sagen Python "benutze Flask
from flask_cors import CORS #CORS erlaubt unserem Frontend mit dem Backend zu reden. Ohne das blockiert der Browser die Verbindung.
from flask import Flask, jsonify, request #request erlaubt uns, Daten vom Frontend zu empfangen, z.B. wenn jemand ein Formular abschickt.


app = Flask(__name__)
CORS(app)       #Wir starten Flask und aktivieren CORS.

locations = [
    {"id": 1, "name": "Stadtpark", "type": "park", "crowd_level": 20, "lat": 48.2063, "lng": 16.3806},
    {"id": 2, "name": "Bibliothek Wien", "type": "library", "crowd_level": 50, "lat": 48.2093, "lng": 16.3723},
    {"id": 3, "name": "Café Central", "type": "cafe", "crowd_level": 75, "lat": 48.2099, "lng": 16.3674},
]

@app.route('/locations', methods=['GET']) #Wenn jemand auf http://localhost:5000/locations geht, führt Flask diese Funktion aus. GET bedeutet: jemand will Daten lesen.
def get_locations():
    return jsonify(locations) #Die Funktion erstellt eine Liste von Orten mit ihren Informationen und gibt sie als JSON zurück. JSON ist ein Format, das leicht von JavaScript im Frontend verarbeitet werden kann.


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
    

if __name__ == '__main__': 
    app.run(debug=True) 