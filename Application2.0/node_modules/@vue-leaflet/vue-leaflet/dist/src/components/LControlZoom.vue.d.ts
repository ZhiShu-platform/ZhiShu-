import type L from "leaflet";
declare const _sfc_main: import("vue").DefineComponent<{
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
}, {
    leafletObject: import("vue").Ref<L.Control.Scale | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
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
}>>, {
    readonly options: Record<string, any>;
}>;
export default _sfc_main;
