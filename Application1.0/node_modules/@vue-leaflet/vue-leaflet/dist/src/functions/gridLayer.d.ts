import type L from "leaflet";
import { type PropType } from "vue";
import { type VNode } from "vue";
export type VueGridLayerTileRenderer = (props: {
    coords: L.Point;
}) => () => VNode;
export declare const gridLayerProps: {
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
export declare const setupGridLayer: (props: any, leafletRef: any, context: any) => {
    options: L.GridLayerOptions;
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
export declare const CreateVueGridLayer: (GridLayer: typeof L.GridLayer, DomUtil: typeof L.DomUtil, Util: typeof L.Util, childRenderer: VueGridLayerTileRenderer) => (new (options: L.GridLayerOptions) => L.GridLayer) & typeof L.Class;
