import type L from "leaflet";
export declare const controlAttributionProps: {
    readonly prefix: {
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
export declare const setupControlAttribution: (props: any, leafletRef: any) => {
    options: L.Control.AttributionOptions;
    methods: {
        setPrefix(prefix: any): void;
        setPosition(position: any): void;
    };
};
