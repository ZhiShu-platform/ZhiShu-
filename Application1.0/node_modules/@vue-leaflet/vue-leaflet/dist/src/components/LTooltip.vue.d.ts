import type L from "leaflet";
/**
 * Display a tooltip on the map
 */
declare const _sfc_main: import("vue").DefineComponent<{
    readonly content: {
        readonly type: StringConstructor;
        readonly default: null;
    };
    readonly options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
}, {
    root: import("vue").Ref<null>;
    leafletObject: import("vue").Ref<L.Tooltip | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly content: {
        readonly type: StringConstructor;
        readonly default: null;
    };
    readonly options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
}>>, {
    readonly options: Record<string, any>;
    readonly content: string;
}>;
export default _sfc_main;
