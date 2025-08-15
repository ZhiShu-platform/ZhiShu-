import type L from "leaflet";
declare const _sfc_main: import("vue").DefineComponent<{
    disableClickPropagation: {
        type: BooleanConstructor;
        custom: boolean;
        default: boolean;
    };
    disableScrollPropagation: {
        type: BooleanConstructor;
        custom: boolean;
        default: boolean;
    };
    position: {
        readonly type: import("vue").PropType<L.ControlPosition>;
    };
    options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
}, {
    root: import("vue").Ref<HTMLInputElement | undefined>;
    leafletObject: import("vue").Ref<L.Control | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    disableClickPropagation: {
        type: BooleanConstructor;
        custom: boolean;
        default: boolean;
    };
    disableScrollPropagation: {
        type: BooleanConstructor;
        custom: boolean;
        default: boolean;
    };
    position: {
        readonly type: import("vue").PropType<L.ControlPosition>;
    };
    options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
}>>, {
    options: Record<string, any>;
    disableClickPropagation: boolean;
    disableScrollPropagation: boolean;
}>;
export default _sfc_main;
