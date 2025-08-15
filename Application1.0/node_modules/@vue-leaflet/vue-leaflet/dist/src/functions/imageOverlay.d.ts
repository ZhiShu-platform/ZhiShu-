import type L from "leaflet";
import type { PropType } from "vue";
/**
 * @typedef {import('leaflet/dist/leaflet-src.esm.js').LatLngBounds} LatLngBounds
 */
export declare const imageOverlayProps: {
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
        readonly type: PropType<L.LatLngBoundsExpression>;
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
export declare const setupImageOverlay: (props: any, leafletRef: any, context: any) => {
    options: L.ImageOverlayOptions;
    methods: {
        /**
         * Sets the opacity of the overlay.
         * @param {number} opacity
         */
        setOpacity(opacity: any): any;
        /**
         * Changes the URL of the image.
         * @param {string} url
         */
        setUrl(url: any): any;
        /**
         * Update the bounds that this ImageOverlay covers
         * @param {LatLngBounds | Array<Array<number>>} bounds
         */
        setBounds(bounds: any): any;
        /**
         * Get the bounds that this ImageOverlay covers
         * @returns {LatLngBounds}
         */
        getBounds(): any;
        /**
         * Returns the instance of HTMLImageElement used by this overlay.
         * @returns {HTMLElement}
         */
        getElement(): any;
        /**
         * Brings the layer to the top of all overlays.
         */
        bringToFront(): any;
        /**
         * Brings the layer to the bottom of all overlays.
         */
        bringToBack(): any;
        /**
         * Changes the zIndex of the image overlay.
         * @param {number} zIndex
         */
        setZIndex(zIndex: any): any;
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
