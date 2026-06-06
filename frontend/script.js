// Karte erstellen und auf Wien zentrieren
// 48.2082, 16.3738 sind die GPS Koordinaten von Wien
// 13 ist der Zoom Level - je höher desto näher
const map = L.map('map').setView([48.2082, 16.3738], 13);

// Kartenkacheln von OpenStreetMap laden
// Das sind die echten Kartenbilder die wir sehen
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

// ★ NEU: Hier speichern wir alle Locations und Marker für den Filter
let allLocations = [];
let allMarkers = [];

//AB HIER Frontend-Backend verbindung

// Locations vom Backend holen und auf der Karte anzeigen
function loadLocations() {
    // fetch macht einen GET Request an unser Backend
    // AJAX Call - wir fragen den Server nach Daten, ohne die Seite neu zu laden
    fetch('http://localhost:5000/locations')
        // .then bedeutet "wenn die Antwort kommt, mach das:"
        .then(response => response.json())
        // data ist jetzt unsere Liste von Locations
        .then(data => {
            // ★ NEU: Locations speichern damit der Filter sie später benutzen kann
            allLocations = data;
            // ★ NEU: Marker Funktion aufrufen statt direkt hier zu zeichnen
            showMarkers(data);
        });
}

// ★ NEU: Marker auf der Karte anzeigen - eigene Funktion damit Filter sie auch benutzen kann
function showMarkers(locations) {
    // ★ NEU: Zuerst alle alten Marker entfernen bevor neue gesetzt werden
    allMarkers.forEach(marker => map.removeLayer(marker));
    allMarkers = [];

    locations.forEach(location => {
        const marker = L.marker([location.lat, location.lng])
            .addTo(map)
            // ★ NEU: Klick auf Marker zeigt Info Panel links statt Popup
            .on('click', () => showInfoPanel(location));

        // ★ NEU: Marker in Liste speichern
        allMarkers.push(marker);
    });
}

// ★ NEU: Info Panel links befüllen wenn User auf Marker klickt
function showInfoPanel(location) {
    // Crowd Level in Text umwandeln
    let crowdText = '';
    if (location.crowd_level <= 33) crowdText = '🟢 Quiet';
    else if (location.crowd_level <= 66) crowdText = '🟡 Medium';
    else crowdText = '🔴 Crowded';

    // HTML ins Info Panel schreiben - ersetzt den default Text
    document.getElementById('info-panel').innerHTML = `
        <h2>${location.name}</h2>
        <p>${location.type}</p>
        <hr/>
        <h3>${location.crowd_level}% ${crowdText}</h3>
        <br/>
        <button onclick="deleteLocation(${location.id})">🗑 Location löschen</button>
    `;
}

// ★ NEU: Filter Funktion - wird aufgerufen wenn User Checkbox anhakt
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

// ★ NEU: DELETE Request - Location löschen
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