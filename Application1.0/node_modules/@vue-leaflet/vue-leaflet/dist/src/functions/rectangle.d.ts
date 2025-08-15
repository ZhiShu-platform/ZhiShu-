import type L from "leaflet";
import type { PropType } from "vue";
export declare const rectangleProps: {
    readonly latLngs: {
        readonly required: false;
        readonly type: PropType<L.LatLngExpression[]>;
        readonly custom: true;
    };
    readonly bounds: {
        readonly type: PropType<L.LatLngExpression[]>;
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
        readonly type: PropType<import("../types/enums/LayerType").LayerType>;
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
};
export declare const setupRectangle: (props: any, leafletRef: any, context: any) => {
    options: L.PolylineOptions;
    methods: {
        setBounds(latLngBounds: any): void;
        setLatLngs(latLngs: any): void;
        toGeoJSON(precision: any): any;
        setSmoothFactor(smoothFactor: any): void;
        setNoClip(noClip: any): void;
        addLatLng(latLng: any): void;
        setStroke(stroke: any): void;
        setColor(color: any): void;
        setWeight(weight: any): void;
        setOpacity(opacity: any): void;
        setLineCap(lineCap: any): void;
        setLineJoin(lineJoin: any): void;
        setDashArray(dashArray: any): void;
        setDashOffset(dashOffset: any): void;
        setFill(fill: any): void;
        setFillColor(fillColor: any): void;
        setFillOpacity(fillOpacity: any): void;
        setFillRule(fillRule: any): void;
        setClassName(className: any): void;
        setAttribution(val: any): void;
        setName(): void;
        setLayerType(): void;
        setVisible(isVisible: any): void;
        bindPopup(leafletObject: any): void;
        bindTooltip(leafletObject: any): void;
        unbindTooltip(): void;
        unbindPopup(): void;
        updateVisibleProp(value: any): void;
    };
};
