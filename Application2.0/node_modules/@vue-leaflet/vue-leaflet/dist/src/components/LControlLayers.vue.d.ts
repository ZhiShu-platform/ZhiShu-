import type L from "leaflet";
declare const _sfc_main: import("vue").DefineComponent<{
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
}, {
    leafletObject: import("vue").Ref<L.Control.Layers | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
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
}>>, {
    readonly options: Record<string, any>;
    readonly collapsed: boolean;
    readonly autoZIndex: boolean;
    readonly hideSingleBase: boolean;
    readonly sortLayers: boolean;
}>;
export default _sfc_main;
