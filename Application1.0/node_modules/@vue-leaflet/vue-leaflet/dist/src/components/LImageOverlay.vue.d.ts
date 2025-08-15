import type L from "leaflet";
/**
 * ImageOverlay component, render a plain image instead of a geospatial map.
 */
declare const _sfc_main: import("vue").DefineComponent<{
    readonly opacity: {
        readonly type: NumberConstructor;
    };
    readonly alt: {
        readonly type: StringConstructor;
    };
    readonly interactive: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly crossOrigin: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly errorOverlayUrl: {
        readonly type: StringConstructor;
    };
    readonly zIndex: {
        readonly type: NumberConstructor;
    };
    readonly className: {
        readonly type: StringConstructor;
    };
    readonly url: {
        readonly type: StringConstructor;
        readonly required: true;
        readonly custom: true;
    };
    readonly bounds: {
        readonly type: import("vue").PropType<L.LatLngBoundsExpression>;
        readonly required: true;
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
    leafletObject: import("vue").Ref<L.ImageOverlay | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly opacity: {
        readonly type: NumberConstructor;
    };
    readonly alt: {
        readonly type: StringConstructor;
    };
    readonly interactive: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly crossOrigin: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    readonly errorOverlayUrl: {
        readonly type: StringConstructor;
    };
    readonly zIndex: {
        readonly type: NumberConstructor;
    };
    readonly className: {
        readonly type: StringConstructor;
    };
    readonly url: {
        readonly type: StringConstructor;
        readonly required: true;
        readonly custom: true;
    };
    readonly bounds: {
        readonly type: import("vue").PropType<L.LatLngBoundsExpression>;
        readonly required: true;
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
    readonly interactive: boolean;
    readonly visible: boolean;
    readonly options: Record<string, any>;
    readonly crossOrigin: boolean;
}>;
export default _sfc_main;
