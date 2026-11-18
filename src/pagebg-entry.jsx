import React from "react";
import { createRoot } from "react-dom/client";
import NightSkyBackground from "./NightSkyBackground.js";
import ShaderBackgroundLite from "./ShaderBackgroundLite.js";

// One page background, two looks, driven by the theme:
//   dark  -> the linked Framer NightSkyBackground (starfield + comets)
//   light -> the linked Framer ShaderBackgroundLite in its Aurora preset, recoloured
//            to a soft cloud palette so it reads as sky rather than neon
// Both are the real Framer code components; the Framer runtime bits they touch are
// shimmed in framer-shim.js. Only one is mounted at a time.
const host = document.querySelector(".pagebg");
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

// cloud colours: warm white light on a cold sky, deliberately low contrast so the
// page's black type stays the loudest thing on screen
const CLOUD = { palette: "custom", colors: ["#eef2f8", "#dfe7f2", "#f6f4ef", "#cbd8ea", "#fbfaf7"] };

const LOOKS = {
  dark: ["sky", () => React.createElement(NightSkyBackground, {
    starCount: 100, twinkleSpeed: 2, cometFrequency: 7,
    cometColor: "#ffffff", gradientTop: "#0a0e27", gradientBottom: "#000000"
  })],
  light: ["shader", () => React.createElement(ShaderBackgroundLite, {
    preset: "aurora", ...CLOUD, radius: 0
  })]
};

let mounted = null;   // "sky" | "shader"
let root = null;

function mount(kind) {
  if (mounted === kind) return;
  unmountNow();
  const look = LOOKS[kind];
  const layer = document.createElement("div");
  layer.className = "pagebg-layer is-" + look[0];
  host.appendChild(layer);
  root = createRoot(layer);
  root.render(look[1]());
  mounted = kind;
  host.style.display = "block";
  requestAnimationFrame(() => { host.style.opacity = "1"; });
}

function unmountNow() {
  if (root) { root.unmount(); root = null; }
  host.querySelectorAll(".pagebg-layer").forEach((n) => n.remove());
  mounted = null;
}

function sync() {
  const kind = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
  if (reduce.matches) { unmountNow(); host.style.opacity = "0"; host.style.display = "none"; return; }
  mount(kind);
}

new MutationObserver(sync).observe(document.documentElement, {
  attributes: true, attributeFilter: ["data-theme"]
});
reduce.addEventListener("change", sync);
sync();
