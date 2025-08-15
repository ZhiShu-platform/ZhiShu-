import type L from "leaflet";
export interface IMapBlueprint {
    ready: boolean;
    leafletRef?: L.Map;
    layerControl?: any;
    layersToAdd: any[];
    layersInControl: any[];
    lastSetBounds?: L.LatLngBounds;
    lastSetCenter?: L.LatLng;
}
