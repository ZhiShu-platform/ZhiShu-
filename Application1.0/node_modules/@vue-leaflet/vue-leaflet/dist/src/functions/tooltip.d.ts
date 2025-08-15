export declare const tooltipProps: {
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
export declare const setupTooltip: (props: any, leafletRef: any) => {
    options: any;
    methods: {
        setContent(newVal: any): void;
    };
};
