import type L from "leaflet";
import type { PropType } from "vue";
export declare const iconProps: {
    readonly iconUrl: {
        readonly type: StringConstructor;
    };
    readonly iconRetinaUrl: {
        readonly type: StringConstructor;
    };
    readonly iconSize: {
        readonly type: PropType<L.PointExpression>;
    };
    readonly iconAnchor: {
        readonly type: PropType<L.PointExpression>;
    };
    readonly popupAnchor: {
        readonly type: PropType<L.PointExpression>;
    };
    readonly tooltipAnchor: {
        readonly type: PropType<L.PointExpression>;
    };
    readonly shadowUrl: {
        readonly type: StringConstructor;
    };
    readonly shadowRetinaUrl: {
        readonly type: StringConstructor;
    };
    readonly shadowSize: {
        readonly type: PropType<L.PointExpression>;
    };
    readonly shadowAnchor: {
        readonly type: PropType<L.PointExpression>;
    };
    readonly bgPos: {
        readonly type: PropType<L.PointExpression>;
    };
    readonly className: {
        readonly type: StringConstructor;
    };
};
