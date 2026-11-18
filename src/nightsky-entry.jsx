import React from "react";
import { createRoot } from "react-dom/client";
import NightSkyBackground from "./NightSkyBackground.js";

// Draw only while dark mode is the theme and the plate is on screen. The canvas is
// fixed to the viewport so the sky keeps moving behind the hero while the page
// scrolls, and it fades out well before the content below.
const cv = document.querySelector(".nightsky");
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

function mount() {
  cv.style.display = "block";
  requestAnimationFrame(() => { cv.style.opacity = "1"; });
  const root = createRoot(cv);
  root.render(
    React.createElement(NightSkyBackground, {
      // the component's own defaults, kept: 100 stars, a 7s comet timer, the
      // navy-to-black gradient it ships with
      starCount: 100,
      twinkleSpeed: 2,
      cometFrequency: 7,
      cometColor: "#ffffff",
      gradientTop: "#0a0e27",
      gradientBottom: "#000000"
    })
  );
  cv.__root = root;
}

function unmount() {
  cv.style.opacity = "0";
  setTimeout(() => {
    if (cv.__root) { cv.__root.unmount(); cv.__root = null; }
    cv.style.display = "none";
  }, 600);
}

const dark = () => document.documentElement.dataset.theme === "dark";

function sync() {
  const want = dark() && !reduce.matches;
  if (want && !cv.__root) mount();
  else if (!want && cv.__root) unmount();
}

new MutationObserver(sync).observe(document.documentElement, {
  attributes: true, attributeFilter: ["data-theme"]
});
reduce.addEventListener("change", sync);

// a first paint that lands already in dark mode
sync();
