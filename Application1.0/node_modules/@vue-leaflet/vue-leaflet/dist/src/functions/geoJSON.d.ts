import type { GeoJsonObject } from "geojson";
import type L from "leaflet";
import type { PropType } from "vue";
export declare const geoJSONProps: {
    readonly geojson: {
        readonly type: PropType<GeoJsonObject | GeoJsonObject[]>;
        readonly custom: true;
    };
    readonly optionsStyle: {
        readonly type: PropType<L.StyleFunction<any>>;
        readonly custom: true;
    };
    readonly pane: {
        readonly type: StringConstructor;
    };
    readonly attribution: {
        readonly type: StringConstructor;
    };
    readonly name: {
        readonly type: StringConstructor;
        readonly custom: true;
    };
    readonly layerType: {
        readonly type: PropType<import("../types/enums/LayerType").LayerType>;
        readonly custom: true;
    };
    readonly visible: {
        readonly type: BooleanConstructor;
        readonly custom: true;
        readonly default: true;
    };
    readonly options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
};
export declare const setupGeoJSON: (props: any, leafletRef: any, context: any) => {
    options: L.GeoJSONOptions<any, import("geojson").Geometry>;
    methods: {
        setGeojson(newVal: any): void;
        setOptionsStyle(newVal: any): void;
        getGeoJSONData(): any;
        getBounds(): any;
        addLayer(layer: any): void;
        removeLayer(layer: any): void;
        setAttribution(val: any): void;
        setName(): void;
        setLayerType(): void;
        setVisible(isVisible: any): void;
        bindPopup(leafletObject: any): void;
        bindTooltip(leafletObject: any): void;
        unbindTooltip(): void;
        unbindPopup(): void;
        updateVisibleProp(value: any): void;
    };
};
