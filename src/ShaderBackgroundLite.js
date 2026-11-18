/**
 * Shader Background Lite — free animated WebGL background for Framer by PixelSunset.
 * 5 presets, preset or custom colours, speed, scale and grain.
 *
 * Want 34 presets, intensity/seed, scroll parallax, tap ripples, FPS/DPR/resolution
 * controls, logo overlay and more? Get Shader Background Pro on the Framer Marketplace.
 *
 * @framerSupportedLayoutWidth any-prefer-fixed
 * @framerSupportedLayoutHeight any-prefer-fixed
 * @framerIntrinsicWidth 1200
 * @framerIntrinsicHeight 640
 */function _define_property(obj,key,value){if(key in obj){Object.defineProperty(obj,key,{value:value,enumerable:true,configurable:true,writable:true});}else{obj[key]=value;}return obj;}import{jsx as _jsx,jsxs as _jsxs}from"react/jsx-runtime";import{useEffect,useRef,useState}from"react";import{addPropertyControls,ControlType,RenderTarget,useIsStaticRenderer}from"framer";/* ------------------------------------------------------------------------- *//* GLSL                                                                       *//* ------------------------------------------------------------------------- */const VERT=`attribute vec2 a_pos;
void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }`;const HEADER=`
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 u_res;
uniform float u_time;
uniform vec3 u_c0;
uniform vec3 u_c1;
uniform vec3 u_c2;
uniform vec3 u_c3;
uniform vec3 u_c4;
uniform float u_count;
uniform float u_scale;
uniform float u_intensity;
uniform float u_grain;
uniform float u_seed;
uniform vec2 u_mouse;
uniform float u_mouseAmt;
uniform vec3 u_ripple;
uniform float u_scroll;
#define PI 3.14159265
#define TAU 6.28318531
float ASP;

float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec2 hash22(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
mat2 rot(float a){ float c = cos(a); float s = sin(a); return mat2(c, -s, s, c); }
float vnoise(vec2 p){
  vec2 i = floor(p); vec2 f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x), mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y);
}
vec3 mod289(vec3 x){ return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x){ return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x){ return mod289(((x * 34.0) + 1.0) * x); }
float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
  m = m * m; m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}
float fbm(vec2 p){ float s = 0.0; float a = 0.5; mat2 m = mat2(1.6, 1.2, -1.2, 1.6); for (int i = 0; i < 5; i++){ s += a * snoise(p); p = m * p; a *= 0.5; } return s; }
float fbm3(vec2 p){ float s = 0.0; float a = 0.5; mat2 m = mat2(1.6, 1.2, -1.2, 1.6); for (int i = 0; i < 3; i++){ s += a * snoise(p); p = m * p; a *= 0.5; } return s * 1.14; }
vec3 cAt(int i){ if (i == 0) return u_c0; if (i == 1) return u_c1; if (i == 2) return u_c2; if (i == 3) return u_c3; return u_c4; }
/* palette through all colours */
vec3 pal(float t){
  float x = clamp(t, 0.0, 1.0) * (u_count - 1.0);
  vec3 c = mix(u_c0, u_c1, smoothstep(0.0, 1.0, x));
  c = mix(c, u_c2, smoothstep(1.0, 2.0, x));
  c = mix(c, u_c3, smoothstep(2.0, 3.0, x));
  c = mix(c, u_c4, smoothstep(3.0, 4.0, x));
  return c;
}
/* palette that skips colour 1 (used as background by many presets) */
vec3 palB(float t){
  float x = 1.0 + clamp(t, 0.0, 1.0) * max(u_count - 2.0, 0.0);
  vec3 c = u_c1;
  c = mix(c, u_c2, smoothstep(1.0, 2.0, x));
  c = mix(c, u_c3, smoothstep(2.0, 3.0, x));
  c = mix(c, u_c4, smoothstep(3.0, 4.0, x));
  return c;
}
vec3 palLoop(float t){ return pal(1.0 - abs(1.0 - 2.0 * fract(t))); }
vec3 shade(vec2 p, vec2 uv);
`;const MAIN=`
void main(){
  ASP = u_res.x / u_res.y;
  vec2 uv = gl_FragCoord.xy / u_res;
  vec2 p = (uv - 0.5) * vec2(ASP, 1.0);
  vec2 dm = p - u_mouse;
  p -= dm * exp(-dot(dm, dm) * 10.0) * 0.3 * u_mouseAmt;
  if (u_ripple.z < 2.5) {
    vec2 dr = p - u_ripple.xy;
    float d = length(dr);
    float k = (d - u_ripple.z * 0.75) * 14.0;
    float w = exp(-k * k) * (1.0 - u_ripple.z / 2.5);
    p += dr / (d + 1e-4) * w * 0.035;
  }
  p.y += u_scroll;
  vec3 col = shade(p, uv);
  float g = hash12(gl_FragCoord.xy + fract(u_time * 0.37) * 517.0) - 0.5;
  col += g * u_grain * 0.35;
  col += (hash12(gl_FragCoord.xy * 1.37 + 3.1) - 0.5) / 255.0;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
`;const PRESETS={meshGradient:{label:"Mesh Gradient",colors:["#ff7a59","#ffc75f","#845ec2","#00c9a7","#4d8bf5"],glsl:`
vec3 shade(vec2 p, vec2 uv){
  vec2 q = p / u_scale;
  float t = u_time * 0.12 + u_seed;
  q += 0.18 * u_intensity * vec2(snoise(q * 1.1 + vec2(t, -t)), snoise(q * 1.1 + vec2(7.3 - t, t * 0.7)));
  vec3 acc = vec3(0.0); float ws = 0.0;
  for (int i = 0; i < 5; i++){
    float fi = float(i);
    if (fi < u_count) {
      vec2 c = vec2(0.5 * ASP * sin(t * (0.9 + 0.17 * fi) + fi * 2.4), 0.42 * cos(t * (0.7 + 0.13 * fi) + fi * 1.7));
      vec2 d = q - c;
      float w = 1.0 / pow(dot(d, d) + 0.002, 1.4);
      acc += cAt(i) * w; ws += w;
    }
  }
  return acc / ws;
}`},aurora:{label:"Aurora",colors:["#050816","#1fe5a8","#2bd2ff","#7b5cff","#ff5fa2"],glsl:`
vec3 shade(vec2 p, vec2 uv){
  vec2 q = p / u_scale;
  float t = u_time * 0.25 + u_seed;
  vec3 col = mix(u_c0 * 0.6, u_c0, uv.y);
  for (int i = 0; i < 3; i++){
    float fi = float(i);
    float x = q.x * (1.0 + 0.3 * fi) + fi * 3.1;
    float h = 0.22 * fbm3(vec2(x * 0.5 + t * 0.12, fi * 4.0 + t * 0.04)) + 0.07 * sin(x * 2.3 + t * 0.7 + fi * 2.0);
    float y = q.y - h + 0.02 + fi * 0.07;
    float below = smoothstep(-0.07, 0.0, y);
    float edge = exp(-max(y, 0.0) * 16.0);
    float s = vnoise(vec2(x * 28.0 + h * 18.0, t * 0.35 + fi * 7.0));
    float rays = pow(s, 2.2) * exp(-max(y, 0.0) * 3.0);
    float a = below * (edge * 0.5 + rays * 0.85) * (0.8 - fi * 0.18) * u_intensity;
    col += palB(fract(fi * 0.34 + 0.15 * sin(x * 0.4 + t * 0.2) + 0.1)) * a;
  }
  vec2 sid = floor(p * 140.0);
  col += step(0.996, hash12(sid)) * 0.45 * smoothstep(0.0, 0.6, uv.y) * (0.5 + 0.5 * sin(u_time * 3.0 + hash12(sid + 1.0) * 6.0));
  return col;
}`},silk:{label:"Silk",colors:["#1a0b2e","#5b2a86","#c04bd6","#f4a6d7","#fff1f8"],glsl:`
float silkH(vec2 q, float t){
  float h = sin(q.x * 1.5 + 1.3 * sin(q.y * 0.45 + t * 0.5) + t * 0.3);
  h += 0.45 * sin(q.x * 3.0 + 0.9 * sin(q.y * 0.7 - t * 0.4) - t * 0.5);
  h += 0.18 * snoise(vec2(q.x * 0.6, q.y * 0.3) + t * 0.1);
  return h;
}
vec3 shade(vec2 p, vec2 uv){
  vec2 q = rot(0.6) * (p / u_scale) * 2.2;
  float t = u_time * 0.25 + u_seed;
  float e = 0.01;
  float h = silkH(q, t);
  float hx = silkH(q + vec2(e, 0.0), t);
  float hy = silkH(q + vec2(0.0, e), t);
  vec3 n = normalize(vec3(-(hx - h) / e, -(hy - h) / e, 2.6 / (0.3 + 0.7 * u_intensity)));
  vec3 L = normalize(vec3(-0.5, 0.6, 0.65));
  float diff = clamp(dot(n, L) * 0.9 + 0.1, 0.0, 1.0);
  float spec = pow(max(dot(n, normalize(L + vec3(0.0, 0.0, 1.0))), 0.0), 36.0);
  float shadeV = smoothstep(0.0, 1.0, diff);
  return pal(clamp(0.05 + 0.8 * shadeV, 0.0, 1.0)) + pal(1.0) * spec * 0.3;
}`},liquidChrome:{label:"Liquid Chrome",colors:["#0b0d12","#3a4150","#9aa3b2","#e9edf2","#ffffff"],glsl:`
float chromeH(vec2 q, float t){
  for (int i = 1; i < 6; i++){
    float fi = float(i);
    q += vec2(0.5 / fi * sin(fi * q.y + t + 0.3 * fi), 0.5 / fi * cos(fi * q.x + t * 0.8 + 0.5 * fi));
  }
  return 0.5 + 0.5 * sin(q.x + q.y);
}
vec3 shade(vec2 p, vec2 uv){
  vec2 q = p / u_scale * 2.2;
  float t = u_time * 0.35 + u_seed;
  float e = 0.012;
  float h = chromeH(q, t);
  float hx = chromeH(q + vec2(e, 0.0), t);
  float hy = chromeH(q + vec2(0.0, e), t);
  vec3 n = normalize(vec3((h - hx) / e, (h - hy) / e, 2.2 / (0.4 + 0.6 * u_intensity)));
  float v = n.y + 0.3 * n.x;
  vec3 sky = mix(pal(0.6), pal(1.0), smoothstep(0.0, 0.7, v));
  vec3 ground = mix(pal(0.0), pal(0.35), smoothstep(-0.8, 0.0, v));
  vec3 col = mix(ground, sky, smoothstep(-0.025, 0.025, v));
  col += pow(max(dot(n, normalize(vec3(-0.4, 0.5, 0.8))), 0.0), 48.0) * 0.7;
  return col;
}`},caustics:{label:"Caustics",colors:["#012a4a","#014f86","#2a6f97","#61a5c2","#e0f7ff"],glsl:`
vec3 shade(vec2 p, vec2 uv){
  vec2 q = p / u_scale * 1.2;
  float t = u_time * 0.4 + u_seed + 23.0;
  vec2 pp = q * TAU - 250.0;
  vec2 i = pp; float c = 1.0; float inten = 0.005;
  for (int n = 0; n < 5; n++){
    float tt = t * (1.0 - (3.5 / float(n + 1)));
    i = pp + vec2(cos(tt - i.x) + sin(tt + i.y), sin(tt - i.y) + cos(tt + i.x));
    c += 1.0 / length(vec2(pp.x / (sin(i.x + tt) / inten), pp.y / (cos(i.y + tt) / inten)));
  }
  c /= 5.0;
  c = 1.17 - pow(c, 1.4);
  float v = clamp(pow(abs(c), 8.0), 0.0, 1.0);
  return pal(0.15 + 0.4 * uv.y) + pal(1.0) * v * u_intensity * 0.9;
}`}};const PRESET_KEYS=Object.keys(PRESETS);const DEFAULT_CUSTOM=["#0f172a","#6366f1","#ec4899","#f59e0b"];function buildFragmentSource(preset){const p=PRESETS[preset]||PRESETS.meshGradient;return HEADER+p.glsl+MAIN;}/* ------------------------------------------------------------------------- *//* Engine                                                                     *//* ------------------------------------------------------------------------- */const UNIFORM_NAMES=["u_res","u_time","u_c0","u_c1","u_c2","u_c3","u_c4","u_count","u_scale","u_intensity","u_grain","u_seed","u_mouse","u_mouseAmt","u_ripple","u_scroll"];class ShaderEngine{initResources(){const gl=this.gl;this.buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);// One oversized triangle covers the viewport (cheaper than a quad).
gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);this.vs=this.compile(gl.VERTEX_SHADER,VERT);this.program=null;}compile(type,src){const gl=this.gl;const s=gl.createShader(type);if(!s)return null;gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)&&!gl.isContextLost()){console.warn("[ShaderBackground] shader compile error:\n"+gl.getShaderInfoLog(s));gl.deleteShader(s);return null;}return s;}/** Compile + link a fragment shader. Returns false on failure. */setFragment(src){const gl=this.gl;this.source=src;if(!this.vs)return false;const fs=this.compile(gl.FRAGMENT_SHADER,src);if(!fs)return false;const prog=gl.createProgram();if(!prog)return false;gl.attachShader(prog,this.vs);gl.attachShader(prog,fs);gl.bindAttribLocation(prog,0,"a_pos");gl.linkProgram(prog);gl.deleteShader(fs);if(!gl.getProgramParameter(prog,gl.LINK_STATUS)&&!gl.isContextLost()){console.warn("[ShaderBackground] link error: "+gl.getProgramInfoLog(prog));gl.deleteProgram(prog);return false;}if(this.program)gl.deleteProgram(this.program);this.program=prog;gl.useProgram(prog);for(const n of UNIFORM_NAMES)this.loc[n]=gl.getUniformLocation(prog,n);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);return true;}/** Re-create GPU resources after a `webglcontextrestored` event. */restore(){this.initResources();return this.source?this.setFragment(this.source):false;}draw(u){const gl=this.gl;if(!this.program||gl.isContextLost())return false;const w=this.canvas.width;const h=this.canvas.height;gl.viewport(0,0,w,h);const L=this.loc;const c=u.colors;const at=i=>c[Math.min(i,c.length-1)];gl.uniform2f(L.u_res,w,h);gl.uniform1f(L.u_time,u.time);gl.uniform3fv(L.u_c0,at(0));gl.uniform3fv(L.u_c1,at(1));gl.uniform3fv(L.u_c2,at(2));gl.uniform3fv(L.u_c3,at(3));gl.uniform3fv(L.u_c4,at(4));gl.uniform1f(L.u_count,Math.max(2,Math.min(5,c.length)));gl.uniform1f(L.u_scale,Math.max(.05,u.scale));gl.uniform1f(L.u_intensity,u.intensity);gl.uniform1f(L.u_grain,u.grain);gl.uniform1f(L.u_seed,u.seed);gl.uniform2f(L.u_mouse,u.mouse[0],u.mouse[1]);gl.uniform1f(L.u_mouseAmt,u.mouseAmt);gl.uniform3f(L.u_ripple,u.ripple[0],u.ripple[1],u.ripple[2]);gl.uniform1f(L.u_scroll,u.scroll);gl.drawArrays(gl.TRIANGLES,0,3);return true;}destroy(){const gl=this.gl;try{if(this.program)gl.deleteProgram(this.program);if(this.vs)gl.deleteShader(this.vs);if(this.buffer)gl.deleteBuffer(this.buffer);gl.getExtension("WEBGL_lose_context")?.loseContext();}catch{/* context already gone */}this.program=null;this.vs=null;this.buffer=null;}constructor(canvas,lowPower){_define_property(this,"gl",void 0);_define_property(this,"canvas",void 0);_define_property(this,"program",null);_define_property(this,"vs",null);_define_property(this,"buffer",null);_define_property(this,"loc",{});_define_property(this,"source","");this.canvas=canvas;const attrs={alpha:false,antialias:false,depth:false,stencil:false,premultipliedAlpha:false,preserveDrawingBuffer:false,powerPreference:lowPower?"low-power":"default"};const gl=canvas.getContext("webgl",attrs)||canvas.getContext("experimental-webgl",attrs);if(!gl)throw new Error("WebGL unavailable");this.gl=gl;this.initResources();}}/* ------------------------------------------------------------------------- *//* Colour helpers                                                             *//* ------------------------------------------------------------------------- */function parseColorFallback(input){let s=(input||"").trim();const v=/^var\([^,]+,\s*(.+)\)$/.exec(s);if(v)s=v[1].trim();const hex=/^#([0-9a-f]{3,8})$/i.exec(s);if(hex){let h=hex[1];if(h.length<=4)h=h.split("").map(ch=>ch+ch).join("");return[parseInt(h.slice(0,2),16)/255,parseInt(h.slice(2,4),16)/255,parseInt(h.slice(4,6),16)/255];}const rgb=/rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/i.exec(s);if(rgb)return[+rgb[1]/255,+rgb[2]/255,+rgb[3]/255];return[.5,.5,.5];}let colorCtx=null;/** Resolves any CSS colour: hex, rgb(), hsl(), oklch(), Framer colour tokens (var(--token, fallback)). */function resolveColor(input,probe){// computed rgb() from our own probe element; also used by the regex fallback
let value=input;try{if(probe){probe.style.color="";probe.style.color=input;const computed=getComputedStyle(probe).color;if(computed)value=computed;}// Detached OffscreenCanvas (never part of the page) converts any CSS colour to RGB.
if(!colorCtx&&typeof OffscreenCanvas!=="undefined"){colorCtx=new OffscreenCanvas(1,1).getContext("2d",{willReadFrequently:true});}if(colorCtx){colorCtx.clearRect(0,0,1,1);colorCtx.fillStyle="#000";colorCtx.fillStyle=value;colorCtx.fillRect(0,0,1,1);const d=colorCtx.getImageData(0,0,1,1).data;return[d[0]/255,d[1]/255,d[2]/255];}}catch{/* fall through */}return parseColorFallback(value);}function fallbackBackground(colors){const a=colors[0]||"#111";const b=colors[1]||a;const c=colors[2]||b;const d=colors[3]||a;return[`radial-gradient(60% 70% at 18% 22%, ${b} 0%, transparent 70%)`,`radial-gradient(55% 65% at 82% 30%, ${c} 0%, transparent 70%)`,`radial-gradient(70% 60% at 50% 95%, ${d} 0%, transparent 70%)`,a].join(", ");}const DEFAULT_INTERACTION={mouse:true,mouseStrength:1,clickRipple:true,scroll:false,scrollStrength:1};const DEFAULT_PERFORMANCE={fpsCap:60,maxDpr:1.5,resolution:1,pauseOffscreen:true,lowPowerMobile:true,animateOnCanvas:false};function detectLowPower(enabled){if(!enabled||typeof window==="undefined")return false;try{const nav=navigator;const coarse=!!window.matchMedia?.("(pointer: coarse)").matches&&navigator.maxTouchPoints>0;const saveData=!!nav.connection?.saveData;const weak=typeof nav.deviceMemory==="number"&&nav.deviceMemory<=2;return coarse||saveData||weak;}catch{return false;}}function usePrefersReducedMotion(){const[reduced,setReduced]=useState(false);useEffect(()=>{if(typeof window==="undefined"||!window.matchMedia)return;const mq=window.matchMedia("(prefers-reduced-motion: reduce)");const update=()=>setReduced(mq.matches);update();mq.addEventListener?.("change",update);return()=>mq.removeEventListener?.("change",update);},[]);return reduced;}/** Canvases whose WebGL context this component destroyed (never handed to a new engine). */const DESTROYED_CANVASES=new WeakSet;/**
 * Shader Background Lite
 *
 * @framerSupportedLayoutWidth any-prefer-fixed
 * @framerSupportedLayoutHeight any-prefer-fixed
 * @framerIntrinsicWidth 1200
 * @framerIntrinsicHeight 640
 */export default function ShaderBackgroundLite(props){const{preset="meshGradient",palette="preset",colors=DEFAULT_CUSTOM,radius=0,style}=props;// Lite: fixed engine settings (configurable in Shader Background Pro).
const reducedMotion="still";const interaction=DEFAULT_INTERACTION;const perf=DEFAULT_PERFORMANCE;// Cursor Reaction off: no pointer listeners, mouse uniform held at the neutral centre.
const cursorOn=props.cursorReaction!==false;const hostRef=useRef(null);const canvasRef=useRef(null);const probeRef=useRef(null);const[failed,setFailed]=useState(false);// The <canvas> is rendered declaratively in JSX. Its key bumps after an engine is torn
// down (context lost on purpose), so a remount always gets a fresh canvas element.
const[canvasGen,setCanvasGen]=useState(0);const prefersReduced=usePrefersReducedMotion();// useIsStaticRenderer() is true on the canvas, in thumbnails and exports. Only the editor
// canvas may opt back into animation (Animate on Canvas); thumbnails/exports never animate.
const staticRenderer=useIsStaticRenderer();const onCanvas=RenderTarget.current()===RenderTarget.canvas;const[userPaused,setUserPaused]=useState(false);const[hovered,setHovered]=useState(false);const[focusWithin,setFocusWithin]=useState(false);const isStatic=staticRenderer&&!(onCanvas&&perf.animateOnCanvas)||prefersReduced&&reducedMotion==="still";const slowMotion=prefersReduced&&reducedMotion==="slow";const interactive=!staticRenderer&&!(prefersReduced&&reducedMotion!=="ignore");const showPause=props.pauseButton!==false&&!isStatic;const presetDef=PRESETS[preset]||PRESETS.meshGradient;const rawColors=(palette==="custom"&&colors&&colors.length?colors:presetDef.colors).slice(0,5);while(rawColors.length<2)rawColors.push(rawColors[0]||"#000000");const colorKey=rawColors.join("|");// Latest settings for the render loop (read every frame; no React re-render per frame).
const live=useRef({props,interaction,perf,isStatic,slowMotion,interactive,userPaused,colors:[]});live.current.userPaused=userPaused;live.current.props=props;live.current.interaction=cursorOn?interaction:{...interaction,mouse:false};live.current.perf=perf;live.current.isStatic=isStatic;live.current.slowMotion=slowMotion;live.current.interactive=interactive;const api=useRef(null);const pointerApi=useRef(null);// ----- Engine lifecycle (mount/unmount) -----
useEffect(()=>{const host=hostRef.current;const canvas=canvasRef.current;if(!host||!canvas||typeof document==="undefined")return;// Never reuse a canvas whose context was destroyed (StrictMode remount): the
// canvasGen bump from the cleanup renders a fresh <canvas> and re-runs this effect.
if(DESTROYED_CANVASES.has(canvas))return;const lowPower=detectLowPower(live.current.perf.lowPowerMobile);let engine;try{engine=new ShaderEngine(canvas,lowPower);}catch{// The (transparent) canvas stays mounted; the CSS gradient fallback shows.
setFailed(true);return;}let raf=0;let pendingStatic=0;let lastTick=0;let lastDraw=0;let time=0;let visible=true;let pageVisible=!document.hidden;let contextLost=false;let didFirstFrame=false;// Set whenever something outside the per-frame state changes (resize, colours, props, preset).
// Lets the loop skip identical frames (e.g. speed 0 with the pointer at rest).
let dirty=true;let rect=host.getBoundingClientRect();const mouse={x:0,y:0,tx:0,ty:0,amt:0,tamt:0};const ripple=[0,0,99];let scroll=0;let scrollTarget=0;const toLocal=(clientX,clientY)=>{const w=Math.max(1,rect.width);const h=Math.max(1,rect.height);const ux=(clientX-rect.left)/w;const uy=(clientY-rect.top)/h;return{x:(ux-.5)*(w/h),y:.5-uy,inside:ux>=0&&ux<=1&&uy>=0&&uy<=1};};const resize=()=>{rect=host.getBoundingClientRect();const P=live.current.perf;const cssW=Math.max(1,host.clientWidth);const cssH=Math.max(1,host.clientHeight);let dpr=Math.min(window.devicePixelRatio||1,Math.max(.5,P.maxDpr));if(lowPower)dpr=Math.min(dpr,1);let scaleF=dpr*Math.min(1,Math.max(.2,P.resolution))*(lowPower?.75:1);const MAX_PIXELS=35e5;if(cssW*cssH*scaleF*scaleF>MAX_PIXELS)scaleF=Math.sqrt(MAX_PIXELS/(cssW*cssH));const w=Math.max(1,Math.round(cssW*scaleF));const h=Math.max(1,Math.round(cssH*scaleF));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}requestDraw();};const currentUniforms=()=>{const L=live.current;const P=L.props;const seed=0;const still=L.isStatic;return{time:(still?4:time)+seed*7.31,colors:L.colors,scale:P.scale??1,intensity:1,grain:P.grain??.08,seed:seed*1.37,mouse:[mouse.x,mouse.y],mouseAmt:still?0:mouse.amt,ripple:still?[0,0,99]:ripple,scroll:still?0:scroll};};const drawNow=()=>{if(contextLost||!live.current.colors.length)return;if(!engine.draw(currentUniforms()))return;if(!didFirstFrame){didFirstFrame=true;canvas.style.opacity="1";host.setAttribute("data-shader-ready","true");}};const frame=now=>{raf=requestAnimationFrame(frame);const L=live.current;const fps=lowPower?Math.min(L.perf.fpsCap,30):L.perf.fpsCap;const minDelta=fps>=120?0:1e3/Math.max(1,fps);const elapsed=now-lastDraw;if(lastDraw&&elapsed<minDelta-1)return;// Advance the schedule by whole intervals so caps that are not a divisor of the
// display rate (e.g. 45 fps on 60 Hz) are honoured instead of snapping down to 30.
lastDraw=lastDraw&&elapsed<minDelta*2?lastDraw+minDelta:now;const dt=lastTick?Math.min((now-lastTick)/1e3,.1):0;lastTick=now;const prevTime=time;time+=dt*(L.props.speed??1)*(L.slowMotion?.2:1);const rippleActive=ripple[2]<99;const settling=Math.abs(mouse.tx-mouse.x)+Math.abs(mouse.ty-mouse.y)+Math.abs(mouse.tamt-mouse.amt)>1e-4||Math.abs(scrollTarget-scroll)>1e-5;const k=1-Math.exp(-dt*7);mouse.x+=(mouse.tx-mouse.x)*k;mouse.y+=(mouse.ty-mouse.y)*k;mouse.amt+=(mouse.tamt-mouse.amt)*k;scroll+=(scrollTarget-scroll)*(1-Math.exp(-dt*10));if(rippleActive)ripple[2]=ripple[2]+dt>2.5?99:ripple[2]+dt;if(!dirty&&!settling&&!rippleActive&&time===prevTime)return;dirty=false;drawNow();};const start=()=>{if(raf)return;if(pendingStatic){cancelAnimationFrame(pendingStatic);pendingStatic=0;}lastTick=0;lastDraw=0;dirty=true;raf=requestAnimationFrame(frame);};const stop=()=>{if(raf)cancelAnimationFrame(raf);raf=0;};const update=()=>{const L=live.current;// Interaction switched off (prop toggle, reduced motion, canvas): relax back to rest
// instead of freezing the last pointer lens / parallax offset.
if(!L.interactive||!L.interaction.mouse)mouse.tamt=0;if(!L.interactive||!L.interaction.scroll)scrollTarget=0;else onScroll();const run=!L.isStatic&&!L.userPaused&&!contextLost&&pageVisible&&(visible||!L.perf.pauseOffscreen);if(run)start();else{stop();requestDraw();}};function requestDraw(){dirty=true;if(raf||pendingStatic)return;pendingStatic=requestAnimationFrame(()=>{pendingStatic=0;drawNow();});}const setPreset=key=>{const ok=engine.setFragment(buildFragmentSource(key));if(!ok&&!engine.gl.isContextLost()){// Show the CSS gradient fallback instead of a stale/black canvas.
canvas.style.opacity="0";didFirstFrame=false;setFailed(true);}requestDraw();return ok;};// --- Observers & listeners ---
const ro=typeof ResizeObserver!=="undefined"?new ResizeObserver(resize):null;ro?.observe(host);const io=typeof IntersectionObserver!=="undefined"?new IntersectionObserver(entries=>{visible=entries[entries.length-1].isIntersecting;if(visible)rect=host.getBoundingClientRect();update();},{rootMargin:"120px"}):null;io?.observe(host);const onVisibility=()=>{pageVisible=!document.hidden;update();};const onPointerMove=e=>{const L=live.current;if(!L.interactive||!L.interaction.mouse){mouse.tamt=0;return;}const p=toLocal(e.clientX,e.clientY);mouse.tx=p.x;mouse.ty=p.y;mouse.tamt=p.inside?Math.max(0,L.interaction.mouseStrength):0;if(mouse.amt<.01){mouse.x=p.x;mouse.y=p.y;}};const onPointerDown=e=>{const L=live.current;if(!L.interactive)return;rect=host.getBoundingClientRect();const p=toLocal(e.clientX,e.clientY);if(!p.inside)return;if(L.interaction.clickRipple){ripple[0]=p.x;ripple[1]=p.y;ripple[2]=0;}if(e.pointerType!=="mouse")onPointerMove(e);};const onPointerEnd=e=>{if(e.pointerType!=="mouse")mouse.tamt=0;};const onLeave=()=>{mouse.tamt=0;};const onScroll=()=>{rect=host.getBoundingClientRect();const L=live.current;if(!L.interactive||!L.interaction.scroll){scrollTarget=0;return;}const vh=window.innerHeight||1;const center=rect.top+rect.height/2;scrollTarget=-((center-vh/2)/vh)*.35*L.interaction.scrollStrength;};const onContextLost=e=>{e.preventDefault();contextLost=true;stop();if(pendingStatic){cancelAnimationFrame(pendingStatic);pendingStatic=0;}};const onContextRestored=()=>{contextLost=false;if(!engine.restore())setFailed(true);update();};document.addEventListener("visibilitychange",onVisibility);window.addEventListener("pointerdown",onPointerDown,{passive:true});// Capture phase also catches scrolling inside nested scroll containers (keeps rect fresh).
window.addEventListener("scroll",onScroll,{passive:true,capture:true});window.addEventListener("resize",resize);canvas.addEventListener("webglcontextlost",onContextLost);canvas.addEventListener("webglcontextrestored",onContextRestored);api.current={requestDraw,update,setPreset};pointerApi.current={move:onPointerMove,end:onPointerEnd,leave:onLeave,reset:()=>{mouse.x=mouse.y=mouse.tx=mouse.ty=0;mouse.amt=mouse.tamt=0;requestDraw();}};resize();onScroll();setPreset(live.current.props.preset||"meshGradient");update();return()=>{stop();if(pendingStatic)cancelAnimationFrame(pendingStatic);ro?.disconnect();io?.disconnect();document.removeEventListener("visibilitychange",onVisibility);window.removeEventListener("pointerdown",onPointerDown);window.removeEventListener("scroll",onScroll,{capture:true});window.removeEventListener("resize",resize);canvas.removeEventListener("webglcontextlost",onContextLost);canvas.removeEventListener("webglcontextrestored",onContextRestored);api.current=null;pointerApi.current=null;engine.destroy();DESTROYED_CANVASES.add(canvas);setCanvasGen(g=>g+1);};},[canvasGen]);// ----- Cursor Reaction: pointer listeners exist only while the toggle is on -----
useEffect(()=>{const P=pointerApi.current;if(!P)return;if(!cursorOn){P.reset();return;}window.addEventListener("pointermove",P.move,{passive:true});window.addEventListener("pointerup",P.end,{passive:true});window.addEventListener("pointercancel",P.end,{passive:true});document.documentElement.addEventListener("pointerleave",P.leave);return()=>{window.removeEventListener("pointermove",P.move);window.removeEventListener("pointerup",P.end);window.removeEventListener("pointercancel",P.end);document.documentElement.removeEventListener("pointerleave",P.leave);};},[canvasGen,cursorOn]);// ----- Preset changes recompile only the fragment shader (context is kept) -----
const mountedPreset=useRef(preset);useEffect(()=>{if(mountedPreset.current===preset)return;mountedPreset.current=preset;if(api.current){setFailed(false);api.current.setPreset(preset);}},[preset]);// ----- Colour resolution (supports Framer colour tokens & dark-mode token swaps) -----
useEffect(()=>{const resolveAll=()=>{live.current.colors=rawColors.map(c=>resolveColor(c,probeRef.current));api.current?.requestDraw();};resolveAll();const mq=window.matchMedia?.("(prefers-color-scheme: dark)");mq?.addEventListener?.("change",resolveAll);return()=>mq?.removeEventListener?.("change",resolveAll);// eslint-disable-next-line react-hooks/exhaustive-deps
},[colorKey]);// ----- Any other prop change: redraw the still frame / start-stop the loop -----
useEffect(()=>{api.current?.update();api.current?.requestDraw();});return /*#__PURE__*/_jsxs("div",{ref:hostRef,"data-preset":preset,onPointerEnter:e=>e.pointerType==="mouse"&&setHovered(true),onPointerLeave:()=>setHovered(false),onFocus:()=>setFocusWithin(true),onBlur:e=>{if(!e.currentTarget.contains(e.relatedTarget))setFocusWithin(false);},style:{position:"relative",width:"100%",height:"100%",overflow:"hidden",borderRadius:radius,background:fallbackBackground(rawColors),isolation:"isolate",...style},children:[/*#__PURE__*/_jsx("canvas",{ref:canvasRef,"aria-hidden":"true",role:"presentation",style:{position:"absolute",inset:0,width:"100%",height:"100%",display:"block",opacity:0,transition:"opacity 400ms ease",pointerEvents:"none"}},canvasGen),/*#__PURE__*/_jsx("span",{ref:probeRef,"aria-hidden":"true",style:{position:"absolute",width:0,height:0,overflow:"hidden",visibility:"hidden"}}),failed&&/*#__PURE__*/_jsx("span",{"data-shader-fallback":"true",hidden:true}),showPause&&!failed&&/*#__PURE__*/_jsx("button",{type:"button",// The label names the action; no aria-pressed (it would contradict a changing label).
"aria-label":userPaused?"Play background animation":"Pause background animation",onClick:()=>setUserPaused(v=>!v),style:{position:"absolute",right:12,bottom:12,width:32,height:32,padding:0,border:"none",borderRadius:16,background:"rgba(0,0,0,0.45)",color:"#fff",cursor:"pointer",display:"grid",placeItems:"center",// Visible on hover and whenever keyboard focus is inside the component.
opacity:hovered||focusWithin?1:0,pointerEvents:hovered||focusWithin?"auto":"none",outlineOffset:2,transition:"opacity 0.15s",zIndex:2},children:/*#__PURE__*/_jsx("svg",{"aria-hidden":"true",focusable:"false",width:"12",height:"12",viewBox:"0 0 12 12",fill:"currentColor",children:userPaused?/*#__PURE__*/_jsx("path",{d:"M3 1.5v9l7.5-4.5z"}):/*#__PURE__*/_jsx("path",{d:"M2.5 1.5h2.5v9H2.5zM7 1.5h2.5v9H7z"})})})]});}ShaderBackgroundLite.displayName="Shader Background Lite";/* ------------------------------------------------------------------------- *//* Property controls                                                          *//* ------------------------------------------------------------------------- */addPropertyControls(ShaderBackgroundLite,{preset:{type:ControlType.Enum,title:"Preset",options:PRESET_KEYS,optionTitles:PRESET_KEYS.map(k=>PRESETS[k].label),defaultValue:"meshGradient",description:"5 presets in Lite. Shader Background Pro has 34 presets and more controls."},palette:{type:ControlType.Enum,title:"Colors",options:["preset","custom"],optionTitles:["Preset","Custom"],displaySegmentedControl:true,defaultValue:"preset"},colors:{type:ControlType.Array,title:"Palette",control:{type:ControlType.Color},maxCount:5,defaultValue:DEFAULT_CUSTOM,hidden:p=>p.palette!=="custom",description:"2–5 colors. Many presets use the first color as the background."},speed:{type:ControlType.Number,title:"Speed",min:0,max:5,step:.05,defaultValue:1,description:"0 freezes the animation."},scale:{type:ControlType.Number,title:"Scale",min:.2,max:4,step:.05,defaultValue:1,description:"Bigger values give bigger shapes."},grain:{type:ControlType.Number,title:"Grain",min:0,max:1,step:.01,defaultValue:.08,description:"Animated film grain."},cursorReaction:{type:ControlType.Boolean,title:"Cursor Reaction",defaultValue:true,description:"Off: the background ignores the cursor and touch movement."},pauseButton:{type:ControlType.Boolean,title:"Pause Button",defaultValue:true,description:"Pause/play button, shown on hover and keyboard focus."},radius:{type:ControlType.Number,title:"Radius",min:0,max:400,step:1,defaultValue:0,description:"Corner radius in px."}});
export const __FramerMetadata__ = {"exports":{"ShaderBackgroundLiteProps":{"type":"tsType","annotations":{"framerContractVersion":"1"}},"default":{"type":"reactComponent","name":"ShaderBackgroundLite","slots":[],"annotations":{"framerSupportedLayoutWidth":"any-prefer-fixed","framerContractVersion":"1","framerIntrinsicWidth":"1200","framerIntrinsicHeight":"640","framerSupportedLayoutHeight":"any-prefer-fixed"}},"__FramerMetadata__":{"type":"variable"}}}
//# sourceMappingURL=./ShaderBackgroundLite.map