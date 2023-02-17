<script lang="ts" setup>
import Geolocation from "ol/Geolocation";
import Map from "ol/Map";
import View from "ol/View";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { FullScreen, defaults as defaultControls } from "ol/control";
import TileLayer from "ol/layer/Tile";
import OSM from "ol/source/OSM";
import { defaults as defaultInteractions, Interaction } from "ol/interaction";
import type MapBrowserEvent from "ol/MapBrowserEvent";
import MapBrowserEventType from "ol/MapBrowserEventType";
import { Vector } from "ol/layer";
import VectorSource from "ol/source/Vector";
import Feature from "ol/Feature";
import { Point } from "ol/geom";
import type { Coordinate } from "ol/coordinate";

const router = useRouter();
const map = ref(null as Map | null);
const pointFeature = new Feature(new Point([1e20, 0]));
const selected_position = ref(null as Coordinate | null);

class DoubleClickSelect extends Interaction {
  constructor() {
    super();
  }

  handleEvent(event: MapBrowserEvent<any>): boolean {
    let stopEvent = false;
    if (
      event.type === MapBrowserEventType.DBLCLICK ||
      event.type === MapBrowserEventType.CLICK
    ) {
      const browserEvent: MouseEvent = event.originalEvent;
      const anchor = event.coordinate;
      pointFeature.setGeometry(new Point(anchor));
      browserEvent.preventDefault();
      stopEvent = true;
      selected_position.value = anchor;
    }
    return !stopEvent;
  }
}

onMounted(async () => {
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

  map.value = new Map({
    controls: defaultControls().extend([new FullScreen()]),
    layers: [
      new TileLayer({ source: new OSM() }),
      new Vector({
        source: new VectorSource({ features: [pointFeature] }),
        style: {
          "icon-src": "/imgs/lost_pet_icon.png",
          "icon-opacity": 0.7,
        },
      }),
    ],
    view: view,
    target: "map-picker",
    interactions: defaultInteractions({ doubleClickZoom: false }).extend([
      new DoubleClickSelect(),
    ]),
  });
});
</script>

<template>
  <h2>Report a lost Pet</h2>
  <div class="container">
    <form>
      <!-- Email input -->
      <div class="form-outline mb-4">
        <label class="form-label" for="pet-name">Pet name</label>
        <input type="text" id="pet-name" class="form-control" />
      </div>

      <div class="form-outline mb-4">
        <div id="map-picker" class="map"></div>
        <input type="hidden" :value="selected_position" />
        <p class="form-text" v-if="selected_position !== null">
          Coordinates: {{ Math.round(selected_position[0]) }},
          {{ Math.round(selected_position[1]) }}
        </p>
      </div>
    </form>
  </div>
</template>

<style scoped>
.map {
  height: 20rem;
}
</style>
