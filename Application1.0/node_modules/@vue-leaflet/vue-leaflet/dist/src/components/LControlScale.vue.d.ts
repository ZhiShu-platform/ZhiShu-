import type L from "leaflet";
declare const _sfc_main: import("vue").DefineComponent<{
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
}, {
    leafletObject: import("vue").Ref<L.Control.Scale | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
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
}>>, {
    readonly options: Record<string, any>;
    readonly metric: boolean;
    readonly imperial: boolean;
    readonly updateWhenIdle: boolean;
}>;
export default _sfc_main;
