import type L from "leaflet";
/**
 * Rectangle component, lets you add and customize rectangular regions on the map
 */
declare const _sfc_main: import("vue").DefineComponent<{
    readonly latLngs: {
        readonly required: false;
        readonly type: import("vue").PropType<L.LatLngExpression[]>;
        readonly custom: true;
    };
    readonly bounds: {
        readonly type: import("vue").PropType<L.LatLngExpression[]>;
        readonly custom: true;
    };
    readonly smoothFactor: {
        readonly type: NumberConstructor;
    };
    readonly noClip: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly stroke: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly color: {
        readonly type: StringConstructor;
    };
    readonly weight: {
        readonly type: NumberConstructor;
    };
    readonly opacity: {
        readonly type: NumberConstructor;
    };
    readonly lineCap: {
        readonly type: StringConstructor;
    };
    readonly lineJoin: {
        readonly type: StringConstructor;
    };
    readonly dashArray: {
        readonly type: StringConstructor;
    };
    readonly dashOffset: {
        readonly type: StringConstructor;
    };
    readonly fill: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly fillColor: {
        readonly type: StringConstructor;
    };
    readonly fillOpacity: {
        readonly type: NumberConstructor;
    };
    readonly fillRule: {
        readonly type: StringConstructor;
    };
    readonly className: {
        readonly type: StringConstructor;
    };
    readonly interactive: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly bubblingMouseEvents: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
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
    leafletObject: import("vue").Ref<L.Rectangle<any> | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly latLngs: {
        readonly required: false;
        readonly type: import("vue").PropType<L.LatLngExpression[]>;
        readonly custom: true;
    };
    readonly bounds: {
        readonly type: import("vue").PropType<L.LatLngExpression[]>;
        readonly custom: true;
    };
    readonly smoothFactor: {
        readonly type: NumberConstructor;
    };
    readonly noClip: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly stroke: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly color: {
        readonly type: StringConstructor;
    };
    readonly weight: {
        readonly type: NumberConstructor;
    };
    readonly opacity: {
        readonly type: NumberConstructor;
    };
    readonly lineCap: {
        readonly type: StringConstructor;
    };
    readonly lineJoin: {
        readonly type: StringConstructor;
    };
    readonly dashArray: {
        readonly type: StringConstructor;
    };
    readonly dashOffset: {
        readonly type: StringConstructor;
    };
    readonly fill: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly fillColor: {
        readonly type: StringConstructor;
    };
    readonly fillOpacity: {
        readonly type: NumberConstructor;
    };
    readonly fillRule: {
        readonly type: StringConstructor;
    };
    readonly className: {
        readonly type: StringConstructor;
    };
    readonly interactive: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly bubblingMouseEvents: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
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
    readonly fill: boolean;
    readonly stroke: boolean;
    readonly interactive: boolean;
    readonly bubblingMouseEvents: boolean;
    readonly visible: boolean;
    readonly options: Record<string, any>;
    readonly noClip: boolean;
}>;
export default _sfc_main;
