import type L from "leaflet";
/**
 * Marker component, lets you add and personalize markers on the map
 */
declare const _sfc_main: import("vue").DefineComponent<{
    readonly draggable: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly icon: {
        readonly type: import("vue").PropType<L.Icon<L.IconOptions>>;
    };
    readonly zIndexOffset: {
        readonly type: NumberConstructor;
    };
    readonly latLng: {
        readonly type: import("vue").PropType<L.LatLngExpression>;
        readonly custom: true;
        readonly required: true;
    };
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
    leafletObject: import("vue").Ref<L.Marker<any> | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly draggable: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly icon: {
        readonly type: import("vue").PropType<L.Icon<L.IconOptions>>;
    };
    readonly zIndexOffset: {
        readonly type: NumberConstructor;
    };
    readonly latLng: {
        readonly type: import("vue").PropType<L.LatLngExpression>;
        readonly custom: true;
        readonly required: true;
    };
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
    readonly draggable: boolean;
}>;
export default _sfc_main;
