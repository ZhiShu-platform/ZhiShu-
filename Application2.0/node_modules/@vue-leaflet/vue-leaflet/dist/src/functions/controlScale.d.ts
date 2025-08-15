import type L from "leaflet";
export declare const controlScaleProps: {
    readonly maxWidth: {
        readonly type: NumberConstructor;
    };
    readonly metric: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly imperial: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly updateWhenIdle: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
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
export declare const setupControlScale: (props: any, leafletRef: any) => {
    options: L.Control.ScaleOptions;
    methods: {
        setPosition(position: any): void;
    };
};
