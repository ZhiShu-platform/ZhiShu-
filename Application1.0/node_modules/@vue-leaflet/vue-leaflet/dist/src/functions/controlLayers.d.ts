import type L from "leaflet";
export declare const controlLayersProps: {
    readonly collapsed: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly autoZIndex: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly hideSingleBase: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly sortLayers: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly sortFunction: {
        readonly type: FunctionConstructor;
    };
    readonly position: {
        readonly type: import("vue").PropType<L.ControlPosition>;
    };
    readonly options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
};
export declare const setupControlLayers: (props: any, leafletRef: any) => {
    options: L.Control.LayersOptions;
    methods: {
        addLayer(layer: any): void;
        removeLayer(layer: any): void;
    };
};
