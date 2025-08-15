import { watch as He, ref as c, provide as A, inject as O, onUnmounted as pe, h as U, onBeforeUnmount as R, defineComponent as S, onMounted as _, markRaw as j, nextTick as g, render as mt, reactive as vt, computed as oe } from "vue";
const ce = (e, o) => {
  for (const t of Object.keys(o))
    e.on(t, o[t]);
}, ye = (e) => {
  for (const o of Object.keys(e)) {
    const t = e[o];
    t && k(t.cancel) && t.cancel();
  }
}, Je = (e) => !e || typeof e.charAt != "function" ? e : e.charAt(0).toUpperCase() + e.slice(1), k = (e) => typeof e == "function", L = (e, o, t) => {
  for (const n in t) {
    const s = "set" + Je(n);
    e[s] ? He(
      () => t[n],
      (r, l) => {
        e[s](r, l);
      }
    ) : o[s] && He(
      () => t[n],
      (r) => {
        o[s](r);
      }
    );
  }
}, f = (e, o, t = {}) => {
  const n = { ...t };
  for (const s in e) {
    const r = o[s], l = e[s];
    r && (r && r.custom === !0 || l !== void 0 && (n[s] = l));
  }
  return n;
}, T = (e) => {
  const o = {}, t = {};
  for (const n in e)
    if (n.startsWith("on") && !n.startsWith("onUpdate") && n !== "onReady") {
      const s = n.slice(2).toLocaleLowerCase();
      o[s] = e[n];
    } else
      t[n] = e[n];
  return { listeners: o, attrs: t };
}, qe = async (e) => {
  const o = await Promise.all([
    import("leaflet/dist/images/marker-icon-2x.png"),
    import("leaflet/dist/images/marker-icon.png"),
    import("leaflet/dist/images/marker-shadow.png")
  ]);
  delete e.Default.prototype._getIconUrl, e.Default.mergeOptions({
    iconRetinaUrl: o[0].default,
    iconUrl: o[1].default,
    shadowUrl: o[2].default
  });
}, Y = (e) => {
  const o = c(
    (...n) => console.warn(`Method ${e} has been invoked without being replaced`)
  ), t = (...n) => o.value(...n);
  return t.wrapped = o, A(e, t), t;
}, V = (e, o) => e.wrapped.value = o, b = typeof self == "object" && self.self === self && self || typeof global == "object" && global.global === global && global || globalThis, m = (e) => {
  const o = O(e);
  if (o === void 0)
    throw new Error(
      `Attempt to inject ${e.description} before it was provided.`
    );
  return o;
}, Kt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  WINDOW_OR_GLOBAL: b,
  assertInject: m,
  bindEventHandlers: ce,
  cancelDebounces: ye,
  capitalizeFirstLetter: Je,
  isFunction: k,
  propsBinder: L,
  propsToLeafletOptions: f,
  provideLeafletWrapper: Y,
  remapEvents: T,
  resetWebpackIcon: qe,
  updateLeafletWrapper: V
}, Symbol.toStringTag, { value: "Module" })), h = Symbol(
  "useGlobalLeaflet"
), M = Symbol("addLayer"), ee = Symbol("removeLayer"), H = Symbol(
  "registerControl"
), me = Symbol(
  "registerLayerControl"
), ve = Symbol(
  "canSetParentHtml"
), be = Symbol("setParentHtml"), fe = Symbol("setIcon"), ge = Symbol("bindPopup"), Le = Symbol("bindTooltip"), he = Symbol("unbindPopup"), Oe = Symbol("unbindTooltip"), Qt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  AddLayerInjection: M,
  BindPopupInjection: ge,
  BindTooltipInjection: Le,
  CanSetParentHtmlInjection: ve,
  RegisterControlInjection: H,
  RegisterLayerControlInjection: me,
  RemoveLayerInjection: ee,
  SetIconInjection: fe,
  SetParentHtmlInjection: be,
  UnbindPopupInjection: he,
  UnbindTooltipInjection: Oe,
  UseGlobalLeafletInjection: h
}, Symbol.toStringTag, { value: "Module" })), W = {
  options: {
    type: Object,
    default: () => ({}),
    custom: !0
  }
}, J = (e) => ({ options: e.options, methods: {} }), bt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  componentProps: W,
  setupComponent: J
}, Symbol.toStringTag, { value: "Module" })), D = {
  ...W,
  pane: {
    type: String
  },
  attribution: {
    type: String
  },
  name: {
    type: String,
    custom: !0
  },
  layerType: {
    type: String,
    custom: !0
  },
  visible: {
    type: Boolean,
    custom: !0,
    default: !0
  }
}, q = (e, o, t) => {
  const n = m(M), s = m(ee), { options: r, methods: l } = J(e), a = f(
    e,
    D,
    r
  ), i = () => n({ leafletObject: o.value }), u = () => s({ leafletObject: o.value }), d = {
    ...l,
    setAttribution(y) {
      u(), o.value.options.attribution = y, e.visible && i();
    },
    setName() {
      u(), e.visible && i();
    },
    setLayerType() {
      u(), e.visible && i();
    },
    setVisible(y) {
      o.value && (y ? i() : u());
    },
    bindPopup(y) {
      if (!o.value || !k(o.value.bindPopup)) {
        console.warn(
          "Attempt to bind popup before bindPopup method available on layer."
        );
        return;
      }
      o.value.bindPopup(y);
    },
    bindTooltip(y) {
      if (!o.value || !k(o.value.bindTooltip)) {
        console.warn(
          "Attempt to bind tooltip before bindTooltip method available on layer."
        );
        return;
      }
      o.value.bindTooltip(y);
    },
    unbindTooltip() {
      o.value && (k(o.value.closeTooltip) && o.value.closeTooltip(), k(o.value.unbindTooltip) && o.value.unbindTooltip());
    },
    unbindPopup() {
      o.value && (k(o.value.closePopup) && o.value.closePopup(), k(o.value.unbindPopup) && o.value.unbindPopup());
    },
    updateVisibleProp(y) {
      t.emit("update:visible", y);
    }
  };
  return A(ge, d.bindPopup), A(Le, d.bindTooltip), A(he, d.unbindPopup), A(Oe, d.unbindTooltip), pe(() => {
    d.unbindPopup(), d.unbindTooltip(), u();
  }), { options: a, methods: d };
}, G = (e, o) => {
  if (e && o.default)
    return U("div", { style: { display: "none" } }, o.default());
}, ft = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  layerProps: D,
  render: G,
  setupLayer: q
}, Symbol.toStringTag, { value: "Module" })), Se = {
  ...D,
  interactive: {
    type: Boolean,
    default: void 0
  },
  bubblingMouseEvents: {
    type: Boolean,
    default: void 0
  }
}, Ke = (e, o, t) => {
  const { options: n, methods: s } = q(
    e,
    o,
    t
  );
  return { options: f(
    e,
    Se,
    n
  ), methods: s };
}, gt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  interactiveLayerProps: Se,
  setupInteractiveLayer: Ke
}, Symbol.toStringTag, { value: "Module" })), ne = {
  ...Se,
  stroke: {
    type: Boolean,
    default: void 0
  },
  color: {
    type: String
  },
  weight: {
    type: Number
  },
  opacity: {
    type: Number
  },
  lineCap: {
    type: String
  },
  lineJoin: {
    type: String
  },
  dashArray: {
    type: String
  },
  dashOffset: {
    type: String
  },
  fill: {
    type: Boolean,
    default: void 0
  },
  fillColor: {
    type: String
  },
  fillOpacity: {
    type: Number
  },
  fillRule: {
    type: String
  },
  className: {
    type: String
  }
}, _e = (e, o, t) => {
  const { options: n, methods: s } = Ke(e, o, t), r = f(
    e,
    ne,
    n
  ), l = m(ee), a = {
    ...s,
    setStroke(i) {
      o.value.setStyle({ stroke: i });
    },
    setColor(i) {
      o.value.setStyle({ color: i });
    },
    setWeight(i) {
      o.value.setStyle({ weight: i });
    },
    setOpacity(i) {
      o.value.setStyle({ opacity: i });
    },
    setLineCap(i) {
      o.value.setStyle({ lineCap: i });
    },
    setLineJoin(i) {
      o.value.setStyle({ lineJoin: i });
    },
    setDashArray(i) {
      o.value.setStyle({ dashArray: i });
    },
    setDashOffset(i) {
      o.value.setStyle({ dashOffset: i });
    },
    setFill(i) {
      o.value.setStyle({ fill: i });
    },
    setFillColor(i) {
      o.value.setStyle({ fillColor: i });
    },
    setFillOpacity(i) {
      o.value.setStyle({ fillOpacity: i });
    },
    setFillRule(i) {
      o.value.setStyle({ fillRule: i });
    },
    setClassName(i) {
      o.value.setStyle({ className: i });
    }
  };
  return R(() => {
    l({ leafletObject: o.value });
  }), { options: r, methods: a };
}, Lt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  pathProps: ne,
  setupPath: _e
}, Symbol.toStringTag, { value: "Module" })), re = {
  ...ne,
  /**
   * Radius of the marker in pixels.
   */
  radius: {
    type: Number
  },
  latLng: {
    type: [Object, Array],
    required: !0,
    custom: !0
  }
}, je = (e, o, t) => {
  const { options: n, methods: s } = _e(
    e,
    o,
    t
  ), r = f(
    e,
    re,
    n
  ), l = {
    ...s,
    setRadius(a) {
      o.value.setRadius(a);
    },
    setLatLng(a) {
      o.value.setLatLng(a);
    }
  };
  return { options: r, methods: l };
}, ht = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  circleMarkerProps: re,
  setupCircleMarker: je
}, Symbol.toStringTag, { value: "Module" })), Pe = {
  ...re,
  /**
   * Radius of the circle in meters.
   */
  radius: {
    type: Number
  }
}, Qe = (e, o, t) => {
  const { options: n, methods: s } = je(e, o, t), r = f(
    e,
    Pe,
    n
  ), l = {
    ...s
  };
  return { options: r, methods: l };
}, Ot = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  circleProps: Pe,
  setupCircle: Qe
}, Symbol.toStringTag, { value: "Module" })), Xt = S({
  name: "LCircle",
  props: Pe,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { options: l, methods: a } = Qe(e, t, o);
    return _(async () => {
      const { circle: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(i(e.latLng, l));
      const { listeners: u } = T(o.attrs);
      t.value.on(u), L(a, t.value, e), r({
        ...e,
        ...a,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), Yt = S({
  name: "LCircleMarker",
  props: re,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { options: l, methods: a } = je(
      e,
      t,
      o
    );
    return _(async () => {
      const { circleMarker: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        i(e.latLng, l)
      );
      const { listeners: u } = T(o.attrs);
      t.value.on(u), L(a, t.value, e), r({
        ...e,
        ...a,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), F = {
  ...W,
  position: {
    type: String
  }
}, K = (e, o) => {
  const { options: t, methods: n } = J(e), s = f(
    e,
    F,
    t
  ), r = {
    ...n,
    setPosition(l) {
      o.value && o.value.setPosition(l);
    }
  };
  return pe(() => {
    o.value && o.value.remove();
  }), { options: s, methods: r };
}, Xe = (e) => e.default ? U("div", { ref: "root" }, e.default()) : null, St = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  controlProps: F,
  renderLControl: Xe,
  setupControl: K
}, Symbol.toStringTag, { value: "Module" })), Vt = S({
  name: "LControl",
  props: {
    ...F,
    disableClickPropagation: {
      type: Boolean,
      custom: !0,
      default: !0
    },
    disableScrollPropagation: {
      type: Boolean,
      custom: !0,
      default: !1
    }
  },
  setup(e, o) {
    const t = c(), n = c(), s = O(h), r = m(H), { options: l, methods: a } = K(e, t);
    return _(async () => {
      const { Control: i, DomEvent: u } = s ? b.L : await import("leaflet/dist/leaflet-src.esm"), d = i.extend({
        onAdd() {
          return n.value;
        }
      });
      t.value = j(new d(l)), L(a, t.value, e), r({ leafletObject: t.value }), e.disableClickPropagation && n.value && u.disableClickPropagation(n.value), e.disableScrollPropagation && n.value && u.disableScrollPropagation(n.value), g(() => o.emit("ready", t.value));
    }), { root: n, leafletObject: t };
  },
  render() {
    return Xe(this.$slots);
  }
}), Ce = {
  ...F,
  prefix: {
    type: String
  }
}, Ye = (e, o) => {
  const { options: t, methods: n } = K(
    e,
    o
  ), s = f(
    e,
    Ce,
    t
  ), r = {
    ...n,
    setPrefix(l) {
      o.value.setPrefix(l);
    }
  };
  return { options: s, methods: r };
}, _t = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  controlAttributionProps: Ce,
  setupControlAttribution: Ye
}, Symbol.toStringTag, { value: "Module" })), xt = S({
  name: "LControlAttribution",
  props: Ce,
  setup(e, o) {
    const t = c(), n = O(h), s = m(H), { options: r, methods: l } = Ye(e, t);
    return _(async () => {
      const { control: a } = n ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        a.attribution(r)
      ), L(l, t.value, e), s({ leafletObject: t.value }), g(() => o.emit("ready", t.value));
    }), { leafletObject: t };
  },
  render() {
    return null;
  }
}), Te = {
  ...F,
  collapsed: {
    type: Boolean,
    default: void 0
  },
  autoZIndex: {
    type: Boolean,
    default: void 0
  },
  hideSingleBase: {
    type: Boolean,
    default: void 0
  },
  sortLayers: {
    type: Boolean,
    default: void 0
  },
  sortFunction: {
    type: Function
  }
}, Ve = (e, o) => {
  const { options: t } = K(e, o);
  return { options: f(
    e,
    Te,
    t
  ), methods: {
    addLayer(r) {
      r.layerType === "base" ? o.value.addBaseLayer(r.leafletObject, r.name) : r.layerType === "overlay" && o.value.addOverlay(r.leafletObject, r.name);
    },
    removeLayer(r) {
      o.value.removeLayer(r.leafletObject);
    }
  } };
}, jt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  controlLayersProps: Te,
  setupControlLayers: Ve
}, Symbol.toStringTag, { value: "Module" })), Rt = S({
  name: "LControlLayers",
  props: Te,
  setup(e, o) {
    const t = c(), n = O(h), s = m(me), { options: r, methods: l } = Ve(e, t);
    return _(async () => {
      const { control: a } = n ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        a.layers(void 0, void 0, r)
      ), L(l, t.value, e), s({
        ...e,
        ...l,
        leafletObject: t.value
      }), g(() => o.emit("ready", t.value));
    }), { leafletObject: t };
  },
  render() {
    return null;
  }
}), Me = {
  ...F,
  maxWidth: {
    type: Number
  },
  metric: {
    type: Boolean,
    default: void 0
  },
  imperial: {
    type: Boolean,
    default: void 0
  },
  updateWhenIdle: {
    type: Boolean,
    default: void 0
  }
}, xe = (e, o) => {
  const { options: t, methods: n } = K(
    e,
    o
  );
  return { options: f(
    e,
    Me,
    t
  ), methods: n };
}, Pt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  controlScaleProps: Me,
  setupControlScale: xe
}, Symbol.toStringTag, { value: "Module" })), eo = S({
  name: "LControlScale",
  props: Me,
  setup(e, o) {
    const t = c(), n = O(h), s = m(H), { options: r, methods: l } = xe(e, t);
    return _(async () => {
      const { control: a } = n ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(a.scale(r)), L(l, t.value, e), s({ leafletObject: t.value }), g(() => o.emit("ready", t.value));
    }), { leafletObject: t };
  },
  render() {
    return null;
  }
}), Be = {
  ...F,
  zoomInText: {
    type: String
  },
  zoomInTitle: {
    type: String
  },
  zoomOutText: {
    type: String
  },
  zoomOutTitle: {
    type: String
  }
}, Re = (e, o) => {
  const { options: t, methods: n } = K(
    e,
    o
  );
  return { options: f(
    e,
    Be,
    t
  ), methods: n };
}, Ct = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  controlZoomProps: Be,
  setupControlZoom: Re
}, Symbol.toStringTag, { value: "Module" })), to = S({
  name: "LControlZoom",
  props: Be,
  setup(e, o) {
    const t = c(), n = O(h), s = m(H), { options: r, methods: l } = Re(e, t);
    return _(async () => {
      const { control: a } = n ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(a.zoom(r)), L(l, t.value, e), s({ leafletObject: t.value }), g(() => o.emit("ready", t.value));
    }), { leafletObject: t };
  },
  render() {
    return null;
  }
}), te = {
  ...D
}, se = (e, o, t) => {
  const { options: n, methods: s } = q(
    e,
    o,
    t
  ), r = f(
    e,
    te,
    n
  ), l = {
    ...s,
    addLayer(a) {
      o.value.addLayer(a.leafletObject);
    },
    removeLayer(a) {
      o.value.removeLayer(a.leafletObject);
    }
  };
  return A(M, l.addLayer), A(ee, l.removeLayer), { options: r, methods: l };
}, Tt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  layerGroupProps: te,
  setupLayerGroup: se
}, Symbol.toStringTag, { value: "Module" })), we = {
  ...te
}, et = (e, o, t) => {
  const { options: n, methods: s } = se(
    e,
    o,
    t
  ), r = f(
    e,
    we,
    n
  ), l = {
    ...s
  };
  return { options: r, methods: l };
}, Mt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  featureGroupProps: we,
  setupFeatureGroup: et
}, Symbol.toStringTag, { value: "Module" })), oo = S({
  props: we,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { methods: l, options: a } = et(
      e,
      t,
      o
    );
    return _(async () => {
      const { featureGroup: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        i(void 0, a)
      );
      const { listeners: u } = T(o.attrs);
      t.value.on(u), L(l, t.value, e), r({
        ...e,
        ...l,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), Ie = {
  ...te,
  geojson: {
    type: [Object, Array],
    custom: !0
  },
  optionsStyle: {
    type: Function,
    custom: !0
  }
}, tt = (e, o, t) => {
  const { options: n, methods: s } = se(
    e,
    o,
    t
  ), r = f(
    e,
    Ie,
    n
  );
  Object.prototype.hasOwnProperty.call(e, "optionsStyle") && (r.style = e.optionsStyle);
  const l = {
    ...s,
    setGeojson(a) {
      o.value.clearLayers(), o.value.addData(a);
    },
    setOptionsStyle(a) {
      o.value.setStyle(a);
    },
    getGeoJSONData() {
      return o.value.toGeoJSON();
    },
    getBounds() {
      return o.value.getBounds();
    }
  };
  return { options: r, methods: l };
}, Bt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  geoJSONProps: Ie,
  setupGeoJSON: tt
}, Symbol.toStringTag, { value: "Module" })), no = S({
  props: Ie,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { methods: l, options: a } = tt(e, t, o);
    return _(async () => {
      const { geoJSON: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(i(e.geojson, a));
      const { listeners: u } = T(o.attrs);
      t.value.on(u), L(l, t.value, e), r({
        ...e,
        ...l,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), ae = {
  ...D,
  opacity: {
    type: Number
  },
  zIndex: {
    type: Number
  },
  tileSize: {
    type: [Number, Array, Object]
  },
  noWrap: {
    type: Boolean,
    default: void 0
  },
  minZoom: {
    type: Number
  },
  maxZoom: {
    type: Number
  },
  className: {
    type: String
  }
}, Ae = (e, o, t) => {
  const { options: n, methods: s } = q(
    e,
    o,
    t
  ), r = f(
    e,
    ae,
    n
  ), l = {
    ...s,
    setTileComponent() {
      var a;
      (a = o.value) == null || a.redraw();
    }
  };
  return pe(() => {
    o.value.off();
  }), { options: r, methods: l };
}, ot = (e, o, t, n) => e.extend({
  initialize(s) {
    this.tileComponents = {}, this.on("tileunload", this._unloadTile), t.setOptions(this, s);
  },
  createTile(s) {
    const r = this._tileCoordsToKey(s);
    this.tileComponents[r] = o.create("div");
    const l = U({ setup: n, props: ["coords"] }, { coords: s });
    return mt(l, this.tileComponents[r]), this.tileComponents[r];
  },
  _unloadTile(s) {
    const r = this._tileCoordsToKey(s.coords);
    this.tileComponents[r] && (this.tileComponents[r].innerHTML = "", this.tileComponents[r] = void 0);
  }
}), wt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  CreateVueGridLayer: ot,
  gridLayerProps: ae,
  setupGridLayer: Ae
}, Symbol.toStringTag, { value: "Module" })), ro = S({
  props: {
    ...ae,
    childRender: {
      type: Function,
      required: !0
    }
  },
  setup(e, o) {
    const t = c(), n = c(null), s = c(!1), r = O(h), l = m(M), { options: a, methods: i } = Ae(e, t, o);
    return _(async () => {
      const { GridLayer: u, DomUtil: d, Util: y } = r ? b.L : await import("leaflet/dist/leaflet-src.esm"), w = ot(
        u,
        d,
        y,
        e.childRender
      );
      t.value = j(new w(a));
      const { listeners: v } = T(o.attrs);
      t.value.on(v), L(i, t.value, e), l({
        ...e,
        ...i,
        leafletObject: t.value
      }), s.value = !0, g(() => o.emit("ready", t.value));
    }), { root: n, ready: s, leafletObject: t };
  },
  render() {
    return this.ready ? U("div", { style: { display: "none" }, ref: "root" }) : null;
  }
}), de = {
  iconUrl: {
    type: String
  },
  iconRetinaUrl: {
    type: String
  },
  iconSize: {
    type: [Object, Array]
  },
  iconAnchor: {
    type: [Object, Array]
  },
  popupAnchor: {
    type: [Object, Array]
  },
  tooltipAnchor: {
    type: [Object, Array]
  },
  shadowUrl: {
    type: String
  },
  shadowRetinaUrl: {
    type: String
  },
  shadowSize: {
    type: [Object, Array]
  },
  shadowAnchor: {
    type: [Object, Array]
  },
  bgPos: {
    type: [Object, Array]
  },
  className: {
    type: String
  }
}, It = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  iconProps: de
}, Symbol.toStringTag, { value: "Module" })), so = S({
  name: "LIcon",
  props: {
    ...de,
    ...W
  },
  setup(e, o) {
    const t = c(), n = O(h), s = m(ve), r = m(be), l = m(fe);
    let a, i, u, d, y;
    const w = (N, P, B) => {
      const I = N && N.innerHTML;
      if (!P) {
        B && y && s() && r(I);
        return;
      }
      const { listeners: E } = T(o.attrs);
      y && i(y, E);
      const { options: ue } = J(e), $ = f(
        e,
        de,
        ue
      );
      I && ($.html = I), y = $.html ? u($) : d($), a(y, E), l(y);
    }, v = () => {
      g(() => w(t.value, !0, !1));
    }, z = () => {
      g(() => w(t.value, !1, !0));
    }, Z = {
      setIconUrl: v,
      setIconRetinaUrl: v,
      setIconSize: v,
      setIconAnchor: v,
      setPopupAnchor: v,
      setTooltipAnchor: v,
      setShadowUrl: v,
      setShadowRetinaUrl: v,
      setShadowAnchor: v,
      setBgPos: v,
      setClassName: v,
      setHtml: v
    };
    return _(async () => {
      const {
        DomEvent: N,
        divIcon: P,
        icon: B
      } = n ? b.L : await import("leaflet/dist/leaflet-src.esm");
      a = N.on, i = N.off, u = P, d = B, L(Z, {}, e), new MutationObserver(z).observe(t.value, {
        attributes: !0,
        childList: !0,
        characterData: !0,
        subtree: !0
      }), v();
    }), { root: t };
  },
  render() {
    const e = this.$slots.default ? this.$slots.default() : void 0;
    return U("div", { ref: "root" }, e);
  }
}), Ge = {
  ...D,
  opacity: {
    type: Number
  },
  alt: {
    type: String
  },
  interactive: {
    type: Boolean,
    default: void 0
  },
  crossOrigin: {
    type: Boolean,
    default: void 0
  },
  errorOverlayUrl: {
    type: String
  },
  zIndex: {
    type: Number
  },
  className: {
    type: String
  },
  url: {
    type: String,
    required: !0,
    custom: !0
  },
  bounds: {
    type: [Array, Object],
    required: !0,
    custom: !0
  }
}, nt = (e, o, t) => {
  const { options: n, methods: s } = q(
    e,
    o,
    t
  ), r = f(
    e,
    Ge,
    n
  ), l = {
    ...s,
    /**
     * Sets the opacity of the overlay.
     * @param {number} opacity
     */
    setOpacity(a) {
      return o.value.setOpacity(a);
    },
    /**
     * Changes the URL of the image.
     * @param {string} url
     */
    setUrl(a) {
      return o.value.setUrl(a);
    },
    /**
     * Update the bounds that this ImageOverlay covers
     * @param {LatLngBounds | Array<Array<number>>} bounds
     */
    setBounds(a) {
      return o.value.setBounds(a);
    },
    /**
     * Get the bounds that this ImageOverlay covers
     * @returns {LatLngBounds}
     */
    getBounds() {
      return o.value.getBounds();
    },
    /**
     * Returns the instance of HTMLImageElement used by this overlay.
     * @returns {HTMLElement}
     */
    getElement() {
      return o.value.getElement();
    },
    /**
     * Brings the layer to the top of all overlays.
     */
    bringToFront() {
      return o.value.bringToFront();
    },
    /**
     * Brings the layer to the bottom of all overlays.
     */
    bringToBack() {
      return o.value.bringToBack();
    },
    /**
     * Changes the zIndex of the image overlay.
     * @param {number} zIndex
     */
    setZIndex(a) {
      return o.value.setZIndex(a);
    }
  };
  return { options: r, methods: l };
}, At = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  imageOverlayProps: Ge,
  setupImageOverlay: nt
}, Symbol.toStringTag, { value: "Module" })), ao = S({
  name: "LImageOverlay",
  props: Ge,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { options: l, methods: a } = nt(
      e,
      t,
      o
    );
    return _(async () => {
      const { imageOverlay: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        i(e.url, e.bounds, l)
      );
      const { listeners: u } = T(o.attrs);
      t.value.on(u), L(a, t.value, e), r({
        ...e,
        ...a,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), lo = S({
  props: te,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { methods: l } = se(e, t, o);
    return _(async () => {
      const { layerGroup: a } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        a(void 0, e.options)
      );
      const { listeners: i } = T(o.attrs);
      t.value.on(i), L(l, t.value, e), r({
        ...e,
        ...l,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
});
function rt(e, o, t) {
  var n, s, r;
  o === void 0 && (o = 50), t === void 0 && (t = {});
  var l = (n = t.isImmediate) != null && n, a = (s = t.callback) != null && s, i = t.maxWait, u = Date.now(), d = [];
  function y() {
    if (i !== void 0) {
      var v = Date.now() - u;
      if (v + o >= i)
        return i - v;
    }
    return o;
  }
  var w = function() {
    var v = [].slice.call(arguments), z = this;
    return new Promise(function(Z, N) {
      var P = l && r === void 0;
      if (r !== void 0 && clearTimeout(r), r = setTimeout(function() {
        if (r = void 0, u = Date.now(), !l) {
          var I = e.apply(z, v);
          a && a(I), d.forEach(function(E) {
            return (0, E.resolve)(I);
          }), d = [];
        }
      }, y()), P) {
        var B = e.apply(z, v);
        return a && a(B), Z(B);
      }
      d.push({ resolve: Z, reject: N });
    });
  };
  return w.cancel = function(v) {
    r !== void 0 && clearTimeout(r), d.forEach(function(z) {
      return (0, z.reject)(v);
    }), d = [];
  }, w;
}
const We = {
  ...W,
  /**
   * The center of the map, supports .sync modifier
   */
  center: {
    type: [Object, Array]
  },
  /**
   * The bounds of the map, supports .sync modifier
   */
  bounds: {
    type: [Array, Object]
  },
  /**
   * The max bounds of the map
   */
  maxBounds: {
    type: [Array, Object]
  },
  /**
   * The zoom of the map, supports .sync modifier
   */
  zoom: {
    type: Number
  },
  /**
   * The minZoom of the map
   */
  minZoom: {
    type: Number
  },
  /**
   * The maxZoom of the map
   */
  maxZoom: {
    type: Number
  },
  /**
   * The paddingBottomRight of the map
   */
  paddingBottomRight: {
    type: [Object, Array]
  },
  /**
   * The paddingTopLeft of the map
   */
  paddingTopLeft: {
    type: Object
  },
  /**
   * The padding of the map
   */
  padding: {
    type: Object
  },
  /**
   * The worldCopyJump option for the map
   */
  worldCopyJump: {
    type: Boolean,
    default: void 0
  },
  /**
   * The CRS to use for the map. Can be an object that defines a coordinate reference
   * system for projecting geographical points into screen coordinates and back
   * (see https://leafletjs.com/reference-1.7.1.html#crs-l-crs-base), or a string
   * name identifying one of Leaflet's defined CRSs, such as "EPSG4326".
   */
  crs: {
    type: [String, Object]
  },
  maxBoundsViscosity: {
    type: Number
  },
  inertia: {
    type: Boolean,
    default: void 0
  },
  inertiaDeceleration: {
    type: Number
  },
  inertiaMaxSpeed: {
    type: Number
  },
  easeLinearity: {
    type: Number
  },
  zoomAnimation: {
    type: Boolean,
    default: void 0
  },
  zoomAnimationThreshold: {
    type: Number
  },
  fadeAnimation: {
    type: Boolean,
    default: void 0
  },
  markerZoomAnimation: {
    type: Boolean,
    default: void 0
  },
  noBlockingAnimations: {
    type: Boolean,
    default: void 0
  },
  useGlobalLeaflet: {
    type: Boolean,
    default: !0,
    custom: !0
  }
}, io = S({
  inheritAttrs: !1,
  emits: ["ready", "update:zoom", "update:center", "update:bounds"],
  props: We,
  setup(e, o) {
    const t = c(), n = vt({
      ready: !1,
      layersToAdd: [],
      layersInControl: []
    }), { options: s } = J(e), r = f(
      e,
      We,
      s
    ), { listeners: l, attrs: a } = T(o.attrs), i = Y(M), u = Y(ee), d = Y(H), y = Y(
      me
    );
    A(h, e.useGlobalLeaflet);
    const w = oe(() => {
      const P = {};
      return e.noBlockingAnimations && (P.animate = !1), P;
    }), v = oe(() => {
      const P = w.value;
      return e.padding && (P.padding = e.padding), e.paddingTopLeft && (P.paddingTopLeft = e.paddingTopLeft), e.paddingBottomRight && (P.paddingBottomRight = e.paddingBottomRight), P;
    }), z = {
      moveend: rt((P) => {
        n.leafletRef && (o.emit("update:zoom", n.leafletRef.getZoom()), o.emit("update:center", n.leafletRef.getCenter()), o.emit("update:bounds", n.leafletRef.getBounds()));
      }),
      overlayadd(P) {
        const B = n.layersInControl.find((I) => I.name === P.name);
        B && B.updateVisibleProp(!0);
      },
      overlayremove(P) {
        const B = n.layersInControl.find((I) => I.name === P.name);
        B && B.updateVisibleProp(!1);
      }
    };
    _(async () => {
      e.useGlobalLeaflet && (b.L = b.L || await import("leaflet"));
      const { map: P, CRS: B, Icon: I, latLngBounds: E, latLng: ue, stamp: $ } = e.useGlobalLeaflet ? b.L : await import("leaflet/dist/leaflet-src.esm");
      try {
        r.beforeMapMount && await r.beforeMapMount();
      } catch (p) {
        console.error(
          `The following error occurred running the provided beforeMapMount hook ${p.message}`
        );
      }
      await qe(I);
      const yt = typeof r.crs == "string" ? B[r.crs] : r.crs;
      r.crs = yt || B.EPSG3857;
      const Q = {
        addLayer(p) {
          p.layerType !== void 0 && (n.layerControl === void 0 ? n.layersToAdd.push(p) : n.layersInControl.find(
            (X) => $(X.leafletObject) === $(p.leafletObject)
          ) || (n.layerControl.addLayer(p), n.layersInControl.push(p))), p.visible !== !1 && n.leafletRef.addLayer(p.leafletObject);
        },
        removeLayer(p) {
          p.layerType !== void 0 && (n.layerControl === void 0 ? n.layersToAdd = n.layersToAdd.filter(
            (C) => C.name !== p.name
          ) : (n.layerControl.removeLayer(p.leafletObject), n.layersInControl = n.layersInControl.filter(
            (C) => $(C.leafletObject) !== $(p.leafletObject)
          ))), n.leafletRef.removeLayer(p.leafletObject);
        },
        registerLayerControl(p) {
          n.layerControl = p, n.layersToAdd.forEach((C) => {
            n.layerControl.addLayer(C);
          }), n.layersToAdd = [], d(p);
        },
        registerControl(p) {
          n.leafletRef.addControl(p.leafletObject);
        },
        setZoom(p) {
          const C = n.leafletRef.getZoom();
          p !== C && n.leafletRef.setZoom(p, w.value);
        },
        setCrs(p) {
          const C = n.leafletRef.getBounds();
          n.leafletRef.options.crs = p, n.leafletRef.fitBounds(C, {
            animate: !1,
            padding: [0, 0]
          });
        },
        fitBounds(p) {
          n.leafletRef.fitBounds(p, v.value);
        },
        setBounds(p) {
          if (!p)
            return;
          const C = E(p);
          if (!C.isValid())
            return;
          !(n.lastSetBounds || n.leafletRef.getBounds()).equals(C, 0) && (n.lastSetBounds = C, n.leafletRef.fitBounds(C));
        },
        setCenter(p) {
          if (p == null)
            return;
          const C = ue(p), X = n.lastSetCenter || n.leafletRef.getCenter();
          (X.lat !== C.lat || X.lng !== C.lng) && (n.lastSetCenter = C, n.leafletRef.panTo(C, w.value));
        }
      };
      V(i, Q.addLayer), V(u, Q.removeLayer), V(d, Q.registerControl), V(y, Q.registerLayerControl), n.leafletRef = j(P(t.value, r)), L(Q, n.leafletRef, e), ce(n.leafletRef, z), ce(n.leafletRef, l), n.ready = !0, g(() => o.emit("ready", n.leafletRef));
    }), R(() => {
      ye(z), n.leafletRef && (n.leafletRef.off(), n.leafletRef.remove());
    });
    const Z = oe(() => n.leafletRef), N = oe(() => n.ready);
    return { root: t, ready: N, leafletObject: Z, attrs: a };
  },
  render({ attrs: e }) {
    return e.style || (e.style = {}), e.style.width || (e.style.width = "100%"), e.style.height || (e.style.height = "100%"), U(
      "div",
      {
        ...e,
        ref: "root"
      },
      this.ready && this.$slots.default ? this.$slots.default() : {}
    );
  }
}), Gt = ["Symbol(Comment)", "Symbol(Text)"], zt = ["LTooltip", "LPopup"], ze = {
  ...D,
  draggable: {
    type: Boolean,
    default: void 0
  },
  icon: {
    type: [Object]
  },
  zIndexOffset: {
    type: Number
  },
  latLng: {
    type: [Object, Array],
    custom: !0,
    required: !0
  }
}, st = (e, o, t) => {
  const { options: n, methods: s } = q(
    e,
    o,
    t
  ), r = f(
    e,
    ze,
    n
  ), l = {
    ...s,
    setDraggable(a) {
      o.value.dragging && (a ? o.value.dragging.enable() : o.value.dragging.disable());
    },
    latLngSync(a) {
      t.emit("update:latLng", a.latlng), t.emit("update:lat-lng", a.latlng);
    },
    setLatLng(a) {
      if (a != null && o.value) {
        const i = o.value.getLatLng();
        (!i || !i.equals(a)) && o.value.setLatLng(a);
      }
    }
  };
  return { options: r, methods: l };
}, at = (e, o) => {
  const t = o.slots.default && o.slots.default();
  return t && t.length && t.some(Nt);
};
function Nt(e) {
  return !(Gt.includes(e.type.toString()) || zt.includes(e.type.name));
}
const $t = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  markerProps: ze,
  setupMarker: st,
  shouldBlankIcon: at
}, Symbol.toStringTag, { value: "Module" })), uo = S({
  name: "LMarker",
  props: ze,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M);
    A(
      ve,
      () => {
        var u;
        return !!((u = t.value) != null && u.getElement());
      }
    ), A(be, (u) => {
      var y, w;
      const d = k((y = t.value) == null ? void 0 : y.getElement) && ((w = t.value) == null ? void 0 : w.getElement());
      d && (d.innerHTML = u);
    }), A(
      fe,
      (u) => {
        var d;
        return ((d = t.value) == null ? void 0 : d.setIcon) && t.value.setIcon(u);
      }
    );
    const { options: l, methods: a } = st(e, t, o), i = {
      moveHandler: rt(a.latLngSync)
    };
    return _(async () => {
      const { marker: u, divIcon: d } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      at(l, o) && (l.icon = d({ className: "" })), t.value = j(u(e.latLng, l));
      const { listeners: y } = T(o.attrs);
      t.value.on(y), t.value.on("move", i.moveHandler), L(a, t.value, e), r({
        ...e,
        ...a,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), R(() => ye(i)), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), le = {
  ...ne,
  smoothFactor: {
    type: Number
  },
  noClip: {
    type: Boolean,
    default: void 0
  },
  latLngs: {
    type: Array,
    required: !0,
    custom: !0
  }
}, Ne = (e, o, t) => {
  const { options: n, methods: s } = _e(
    e,
    o,
    t
  ), r = f(
    e,
    le,
    n
  ), l = {
    ...s,
    setSmoothFactor(a) {
      o.value.setStyle({ smoothFactor: a });
    },
    setNoClip(a) {
      o.value.setStyle({ noClip: a });
    },
    addLatLng(a) {
      o.value.addLatLng(a);
    }
  };
  return { options: r, methods: l };
}, kt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  polylineProps: le,
  setupPolyline: Ne
}, Symbol.toStringTag, { value: "Module" })), x = {
  ...le
}, $e = (e, o, t) => {
  const { options: n, methods: s } = Ne(
    e,
    o,
    t
  ), r = f(
    e,
    x,
    n
  ), l = {
    ...s,
    toGeoJSON(a) {
      return o.value.toGeoJSON(a);
    }
  };
  return { options: r, methods: l };
}, Ut = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  polygonProps: x,
  setupPolygon: $e
}, Symbol.toStringTag, { value: "Module" })), co = S({
  name: "LPolygon",
  props: x,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { options: l, methods: a } = $e(e, t, o);
    return _(async () => {
      const { polygon: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(i(e.latLngs, l));
      const { listeners: u } = T(o.attrs);
      t.value.on(u), L(a, t.value, e), r({
        ...e,
        ...a,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), po = S({
  name: "LPolyline",
  props: le,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { options: l, methods: a } = Ne(e, t, o);
    return _(async () => {
      const { polyline: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        i(e.latLngs, l)
      );
      const { listeners: u } = T(o.attrs);
      t.value.on(u), L(a, t.value, e), r({
        ...e,
        ...a,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), ke = {
  ...W,
  content: {
    type: String,
    default: null
  }
}, Ue = (e, o) => {
  const { options: t, methods: n } = J(e), s = {
    ...n,
    setContent(r) {
      o.value && r !== null && r !== void 0 && o.value.setContent(r);
    }
  };
  return { options: t, methods: s };
}, De = (e) => e.default ? U("div", { ref: "root" }, e.default()) : null, Dt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  popperProps: ke,
  render: De,
  setupPopper: Ue
}, Symbol.toStringTag, { value: "Module" })), lt = {
  ...ke,
  latLng: {
    type: [Object, Array],
    default: () => []
  }
}, it = (e, o) => {
  const { options: t, methods: n } = Ue(e, o);
  return { options: t, methods: n };
}, Ft = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  popupProps: lt,
  setupPopup: it
}, Symbol.toStringTag, { value: "Module" })), yo = S({
  name: "LPopup",
  props: lt,
  setup(e, o) {
    const t = c(), n = c(null), s = O(h), r = m(ge), l = m(he), { options: a, methods: i } = it(e, t);
    return _(async () => {
      const { popup: u } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(u(a)), e.latLng !== void 0 && t.value.setLatLng(e.latLng), L(i, t.value, e);
      const { listeners: d } = T(o.attrs);
      t.value.on(d), t.value.setContent(e.content || n.value || ""), r(t.value), g(() => o.emit("ready", t.value));
    }), R(() => {
      l();
    }), { root: n, leafletObject: t };
  },
  render() {
    return De(this.$slots);
  }
}), Fe = {
  ...x,
  latLngs: {
    ...x.latLngs,
    required: !1
  },
  bounds: {
    type: Object,
    custom: !0
  }
}, ut = (e, o, t) => {
  const { options: n, methods: s } = $e(
    e,
    o,
    t
  ), r = f(
    e,
    Fe,
    n
  ), l = {
    ...s,
    setBounds(a) {
      o.value.setBounds(a);
    },
    setLatLngs(a) {
      o.value.setBounds(a);
    }
  };
  return { options: r, methods: l };
}, Zt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  rectangleProps: Fe,
  setupRectangle: ut
}, Symbol.toStringTag, { value: "Module" })), mo = S({
  name: "LRectangle",
  props: Fe,
  setup(e, o) {
    const t = c(), n = c(!1), s = O(h), r = m(M), { options: l, methods: a } = ut(e, t, o);
    return _(async () => {
      const { rectangle: i, latLngBounds: u } = s ? b.L : await import("leaflet/dist/leaflet-src.esm"), d = e.bounds ? u(e.bounds) : u(e.latLngs || []);
      t.value = j(i(d, l));
      const { listeners: y } = T(o.attrs);
      t.value.on(y), L(a, t.value, e), r({
        ...e,
        ...a,
        leafletObject: t.value
      }), n.value = !0, g(() => o.emit("ready", t.value));
    }), { ready: n, leafletObject: t };
  },
  render() {
    return G(this.ready, this.$slots);
  }
}), ie = {
  ...ae,
  tms: {
    type: Boolean,
    default: void 0
  },
  subdomains: {
    type: [String, Array],
    validator: (e) => typeof e == "string" ? !0 : Array.isArray(e) ? e.every((o) => typeof o == "string") : !1
  },
  detectRetina: {
    type: Boolean,
    default: void 0
  },
  url: {
    type: String,
    required: !0,
    custom: !0
  }
}, Ze = (e, o, t) => {
  const { options: n, methods: s } = Ae(e, o, t), r = f(
    e,
    ie,
    n
  ), l = {
    ...s
  };
  return { options: r, methods: l };
}, Et = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  setupTileLayer: Ze,
  tileLayerProps: ie
}, Symbol.toStringTag, { value: "Module" })), vo = S({
  props: ie,
  setup(e, o) {
    const t = c(), n = O(h), s = m(M), { options: r, methods: l } = Ze(e, t, o);
    return _(async () => {
      const { tileLayer: a } = n ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(a(e.url, r));
      const { listeners: i } = T(o.attrs);
      t.value.on(i), L(l, t.value, e), s({
        ...e,
        ...l,
        leafletObject: t.value
      }), g(() => o.emit("ready", t.value));
    }), { leafletObject: t };
  },
  render() {
    return null;
  }
}), ct = {
  ...ke
}, dt = (e, o) => {
  const { options: t, methods: n } = Ue(e, o), s = m(Oe);
  return R(() => {
    s();
  }), { options: t, methods: n };
}, Ht = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  setupTooltip: dt,
  tooltipProps: ct
}, Symbol.toStringTag, { value: "Module" })), bo = S({
  name: "LTooltip",
  props: ct,
  setup(e, o) {
    const t = c(), n = c(null), s = O(h), r = m(Le), { options: l, methods: a } = dt(e, t);
    return _(async () => {
      const { tooltip: i } = s ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(i(l)), L(a, t.value, e);
      const { listeners: u } = T(o.attrs);
      t.value.on(u), t.value.setContent(e.content || n.value || ""), r(t.value), g(() => o.emit("ready", t.value));
    }), { root: n, leafletObject: t };
  },
  render() {
    return De(this.$slots);
  }
}), Ee = {
  ...ie,
  layers: {
    type: String,
    required: !0
  },
  styles: {
    type: String
  },
  format: {
    type: String
  },
  transparent: {
    type: Boolean,
    default: void 0
  },
  version: {
    type: String
  },
  crs: {
    type: Object
  },
  uppercase: {
    type: Boolean,
    default: void 0
  }
}, pt = (e, o, t) => {
  const { options: n, methods: s } = Ze(e, o, t);
  return {
    options: f(
      e,
      Ee,
      n
    ),
    methods: {
      ...s
    }
  };
}, Wt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  setupWMSTileLayer: pt,
  wmsTileLayerProps: Ee
}, Symbol.toStringTag, { value: "Module" })), fo = S({
  props: Ee,
  setup(e, o) {
    const t = c(), n = O(h), s = m(M), { options: r, methods: l } = pt(
      e,
      t,
      o
    );
    return _(async () => {
      const { tileLayer: a } = n ? b.L : await import("leaflet/dist/leaflet-src.esm");
      t.value = j(
        a.wms(e.url, r)
      );
      const { listeners: i } = T(o.attrs);
      t.value.on(i), L(l, t.value, e), s({
        ...e,
        ...l,
        leafletObject: t.value
      }), g(() => o.emit("ready", t.value));
    }), { leafletObject: t };
  },
  render() {
    return null;
  }
}), go = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  Circle: Ot,
  CircleMarker: ht,
  Component: bt,
  Control: St,
  ControlAttribution: _t,
  ControlLayers: jt,
  ControlScale: Pt,
  ControlZoom: Ct,
  FeatureGroup: Mt,
  GeoJSON: Bt,
  GridLayer: wt,
  Icon: It,
  ImageOverlay: At,
  InteractiveLayer: gt,
  Layer: ft,
  LayerGroup: Tt,
  Marker: $t,
  Path: Lt,
  Polygon: Ut,
  Polyline: kt,
  Popper: Dt,
  Popup: Ft,
  Rectangle: Zt,
  TileLayer: Et,
  Tooltip: Ht,
  WmsTileLayer: Wt
}, Symbol.toStringTag, { value: "Module" }));
export {
  go as Functions,
  Qt as InjectionKeys,
  Xt as LCircle,
  Yt as LCircleMarker,
  Vt as LControl,
  xt as LControlAttribution,
  Rt as LControlLayers,
  eo as LControlScale,
  to as LControlZoom,
  oo as LFeatureGroup,
  no as LGeoJson,
  ro as LGridLayer,
  so as LIcon,
  ao as LImageOverlay,
  lo as LLayerGroup,
  io as LMap,
  uo as LMarker,
  co as LPolygon,
  po as LPolyline,
  yo as LPopup,
  mo as LRectangle,
  vo as LTileLayer,
  bo as LTooltip,
  fo as LWmsTileLayer,
  Kt as Utilities
};
