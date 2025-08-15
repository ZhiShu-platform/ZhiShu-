import type L from "leaflet";
import type { PropType } from "vue";
export declare const popupProps: {
    readonly latLng: {
        readonly type: PropType<L.LatLngExpression>;
        readonly default: () => never[];
    };
    readonly content: {
        readonly type: StringConstructor;
        readonly default: null;
    };
    readonly options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
};
export declare const setupPopup: (props: any, leafletRef: any) => {
    options: any;
    methods: {
        setContent(newVal: any): void;
    };
};
