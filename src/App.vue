<template>
  <div>
    <h1>Fellowship Church Map Proof of Concept</h1>
  <l-map :zoom="mapZoom" :center="mapCenter" style="height: 500px; width: 100%">
      <l-tile-layer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; <a href='https://osm.org/copyright'>OpenStreetMap</a> contributors"
      />
      <l-marker
        v-for="(church, idx) in filteredChurches"
        :key="church.name || idx"
        :lat-lng="[church.latitude, church.longitude]"
      >
        <l-popup>
          <strong>{{ church.name }}</strong><br />
          {{ church.address }}<br />
          {{ church.phone }}
        </l-popup>
      </l-marker>
      <l-marker v-if="userLocation" :lat-lng="userLocation" :icon="yellowIcon">
        <l-popup>Your Location</l-popup>
      </l-marker>
    </l-map>
    <button @click="findClosestChurches">Find Closest Churches</button>
    <div v-if="closestChurches.length">
      <h2>Closest Churches:</h2>
      <ul>
        <li v-for="church in closestChurches" :key="church.name">
          {{ church.name }} - {{ church.address }} ({{ church.distance.toFixed(2) }} km away)
        </li>
      </ul>
    </div>
    <div style="margin: 1em 0;">
      <input v-model="searchAddress" placeholder="Enter address" style="width: 300px;" />
      <button @click="searchByAddress">Search by Address</button>
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

const yellowIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
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
      yellowIcon: yellowIcon,
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
          this.mapCenter = [pos.coords.latitude, pos.coords.longitude];
          this.mapZoom = 12;
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
        this.mapCenter = [lat, lon];
        this.mapZoom = 12;
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
      } catch (err) {
        alert('Error searching address');
        console.error('Address search error:', err);
      }
    }
  }
}
</script>

<style scoped>
#map {
  height: 500px;
  width: 100%;
}
</style>
