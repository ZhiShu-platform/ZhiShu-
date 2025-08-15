import type L from "leaflet";
import { type PropType } from "vue";
export declare const controlProps: {
    readonly position: {
        readonly type: PropType<L.ControlPosition>;
    };
    readonly options: {
        readonly type: ObjectConstructor;
        readonly default: () => {};
        readonly custom: true;
    };
};
export declare const setupControl: (props: any, leafletRef: any) => {
    options: L.ControlOptions;
    methods: {
        setPosition(position: any): void;
    };
};
export declare const renderLControl: (slots: any) => import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
    [key: string]: any;
}> | null;
