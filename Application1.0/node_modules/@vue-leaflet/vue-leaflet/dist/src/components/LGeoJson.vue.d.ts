import type L from "leaflet";
declare const _sfc_main: import("vue").DefineComponent<{
    readonly geojson: {
        readonly type: import("vue").PropType<import("geojson").GeoJsonObject | import("geojson").GeoJsonObject[]>;
        readonly custom: true;
    };
    readonly optionsStyle: {
        readonly type: import("vue").PropType<L.StyleFunction<any>>;
        readonly custom: true;
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
    leafletObject: import("vue").Ref<L.GeoJSON<any, import("geojson").Geometry> | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly geojson: {
        readonly type: import("vue").PropType<import("geojson").GeoJsonObject | import("geojson").GeoJsonObject[]>;
        readonly custom: true;
    };
    readonly optionsStyle: {
        readonly type: import("vue").PropType<L.StyleFunction<any>>;
        readonly custom: true;
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
}>;
export default _sfc_main;
