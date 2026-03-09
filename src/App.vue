<template>
  <div class="main-bg">
    <div class="header">
      NOTICE: This is a Prototype for the Fellowship of Evangelical Baptists (FEB) Church Finder in Central Canada. It is built using Vue.js and Leaflet for mapping. The church data is sourced from a JSON file containing information about 70% of FEB churches, including their names, addresses, phone numbers, and geographic coordinates.
    </div>
    <div class="intro">
      <h1>Find a Church Near You!</h1>
      <p>
        Welcome to the Feb Central Church Finder! This site helps you connect with churches near you that are part of the Fellowship of Evangelical Baptists (FEB) in Central Canada.<br>
        Enter your address or use your location to discover the closest FEB churches and get connected.
      </p>
    </div>
    <button @click="findClosestChurches">Auto Find Closest Churches</button>
    <center-div>
      <div class="enter-address">
        <input v-model="searchAddress" placeholder="Enter address" class="enter-box" />
        <button @click="searchByAddress">Search</button>
      </div>
    </center-div>
    <l-map :zoom="mapZoom" :center="mapCenter" style="height: 500px; width: 100%">
      <l-tile-layer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; <a href='https://osm.org/copyright'>OpenStreetMap</a> contributors"
      />
      <l-marker
        v-for="(church, idx) in filteredChurches"
        :key="church.name || idx"
        :lat-lng="[church.latitude, church.longitude]"
        :icon="churchIcon"
      >
        <l-popup>
          <strong>{{ church.name }}</strong><br />
          {{ church.address }}<br />
          {{ church.phone }}
        </l-popup>
      </l-marker>
      <l-marker v-if="userLocation" :lat-lng="userLocation" :icon="personIcon">
        <l-popup>Your Location</l-popup>
      </l-marker>
    </l-map>
    <div v-if="closestChurches.length">
      <h2>Closest Churches:</h2>
      <ul>
        <li v-for="church in closestChurches" :key="church.name">
          {{ church.name }} - {{ church.address }} ({{ church.distance.toFixed(2) }} km away)
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { LMap, LTileLayer, LMarker, LPopup } from "@vue-leaflet/vue-leaflet";
import L from 'leaflet';
import febChurches from './febChurches.json'

// Fix for Leaflet's missing icon issue in Vite
import 'leaflet/dist/leaflet.css';
L.Icon.Default.imagePath = 'https://unpkg.com/leaflet@1.9.4/dist/images/';

// Church icon (local SVG)
const churchIcon = new L.Icon({
  iconUrl: '/fellowship-church-map/churchIcon.svg',
  iconSize: [62, 62],
  popupAnchor: [1, -34]
});

// Person icon (local SVG)
const personIcon = new L.Icon({
  iconUrl: '/fellowship-church-map/person.svg',
  iconSize: [45, 45],
  popupAnchor: [1, -34]
});

function haversineDistance(lat1, lon1, lat2, lon2) {
  function toRad(x) { return x * Math.PI / 180; }
  const R = 6371; // km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export default {
  name: 'App',
  components: { LMap, LTileLayer, LMarker, LPopup },
  data() {
    return {
      churches: febChurches,
      userLocation: null,
      closestChurches: [],
      showClosest: false,
      mapCenter: [43.7, -79.4],
      mapZoom: 7,
      churchIcon: churchIcon,
      personIcon: personIcon,
      searchAddress: ''
    }
  },
  computed: {
    filteredChurches() {
      // Only churches with valid lat/lng
      return this.churches.filter(c => c.latitude && c.longitude);
    }
  },
  methods: {
    findClosestChurches() {
      console.log('Find Closest Churches button pressed');
      if (!navigator.geolocation) {
        alert('Geolocation not supported');
        return;
      }
      console.log('Attempting to get user location...');
      navigator.geolocation.getCurrentPosition(
        pos => {
          console.log('User location found:', pos.coords);
          this.userLocation = [pos.coords.latitude, pos.coords.longitude];
          // Calculate distances
          const distances = this.filteredChurches.map(church => ({
            ...church,
            distance: haversineDistance(
              pos.coords.latitude,
              pos.coords.longitude,
              church.latitude,
              church.longitude
            )
          }));
          // Sort by distance and take top 5
          this.closestChurches = distances.sort((a, b) => a.distance - b.distance).slice(0, 5);
          // Zoom to midpoint between user and closest church
          if (this.closestChurches.length > 0) {
            const closest = this.closestChurches[0];
            const midLat = (pos.coords.latitude + closest.latitude) / 2;
            const midLon = (pos.coords.longitude + closest.longitude) / 2;
            this.mapCenter = [midLat, midLon];
            this.mapZoom = 14;
          } else {
            this.mapCenter = [pos.coords.latitude, pos.coords.longitude];
            this.mapZoom = 12;
          }
        },
        err => {
          alert('Could not get location. Error: ' + err.message);
          console.error('Geolocation error:', err);
        }
      );
    },
    async searchByAddress() {
      if (!this.searchAddress) {
        alert('Please enter an address');
        return;
      }
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(this.searchAddress)}`;
      try {
        const response = await fetch(url);
        const results = await response.json();
        if (!results.length) {
          alert('Address not found');
          return;
        }
        const lat = parseFloat(results[0].lat);
        const lon = parseFloat(results[0].lon);
        this.userLocation = [lat, lon];
        // Calculate distances
        const distances = this.filteredChurches.map(church => ({
          ...church,
          distance: haversineDistance(
            lat,
            lon,
            church.latitude,
            church.longitude
          )
        }));
        this.closestChurches = distances.sort((a, b) => a.distance - b.distance).slice(0, 5);
        // Zoom to midpoint between user and closest church
        if (this.closestChurches.length > 0) {
          const closest = this.closestChurches[0];
          const midLat = (lat + closest.latitude) / 2;
          const midLon = (lon + closest.longitude) / 2;
          this.mapCenter = [midLat, midLon];
          this.mapZoom = 14;
        } else {
          this.mapCenter = [lat, lon];
          this.mapZoom = 12;
        }
      } catch (err) {
        alert('Error searching address');
        console.error('Address search error:', err);
      }
    }
  }
}
</script>

<style scoped>
body, .main-bg {
  background: var(--c-bg);
}

.intro {
  background: var(--c-bg);
  color: var(--c-font);
  padding: 2em 1em 1em 1em;
  text-align: center;
}

h1 {
  color: var(--c-blue);
  text-align: center;
  margin: 1em 0 0.5em 0;
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
}

.intro p {
  color: var(--c-font);
  font-size: 1.15em;
  margin-bottom: 2em;
}

button {
  background: var(--c-blue);
  color: var(--c-bg);
  border: none;
  border-radius: 6px;
  padding: 0.6em 1.2em;
  font-size: 1em;
  margin: 0.5em;
  cursor: pointer;

  box-shadow:
    0 0.5rem 1rem rgba(0,0,0,0.12),
    0 0.75rem 1.5rem rgba(0,0,0,0.16);
}

button:hover {
  background: var(--c-font);
}

input {
  border: 1px solid var(--c-font);
  border-radius: 6px;
  padding: 0.5em;
  font-size: 1em;
  color: var(--c-blue);
  background: var(--c-white);
}

h2 {
  color: var(--c-blue);
  margin-top: 1em;
}

ul {
  color: var(--c-font);
  font-size: 1.05em;
}

.header {
  background: yellow;
  color: black;
  font-weight: bold;
  padding: 1em;
  text-align: center;
  font-size: 0.9em;
  border-bottom-left-radius: 1.5rem;
  border-bottom-right-radius: 1.5rem;
}

.enter-address {
  width: 90%;
}
</style>
