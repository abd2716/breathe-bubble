// Karte erstellen und auf Wien zentrieren
// 48.2082, 16.3738 sind die GPS Koordinaten von Wien
// 13 ist der Zoom Level - je höher desto näher
const map = L.map('map').setView([48.2082, 16.3738], 13);

// Kartenkacheln von OpenStreetMap laden
// Das sind die echten Kartenbilder die wir sehen
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

// Hier speichern wir alle Locations und Marker für den Filter
let allLocations = [];
let allMarkers = [];

//AB HIER Frontend-Backend verbindung
// Token speichern - wenn eingeloggt haben wir einen Token
let token = null;

// Login Modal öffnen
function showLogin() {
    document.getElementById('login-modal').style.display = 'flex';
}

// Login Modal schließen
function closeLogin() {
    document.getElementById('login-modal').style.display = 'none';
}

// Sign Up Modal öffnen
function showSignup() {
    document.getElementById('signup-modal').style.display = 'flex';
}

// Sign Up Modal schließen
function closeSignup() {
    document.getElementById('signup-modal').style.display = 'none';
    // Felder leeren damit man wieder ein neues Konto erstellen kann
    document.getElementById('signup-username').value = '';
    document.getElementById('signup-password').value = '';
    document.getElementById('signup-error').textContent = '';
}

// Sign Up Request ans Backend schicken
function signup() {
    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;

    fetch('http://localhost:5000/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            // Token speichern - direkt eingeloggt nach Sign Up
            token = data.token;
            closeSignup();
            // Navbar updaten
            document.getElementById('nav-buttons').innerHTML = 
                `<span>👤 ${username}</span>
                 <button onclick="logout()">Log out</button>`;
            loadFavorites();
        } else {
            document.getElementById('signup-error').textContent = data.error;
        }
    });
}

// Login Request ans Backend schicken
function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    // POST Request an /login mit Username + Passwort
    fetch('http://localhost:5000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            // Token speichern
            token = data.token;
            // Modal schließen
            closeLogin();
            // Login Button zu Username ändern
            document.getElementById('nav-buttons').innerHTML = 
                `<span>👤 ${username}</span>
                 <button onclick="logout()">Log out</button>`;
            // Favorites laden sobald eingeloggt
            loadFavorites();
        } else {
            // Fehlermeldung anzeigen
            document.getElementById('login-error').textContent = 'Wrong username or password';
        }
    });
}

// Logout
function logout() {
    token = null;
    document.getElementById('nav-buttons').innerHTML = 
        `<button onclick="showLogin()">Log in</button>
         <button onclick="showSignup()">Sign up</button>`;
    // Favorites Panel leeren beim Logout
    if (document.getElementById('favorites-panel')) {
        document.getElementById('favorites-panel').innerHTML = '';
    }
}
//Bis hier login-logout (JWT)
// Search Funktion - filtert Locations nach Name
function searchLocations(query) {
    if (query === '') {
        // Wenn Suchfeld leer → alle Locations zeigen
        showMarkers(allLocations);
        return;
    }
    // Locations filtern die den Suchbegriff im Namen haben
    const filtered = allLocations.filter(loc => 
        loc.name.toLowerCase().includes(query.toLowerCase())
    );
    showMarkers(filtered);
}

// Locations vom Backend holen und auf der Karte anzeigen
function loadLocations() {
    // fetch macht einen GET Request an unser Backend
    // AJAX Call - wir fragen den Server nach Daten, ohne die Seite neu zu laden
    fetch('http://localhost:5000/external-locations')
        // .then bedeutet "wenn die Antwort kommt, mach das:"
        .then(response => response.json())
        // data ist jetzt unsere Liste von Locations
        .then(data => {
            // Locations speichern damit der Filter sie später benutzen kann
            allLocations = data;
            // Marker Funktion aufrufen statt direkt hier zu zeichnen
            showMarkers(data);
        });
}

// Marker auf der Karte anzeigen - eigene Funktion damit Filter sie auch benutzen kann
// Marker auf der Karte anzeigen - eigene Funktion damit Filter sie auch benutzen kann
function showMarkers(locations) {
    // Zuerst alle alten Marker entfernen bevor neue gesetzt werden
    allMarkers.forEach(marker => map.removeLayer(marker));
    allMarkers = [];

    locations.forEach(location => {
        // Farbe basierend auf Typ
        let color = '';
        if (location.type === 'park') color = 'green';
        else if (location.type === 'cafe') color = 'orange';
        else color = 'blue';

        // Farbigen Marker erstellen
        const icon = L.divIcon({
            className: '',
            html: `<div style="
                background-color: ${color === 'green' ? '#2d6a4f' : color === 'orange' ? '#e07b39' : '#3b82f6'};
                width: 24px;
                height: 24px;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 24]
        });

        const marker = L.marker([location.lat, location.lng], { icon })
            .addTo(map)
            .on('click', () => showInfoPanel(location));

        allMarkers.push(marker);
    });
}

// Info Panel links befüllen wenn User auf Marker klickt
function showInfoPanel(location) {
    // Crowd Level in Text und Klasse umwandeln
    let crowdText = '';
    let crowdClass = '';
    let crowdIcon = '';
    if (location.crowd_level <= 33) {
        crowdText = 'Quiet';
        crowdClass = 'quiet';
        crowdIcon = '🔇 Quiet environment<br>🪑 Seats available<br>👤 Few people';
    } else if (location.crowd_level <= 66) {
        crowdText = 'Medium';
        crowdClass = 'medium';
        crowdIcon = '🔉 Moderate noise<br>🪑 Some seats available<br>👥 Some people';
    } else {
        crowdText = 'Crowded';
        crowdClass = 'crowded';
        crowdIcon = '🔊 Loud environment<br>🚫 Limited seating<br>👥 Many people';
    }

    const favButton = token ? 
        `<button onclick="addFavorite(${JSON.stringify(location).replace(/"/g, '&quot;')})">⭐ Add to Favorites</button>` 
        : `<p><i>Login to save favorites</i></p>`;

    document.getElementById('info-panel').innerHTML = `
        <h2>${location.name}</h2>
        <p>${location.type}</p>
        <hr/>
        <p style="font-size:0.85rem; color:#999;">Crowded right now</p>
        <div class="crowd-circle">
            <div class="crowd-ring ${crowdClass}">
                ${location.crowd_level}%
            </div>
            <div class="crowd-info">
                <p>${crowdIcon}</p>
            </div>
        </div>
        <hr/>
        <div class="recommendations-box">
            <div id="recommendations-panel"></div>
        </div>
        <hr/>
        ${favButton}
        <div id="rating-panel"></div>
        <div id="favorites-panel"></div>
    `;

    loadRecommendations(location);
    loadRatings(location);
    loadFavorites();
}

// Recommendations vom Backend holen und im Info Panel anzeigen
function loadRecommendations(location) {
    fetch(`http://localhost:5000/recommendations/${location.id}?type=${location.type}&crowd_level=${location.crowd_level}`)
        .then(response => response.json())
        .then(data => {
            let recHtml = '<h4>💡 Recommendations</h4>';
            data.recommendations.forEach(rec => {
                recHtml += `<p>${rec}</p>`;
            });
            document.getElementById('recommendations-panel').innerHTML = recHtml;
        });
}

// Ratings laden und anzeigen
function loadRatings(location) {
    fetch(`http://localhost:5000/ratings/${location.id}`)
        .then(response => response.json())
        .then(data => {
            let ratingHtml = '<h4>⭐ How accurate was our prediction?</h4>';
            
            // Durchschnitt anzeigen wenn Bewertungen vorhanden
            if (data.average) {
                ratingHtml += `<p>Average: ${'⭐'.repeat(Math.round(data.average))} (${data.average}/5 — ${data.count} ratings)</p>`;
            } else {
                ratingHtml += '<p>No ratings yet</p>';
            }

            // Rating Formular nur wenn eingeloggt
            if (token) {
                ratingHtml += `
                    <div id="rating-form">
                        <p>Rate the accuracy:</p>
                        <div id="stars">
                            <span onclick="setRating(1)">☆</span>
                            <span onclick="setRating(2)">☆</span>
                            <span onclick="setRating(3)">☆</span>
                            <span onclick="setRating(4)">☆</span>
                            <span onclick="setRating(5)">☆</span>
                        </div>
                        <button onclick="submitRating(${location.id})">Submit</button>
                    </div>
                `;
            } else {
                ratingHtml += '<p><i>Login to rate this location</i></p>';
            }

            document.getElementById('rating-panel').innerHTML = ratingHtml;
        });
}

// selectedRating speichert den aktuell ausgewählten Stern
let selectedRating = 0;

// Stern auswählen - ★ FIX: sucht Sterne nur innerhalb #rating-form
function setRating(value) {
    selectedRating = value;
    // Sterne nur innerhalb des rating-form updaten
    const stars = document.querySelectorAll('#rating-form #stars span');
    stars.forEach((star, index) => {
        star.textContent = index < value ? '⭐' : '☆';
    });
}

// Bewertung abschicken - POST Request mit Token
function submitRating(locationId) {
    if (!selectedRating || selectedRating === 0) {
        alert('Please select a star rating first!');
        return;
    }

    fetch(`http://localhost:5000/ratings/${locationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Token mitschicken damit Backend weiß wer eingeloggt ist
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ accuracy: selectedRating })
    })
    .then(response => response.json())
    .then(() => {
        // Rating zurücksetzen nach dem Abschicken
        selectedRating = 0;
        // Ratings neu laden damit der neue Durchschnitt angezeigt wird
        loadRatings({ id: locationId });
    });
}

// Filter Funktion - wird aufgerufen wenn User Checkbox anhakt
function filterLocations() {
    // Alle Checkboxen im Filter Panel holen
    const typeCheckboxes = document.querySelectorAll('#filter-panel input[type="checkbox"]');
    const checkedTypes = [];
    const checkedCrowds = [];

    // Schauen welche Checkboxen angehakt sind
    typeCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            // Ist es ein Type oder Crowd Filter?
            if (['park', 'library', 'cafe'].includes(checkbox.value)) {
                checkedTypes.push(checkbox.value);
            } else {
                checkedCrowds.push(checkbox.value);
            }
        }
    });

    // Wenn nichts angehakt → zeige alle Locations
    let filtered = allLocations;

    // Nach Type filtern
    if (checkedTypes.length > 0) {
        filtered = filtered.filter(loc => checkedTypes.includes(loc.type));
    }

    // Nach Crowd Level filtern
    if (checkedCrowds.length > 0) {
        filtered = filtered.filter(loc => {
            if (checkedCrowds.includes('quiet') && loc.crowd_level <= 33) return true;
            if (checkedCrowds.includes('medium') && loc.crowd_level <= 66) return true;
            if (checkedCrowds.includes('crowded') && loc.crowd_level > 66) return true;
            return false;
        });
    }

    // Gefilterte Marker auf der Karte anzeigen
    showMarkers(filtered);
}

// Favorite hinzufügen - POST Request mit Token
function addFavorite(location) {
    fetch('http://localhost:5000/favorites', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            // Token mitschicken damit Backend weiß wer eingeloggt ist
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            location_name: location.name,
            location_type: location.type,
            crowd_level: location.crowd_level,
            lat: location.lat,
            lng: location.lng
        })
    })
    .then(response => response.json())
    .then(() => {
        // Favorites neu laden damit die Liste aktuell ist
        loadFavorites();
    });
}

// Favorites vom Backend holen und im Info Panel anzeigen
function loadFavorites() {
    // Nur wenn eingeloggt - token ist null wenn nicht eingeloggt
    if (!token) return;

    fetch('http://localhost:5000/favorites', {
        // Token mitschicken
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(data => {
        let favHtml = '<h3>⭐ Your Favorites</h3>';
        if (data.length === 0) {
            favHtml += '<p>No favorites yet</p>';
        } else {
            // Für jedes Favorite einen Eintrag mit Delete Button erstellen
            data.forEach(fav => {
                favHtml += `
                    <div class="favorite-item">
                        <b>${fav.location_name}</b>
                        <p>${fav.crowd_level}% crowded</p>
                        <button onclick="deleteFavorite(${fav.id})">🗑 Remove</button>
                    </div>
                `;
            });
        }
        // Favorites Panel updaten
        if (document.getElementById('favorites-panel')) {
            document.getElementById('favorites-panel').innerHTML = favHtml;
        }
    });
}

// Favorite löschen - DELETE Request mit Token
function deleteFavorite(id) {
    fetch(`http://localhost:5000/favorites/${id}`, {
        method: 'DELETE',
        // Token mitschicken damit Backend weiß wer eingeloggt ist
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(() => {
        // Favorites neu laden nach dem Löschen
        loadFavorites();
    });
}

// DELETE Request - Location löschen
function deleteLocation(id) {
    // fetch mit method DELETE - sagt dem Backend "lösche diese Location"
    fetch(`http://localhost:5000/locations/${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(() => {
        // Info Panel zurücksetzen
        document.getElementById('info-panel').innerHTML = 
            '<p id="default-text">Klick auf einen Marker um Details zu sehen</p>';
        // Locations neu laden damit Marker verschwindet
        loadLocations();
    });
}

// Funktion aufrufen - Seite starten
loadLocations();