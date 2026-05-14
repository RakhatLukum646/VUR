import { useEffect, type RefObject } from 'react';

function isEventTargetInNode(target: EventTarget | null, node: HTMLElement | null) {
  if (!target) return false;
  if (!node) return false;
  if (!(target instanceof Node)) return false;
  return node.contains(target);
}

/** Close theme dropdown on outside click / Escape. */
export function useThemeControlsMenuClose(
  isOpen: boolean,
  onClose: () => void,
  ref: RefObject<HTMLDivElement | null>
) {
  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (e: PointerEvent) => {
      if (!isEventTargetInNode(e.target, ref.current)) onClose();
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [isOpen, onClose, ref]);
}
