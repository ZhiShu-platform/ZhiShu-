import type L from "leaflet";
import type { PropType } from "vue";
export declare const markerProps: {
    readonly draggable: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly icon: {
        readonly type: PropType<L.Icon<L.IconOptions>>;
    };
    readonly zIndexOffset: {
        readonly type: NumberConstructor;
    };
    readonly latLng: {
        readonly type: PropType<L.LatLngExpression>;
        readonly custom: true;
        readonly required: true;
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
export declare const setupMarker: (props: any, leafletRef: any, context: any) => {
    options: L.MarkerOptions;
    methods: {
        setDraggable(value: any): void;
        latLngSync(event: any): void;
        setLatLng(newVal: any): void;
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
/**
 * Determine whether the default Leaflet icon should be replaced with a blank div initially.
 *
 * @param {*} options Options object returned by setupMarker
 * @param {*} context Context object returned by setupMarker
 * @returns boolean
 */
export declare const shouldBlankIcon: (options: any, context: any) => any;
