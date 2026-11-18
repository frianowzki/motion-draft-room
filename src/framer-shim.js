// Minimal stand-in for Framer's runtime: code components only need to register their
// property controls, know whether they are being statically rendered (no, in a live
// page), and occasionally read the render target. Everything here is a constant.
export const ControlType = {
  Number: 'number', Color: 'color', Boolean: 'boolean', String: 'string',
  Enum: 'enum', Array: 'array', Object: 'object', File: 'file', Image: 'image',
  ComponentInstance: 'componentInstance', SegmentedEnum: 'segmentedEnum'
};
// Framer exposes this as an object whose current() call answers where we are drawing.
// Code components call RenderTarget.current() to detect the editor canvas, so it has
// to be a function or the component throws on mount.
export const RenderTarget = {
  canvas: 'canvas', thumbnail: 'thumbnail', export: 'export',
  current: () => 'current'
};
export function addPropertyControls(component, controls) {
  component.propertyControls = controls;
  return component;
}
export function useIsStaticRenderer() { return false; }
export function useIsOnFramerCanvas() { return false; }
export const PropertyControls = {};
export const framer = {};
export default { ControlType, RenderTarget, addPropertyControls, useIsStaticRenderer };
