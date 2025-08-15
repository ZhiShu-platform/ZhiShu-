import type L from "leaflet";
declare const _sfc_main: import("vue").DefineComponent<{
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
        readonly type: import("vue").PropType<import("../types/enums/LayerType").LayerType>;
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
}, {
    ready: import("vue").Ref<boolean>;
    leafletObject: import("vue").Ref<L.LayerGroup<any> | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
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
        readonly type: import("vue").PropType<import("../types/enums/LayerType").LayerType>;
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
}>>, {
    readonly visible: boolean;
    readonly options: Record<string, any>;
}>;
export default _sfc_main;
