<script lang="ts" setup>
import Map from "ol/Map";
import View from "ol/View";
import OSM from "ol/source/OSM";
import GeoJSON from 'ol/format/GeoJSON';

import TileLayer from "ol/layer/Tile";
import Geolocation from "ol/Geolocation";
import { FullScreen, defaults as defaultControls } from "ol/control";

import "ol/ol.css";
import { ref, onMounted } from "vue";
import VectorSource from "ol/source/Vector";
import Feature from "ol/Feature";
import { MultiPoint, Point } from "ol/geom";
import { Vector } from "ol/layer";
import Overlay from "ol/Overlay";
import { Popup } from ".";

type ClickedPet = {
  name: string,
  url: string,
}

const map_popup = ref<InstanceType<typeof Popup> | null>(null);

const clicked_pet = ref<ClickedPet | null>(null);
let view = new View({
  center: [0, 0],
  zoom: 2,
});

const geolocation = new Geolocation({
  trackingOptions: {
    enableHighAccuracy: true,
  },
  tracking: true,
  projection: view.getProjection(),
});

geolocation.once("change:position", function () {
  view.setCenter(geolocation.getPosition());
  view.setResolution(10);
});

const base_point = [729000, 7024000];
const points = [];
for (let i = 0; i < 15; i++) {
  points.push([
    base_point[0] + (Math.random() - 0.5) * 10000,
    base_point[1] + (Math.random() - 0.5) * 10000,
  ]);
}
const iconFeature = new Feature({
  geometry: new MultiPoint(points),
  name: "Null Island",
  population: 4000,
  rainfall: 500,
});

onMounted(async () => {
  const map = new Map({
    controls: defaultControls().extend([new FullScreen()]),
    layers: [
      new TileLayer({ source: new OSM() }),
      new Vector({
        source: new VectorSource({ url: "/api/v1/pets", format: new GeoJSON() }),
        style: {
          "icon-src": "/imgs/lost_pet_icon.png",
          "icon-opacity": 0.7,
        },
      }),
    ],
    view: view,
    target: "map",
  });

  const element = document.getElementById("popup") || undefined;

  const popup = new Overlay({
    element: element,
    positioning: "bottom-center",
    stopEvent: false,
  });
  map.addOverlay(popup);

  // display popup on click
  map.on("click", function (evt) {
    const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
      return feature;
    });

    clicked_pet.value = null;

    if (!feature || map_popup.value === null) {
      return;
    }

    clicked_pet.value = { name: feature.get("name"), url: feature.get("image-url") };
    map_popup.value?.togglePopup();
  });
});
</script>

<template>
  <div>
    <div id="map" class="map"></div>
    <Popup ref="map_popup">
      <h2>Lost pet {{ clicked_pet?.name }}!</h2>
      <img :src="clicked_pet?.url" alt="Image of pet {{clicked_pet?.name}}">
    </Popup>
  </div>
</template>

<style scoped>
#map {
  position: fixed;
  width: 100%;
  height: 100%;
  left: 0;
}

.map:-webkit-full-screen {
  height: 100%;
  margin: 0;
}

.map:fullscreen {
  height: 100%;
}

img {
  max-width: 20rem;
}

</style>
