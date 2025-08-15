import type L from "leaflet";
import type { PropType } from "vue";
export declare const tileLayerProps: {
    readonly tms: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly subdomains: {
        readonly type: PropType<String | String[]>;
        readonly validator: (prop: any) => boolean;
    };
    readonly detectRetina: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly url: {
        readonly type: StringConstructor;
        readonly required: true;
        readonly custom: true;
    };
    readonly opacity: {
        readonly type: NumberConstructor;
    };
    readonly zIndex: {
        readonly type: NumberConstructor;
    };
    readonly tileSize: {
        readonly type: PropType<Number | L.PointExpression>;
    };
    readonly noWrap: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly minZoom: {
        readonly type: NumberConstructor;
    };
    readonly maxZoom: {
        readonly type: NumberConstructor;
    };
    readonly className: {
        readonly type: StringConstructor;
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
export declare const setupTileLayer: (props: any, leafletRef: any, context: any) => {
    options: L.TileLayerOptions;
    methods: {
        setTileComponent(): void;
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
