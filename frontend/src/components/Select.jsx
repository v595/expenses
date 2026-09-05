import { useEffect, useId, useRef, useState } from "react";

import { IconChevronDown } from "./icons";

/**
 * Accessible drop-down that replaces a native <select>.
 *
 * Why this exists: the option list a native <select> opens is drawn by the
 * operating system. No CSS can restyle it (which is why it looked dated), and
 * it can only contain plain text — no flags, no icons. Anything richer has to
 * be a custom listbox, so this re-implements the parts the browser gave us for
 * free: keyboard navigation, type-ahead, focus handling and ARIA wiring.
 *
 * options: [{ value, label, icon?, hint? }]
 */
function Select({
  value,
  onChange,
  options,
  placeholder = "Select...",
  disabled = false,
  name,
  id,
  ariaLabel,
}) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const rootRef = useRef(null);
  const listRef = useRef(null);
  const triggerRef = useRef(null);
  const typeahead = useRef({ text: "", at: 0 });
  const generatedId = useId();
  const listId = `${id || generatedId}-listbox`;

  const selectedIndex = options.findIndex((o) => String(o.value) === String(value));
  const selected = selectedIndex >= 0 ? options[selectedIndex] : null;

  // Close when focus or a click goes anywhere outside the component.
  useEffect(() => {
    if (!open) return;
    function onPointerDown(e) {
      if (!rootRef.current?.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [open]);

  // Keep the highlighted row in view when arrowing through a long list.
  useEffect(() => {
    if (!open || activeIndex < 0) return;
    listRef.current?.children[activeIndex]?.scrollIntoView({ block: "nearest" });
  }, [open, activeIndex]);

  function openList() {
    if (disabled) return;
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
    setOpen(true);
  }

  function commit(index) {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    setOpen(false);
    triggerRef.current?.focus();
  }

  function handleKeyDown(e) {
    if (disabled) return;

    if (!open) {
      // Down/Up/Enter/Space all open the list, matching a native select.
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
        e.preventDefault();
        openList();
      }
      return;
    }

    switch (e.key) {
      case "Escape":
        e.preventDefault();
        setOpen(false);
        triggerRef.current?.focus();
        break;
      case "Tab":
        // Let focus leave naturally, but don't leave the list hanging open.
        setOpen(false);
        break;
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((i) => (i + 1) % options.length);
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((i) => (i - 1 + options.length) % options.length);
        break;
      case "Home":
        e.preventDefault();
        setActiveIndex(0);
        break;
      case "End":
        e.preventDefault();
        setActiveIndex(options.length - 1);
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        commit(activeIndex);
        break;
      default:
        // Type-ahead: typing "hd" jumps to HDFC. Resets after a short pause
        // so a new burst starts a fresh search rather than appending.
        if (e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey) {
          const now = Date.now();
          const t = typeahead.current;
          t.text = now - t.at > 700 ? e.key : t.text + e.key;
          t.at = now;
          const match = options.findIndex((o) =>
            o.label.toLowerCase().startsWith(t.text.toLowerCase())
          );
          if (match >= 0) setActiveIndex(match);
        }
    }
  }

  return (
    <div className={`select${open ? " select-open" : ""}`} ref={rootRef}>
      {/* Mirrors the value for normal form submission / uncontrolled reads. */}
      {name && <input type="hidden" name={name} value={value ?? ""} />}

      <button
        type="button"
        ref={triggerRef}
        id={id}
        className="select-trigger"
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        role="combobox"
        aria-controls={listId}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={ariaLabel}
      >
        <span className="select-value">
          {selected?.icon && <span className="select-icon">{selected.icon}</span>}
          <span className={selected ? "" : "select-placeholder"}>
            {selected ? selected.label : placeholder}
          </span>
        </span>
        <IconChevronDown className="select-chevron" width={16} height={16} />
      </button>

      {open && (
        <ul className="select-list" role="listbox" id={listId} ref={listRef} tabIndex={-1}>
          {options.map((option, i) => (
            <li
              key={option.value}
              role="option"
              aria-selected={i === selectedIndex}
              className={`select-option${i === activeIndex ? " is-active" : ""}${
                i === selectedIndex ? " is-selected" : ""
              }`}
              // mousedown, not click: the outside-click handler also runs on
              // mousedown, and would close the list before a click landed.
              onMouseDown={(e) => {
                e.preventDefault();
                commit(i);
              }}
              onMouseEnter={() => setActiveIndex(i)}
            >
              {option.icon && <span className="select-icon">{option.icon}</span>}
              <span className="select-option-label">{option.label}</span>
              {option.hint && <span className="select-option-hint">{option.hint}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Select;
