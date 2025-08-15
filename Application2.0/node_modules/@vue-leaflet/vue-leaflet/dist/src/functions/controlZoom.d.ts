import type L from "leaflet";
export declare const controlZoomProps: {
    readonly zoomInText: {
        readonly type: StringConstructor;
    };
    readonly zoomInTitle: {
        readonly type: StringConstructor;
    };
    readonly zoomOutText: {
        readonly type: StringConstructor;
    };
    readonly zoomOutTitle: {
        readonly type: StringConstructor;
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
export declare const setupControlZoom: (props: any, leafletRef: any) => {
    options: L.Control.ZoomOptions;
    methods: {
        setPosition(position: any): void;
    };
};
