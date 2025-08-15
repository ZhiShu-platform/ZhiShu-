import type L from "leaflet";
import { type InjectionKey } from "vue";
export declare type Data = Record<string, unknown>;
export declare type ListenersAndAttrs = {
    listeners: L.LeafletEventHandlerFnMap;
    attrs: Data;
};
export declare const bindEventHandlers: (leafletObject: L.Evented, eventHandlers: L.LeafletEventHandlerFnMap) => void;
export declare const cancelDebounces: (handlerMethods: {
    [key: string]: any;
}) => void;
export declare const capitalizeFirstLetter: (s: string) => string;
export declare const isFunction: (x: any) => boolean;
export declare const propsBinder: (methods: any, leafletElement: any, props: any) => void;
export declare const propsToLeafletOptions: <T>(propValues: any, propDefinitions: any, baseOptions?: {}) => T;
export declare const remapEvents: (contextAttrs: Data) => ListenersAndAttrs;
export declare const resetWebpackIcon: (Icon: any) => Promise<void>;
/**
 * Wrap a placeholder function and provide it with the given name.
 * The wrapper can later be updated with {@link updateLeafletWrapper}
 * to provide a different function.
 *
 * @param {String} methodName Key used to provide the wrapper function
 */
export declare const provideLeafletWrapper: (methodName: any) => {
    (...args: any[]): void;
    wrapped: import("vue").Ref<(..._args: any[]) => void>;
};
/**
 * Change the function that will be executed when an injected Leaflet wrapper
 * is invoked.
 *
 * @param {*} wrapper Provided wrapper whose wrapped function is to be updated
 * @param {function} leafletMethod New method to be wrapped by the wrapper
 */
export declare const updateLeafletWrapper: (wrapper: any, leafletMethod: any) => any;
export declare const WINDOW_OR_GLOBAL: typeof globalThis;
export declare const assertInject: <T>(key: InjectionKey<T>) => T & ({} | null);
