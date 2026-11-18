// Minimal stand-in for Framer's runtime: the module only needs to register its
// property controls and to answer "am I being statically rendered?" (no).
export const ControlType = {
  Number: 'number', Color: 'color', Boolean: 'boolean', String: 'string',
  Enum: 'enum', Array: 'array', Object: 'object', File: 'file', Image: 'image'
};
export function addPropertyControls(component, controls) {
  component.propertyControls = controls;
  return component;
}
export function useIsStaticRenderer() { return false; }
export const RenderTarget = { canvas: 'canvas', current: 'current', thumbnail: 'thumbnail', export: 'export' };
export const PropertyControls = {};
export const useIsOnFramerCanvas = () => false;
export default { ControlType, addPropertyControls, useIsStaticRenderer };
