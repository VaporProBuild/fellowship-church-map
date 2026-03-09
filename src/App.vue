<template>
  <div v-if="loading" class="spinner-overlay">
    <div class="spinner"></div>
  </div>
  <div class="main-bg">
    <div class="header">
      NOTICE: This is a Prototype for the Fellowship of Evangelical Baptists (FEB) Church Finder in Central Canada. It is built using Vue.js and Leaflet for mapping. The church data is sourced from a JSON file containing information about 70% of FEB churches, including their names, addresses, phone numbers, and geographic coordinates.
    </div>
    <div class="intro">
      <div class="share-parent">
        <button class="share-button" @click="sharePage">
          Share
        </button>
      </div>
      <span class="title">Find a Church Near You!</span>
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
    <div class="radius-slider">
      <label for="radius">Radius: {{ radius }} km</label>
      <input type="range" id="radius" min="3" max="100" v-model="radius" @input="updateRadius" />
    </div>
    <div class="map-container">
      <l-map ref="churchMap" :zoom="mapZoom" :center="mapCenter" class="map">
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
    </div>
    <div v-if="closestChurches.length" class="closest-churches">
      <span class="closest-church-title">{{ closestChurches.length }} Churches Within {{ radius }} km:</span>
        <div v-for="church in closestChurches" :key="church.name" class="church-near-me">
          {{ church.name }} - {{ church.address }} ({{ church.distance.toFixed(2) }} km away)
          <div>
            <button @click="notSetup">Website</button>
            <button @click="notSetup">Directions</button>
          </div>
        </div>
    </div>
    <div v-else-if="searched" class="no-results">
      <span class="closest-church-title">No Churches Within {{ radius }} km please increase the radius.</span>
    </div>
    <div class="footer">
      This is a prototype built by Schaefer Software. For feedback or questions, please contact: <a href="mailto:schaefersoftwaresolutions@gmail.com">schaefersoftwaresolutions@gmail.com</a>
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
      radius: 20,
      showClosest: false,
      mapCenter: [43.7, -79.4],
      mapZoom: 7,
      churchIcon: churchIcon,
      personIcon: personIcon,
      searchAddress: '',
      loading: false,
      searched: false
    }
  },
  computed: {
    filteredChurches() {
      // Only churches with valid lat/lng
      return this.churches.filter(c => c.latitude && c.longitude);
    }
  },
  methods: {
    async sharePage() {
      const shareData = {
        title: 'FEB Church Finder',
        text: 'Find a Fellowship of Evangelical Baptist church near you.',
        url: window.location.href
      };

      if (navigator.share) {
        try {
          await navigator.share(shareData);
        } catch (err) {
          console.error('Share cancelled', err);
        }
      } else {
        try {
          await navigator.clipboard.writeText(window.location.href);
          alert('Link copied to clipboard');
        } catch {
          alert('Unable to share or copy link');
        }
      }
    },
    updateClosestChurches(lat, lon) {
      this.userLocation = [lat, lon];

      const distances = this.filteredChurches.map(church => ({
        ...church,
        distance: haversineDistance(
          lat,
          lon,
          church.latitude,
          church.longitude
        )
      }));

      this.closestChurches = distances
        .filter(church => church.distance <= this.radius)
        .sort((a, b) => a.distance - b.distance);

      this.updateMapView(lat, lon);
    },
    updateMapView(lat, lon) {
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

      this.scrollToMap();
    },
    scrollToMap() {
      this.$nextTick(() => {
        const mapEl = this.$refs.churchMap?.$el;
        if (mapEl) {
          mapEl.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    },
    async searchByAddress() {
      this.loading = true;
      this.searched = true;

      if (!this.searchAddress) {
        alert("Please enter an address");
        this.loading = false;
        return;
      }

      try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(this.searchAddress)}`;
        const response = await fetch(url);
        const results = await response.json();

        if (!results.length) {
          alert("Address not found");
          this.loading = false;
          return;
        }

        const lat = parseFloat(results[0].lat);
        const lon = parseFloat(results[0].lon);

        this.updateClosestChurches(lat, lon);

      } catch (err) {
        console.error("Address search error:", err);
        alert("Error searching address");
      }

      this.loading = false;
    },
    notSetup() {
      alert('This feature is not set up yet.');
    },
    findClosestChurches() {
      this.loading = true;
      this.searched = true;

      if (!navigator.geolocation) {
        alert("Geolocation not supported");
        this.loading = false;
        return;
      }

      navigator.geolocation.getCurrentPosition(
        pos => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;

          this.updateClosestChurches(lat, lon);

          this.loading = false;
        },
        err => {
          alert("Could not get location. Error: " + err.message);
          this.loading = false;
        }
      );
    },
    updateRadius() {
      // Recalculate closest churches if userLocation is set
      if (this.userLocation) {
        const [lat, lon] = this.userLocation;
        const distances = this.filteredChurches.map(church => ({
          ...church,
          distance: haversineDistance(
            lat,
            lon,
            church.latitude,
            church.longitude
          )
        }));
        this.closestChurches = distances
          .filter(church => church.distance <= this.radius)
          .sort((a, b) => a.distance - b.distance);
      }
    },
  }
}
</script>

<style scoped>
.no-results {
  margin-bottom: 3rem;
}

.radius-slider {
  width: 85%;
  max-width: 900px;
  margin: 1rem auto 0 auto;
  display: flex;
  align-items: center;
  gap: 1em;
  font-size: 1.1em;
  color: var(--c-blue);
}
.radius-slider input[type="range"] {
  flex: 1;
  accent-color: var(--c-blue);
  height: 2px;
}
.title {
  color: var(--c-blue);
  text-align: center;
  margin: 1em 0 0.5em 0;
  font-weight: bold;
  font-size: 1.75rem;
}

.closest-church-title {
  color: var(--c-blue);
  font-weight: bold;
  font-size: 1.25rem;
  margin-bottom: 0.5em;
}

.share-parent {
  display: flex;
  justify-content: flex-end;
}
.share-button {
  background: var(--c-blue);
  color: var(--c-bg);
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;

  box-shadow:
    0 6px 14px rgba(0,0,0,0.18),
    0 3px 6px rgba(0,0,0,0.12);
} 
.spinner-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(245,243,243,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000000;
}
.spinner {
  border: 6px solid var(--c-bg);
  border-top: 6px solid var(--c-blue);
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
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
  margin-bottom: 1rem;
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

.map-container {
  width: 85%;
  max-width: 900px;
  height: 27rem;
  margin: 1rem auto;
  border: 0.375rem solid var(--c-font);
  border-radius: 1rem;
  overflow: hidden;
}

.map {
  height: 100%;
  width: 100%;
}

.closest-churches {
  width: 85%;
  max-width: 900px;
  margin: 0 auto 2rem auto;
  gap: 0.25rem;
  display: flex;
  flex-direction: column;
}

.church-near-me {
  background: var(--c-white);
  color: var(--c-font);
  padding: 0.75em;
  border-radius: 1rem;
}

.footer {
  background-color: var(--c-blue);
  color: var(--c-white);
  text-align: center;
  padding: 1em;
  padding-bottom: 2rem;
  font-weight: bold;
}
</style>
