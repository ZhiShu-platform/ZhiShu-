import type L from "leaflet";
import { type PropType } from "vue";
import { type VueGridLayerTileRenderer } from '../functions/gridLayer';
declare const _sfc_main: import("vue").DefineComponent<{
    childRender: {
        type: PropType<VueGridLayerTileRenderer>;
        required: true;
    };
    opacity: {
        readonly type: NumberConstructor;
    };
    zIndex: {
        readonly type: NumberConstructor;
    };
    tileSize: {
        readonly type: PropType<Number | L.PointExpression>;
    };
    noWrap: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    minZoom: {
        readonly type: NumberConstructor;
    };
    maxZoom: {
        readonly type: NumberConstructor;
    };
    className: {
        readonly type: StringConstructor;
    };
    pane: {
        readonly type: StringConstructor;
    };
    attribution: {
        readonly type: StringConstructor;
    };
    name: {
        readonly type: StringConstructor;
        readonly custom: true;
    };
    layerType: {
        readonly type: PropType<import("../types/enums/LayerType").LayerType>;
        readonly custom: true;
    };
    visible: {
        readonly type: BooleanConstructor;
        readonly custom: true;
        readonly default: true;
    };
    options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
}, {
    root: import("vue").Ref<null>;
    ready: import("vue").Ref<boolean>;
    leafletObject: import("vue").Ref<L.GridLayer | undefined>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    childRender: {
        type: PropType<VueGridLayerTileRenderer>;
        required: true;
    };
    opacity: {
        readonly type: NumberConstructor;
    };
    zIndex: {
        readonly type: NumberConstructor;
    };
    tileSize: {
        readonly type: PropType<Number | L.PointExpression>;
    };
    noWrap: {
        readonly type: BooleanConstructor;
        readonly default: undefined;
    };
    minZoom: {
        readonly type: NumberConstructor;
    };
    maxZoom: {
        readonly type: NumberConstructor;
    };
    className: {
        readonly type: StringConstructor;
    };
    pane: {
        readonly type: StringConstructor;
    };
    attribution: {
        readonly type: StringConstructor;
    };
    name: {
        readonly type: StringConstructor;
        readonly custom: true;
    };
    layerType: {
        readonly type: PropType<import("../types/enums/LayerType").LayerType>;
        readonly custom: true;
    };
    visible: {
        readonly type: BooleanConstructor;
        readonly custom: true;
        readonly default: true;
    };
    options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
}>>, {
    visible: boolean;
    options: Record<string, any>;
    noWrap: boolean;
}>;
export default _sfc_main;
