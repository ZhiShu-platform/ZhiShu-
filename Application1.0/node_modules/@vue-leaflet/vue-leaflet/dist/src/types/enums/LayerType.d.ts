import type { ObjectValues } from "../utilityTypes";
declare const LAYER_TYPE: {
    readonly BASE: "base";
    readonly OVERLAY: "overlay";
};
export type LayerType = ObjectValues<typeof LAYER_TYPE>;
export {};
