import type L from "leaflet";
declare const _sfc_main: import("vue").DefineComponent<{
    readonly layers: {
        readonly type: StringConstructor;
        readonly required: true;
    };
    readonly styles: {
        readonly type: StringConstructor;
    };
    readonly format: {
        readonly type: StringConstructor;
    };
    readonly transparent: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly version: {
        readonly type: StringConstructor;
    };
    readonly crs: {
        readonly type: ObjectConstructor;
    };
    readonly uppercase: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly tms: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly subdomains: {
        readonly type: import("vue").PropType<String | String[]>;
        readonly validator: (prop: any) => boolean;
    };
    readonly detectRetina: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly url: {
        readonly type: StringConstructor;
        readonly required: true;
        readonly custom: true;
    };
    readonly opacity: {
        readonly type: NumberConstructor;
    };
    readonly zIndex: {
        readonly type: NumberConstructor;
    };
    readonly tileSize: {
        readonly type: import("vue").PropType<Number | L.PointExpression>;
    };
    readonly noWrap: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly minZoom: {
        readonly type: NumberConstructor;
    };
    readonly maxZoom: {
        readonly type: NumberConstructor;
    };
    readonly className: {
        readonly type: StringConstructor;
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
    leafletObject: import("vue").Ref<L.TileLayer.WMS | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly layers: {
        readonly type: StringConstructor;
        readonly required: true;
    };
    readonly styles: {
        readonly type: StringConstructor;
    };
    readonly format: {
        readonly type: StringConstructor;
    };
    readonly transparent: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly version: {
        readonly type: StringConstructor;
    };
    readonly crs: {
        readonly type: ObjectConstructor;
    };
    readonly uppercase: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly tms: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly subdomains: {
        readonly type: import("vue").PropType<String | String[]>;
        readonly validator: (prop: any) => boolean;
    };
    readonly detectRetina: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly url: {
        readonly type: StringConstructor;
        readonly required: true;
        readonly custom: true;
    };
    readonly opacity: {
        readonly type: NumberConstructor;
    };
    readonly zIndex: {
        readonly type: NumberConstructor;
    };
    readonly tileSize: {
        readonly type: import("vue").PropType<Number | L.PointExpression>;
    };
    readonly noWrap: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly minZoom: {
        readonly type: NumberConstructor;
    };
    readonly maxZoom: {
        readonly type: NumberConstructor;
    };
    readonly className: {
        readonly type: StringConstructor;
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
    readonly noWrap: boolean;
    readonly tms: boolean;
    readonly detectRetina: boolean;
    readonly transparent: boolean;
    readonly uppercase: boolean;
}>;
export default _sfc_main;
