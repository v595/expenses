import { forwardRef, useEffect, useId, useImperativeHandle, useRef, useState } from "react";

import { IconCalendar, IconChevronDown } from "./icons";

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function pad(n) {
  return String(n).padStart(2, "0");
}

function toKey(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function parseKey(key) {
  if (!key) return null;
  const [y, m, d] = key.split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

function sameDay(a, b) {
  return Boolean(a) && Boolean(b) &&
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addMonths(date, delta) {
  return new Date(date.getFullYear(), date.getMonth() + delta, 1);
}

function addDays(date, delta) {
  const d = new Date(date);
  d.setDate(d.getDate() + delta);
  return d;
}

// Always a full 6x7 grid, padded with the tail of the previous/next month,
// so the popup never shows a ragged or half-empty week.
function buildGrid(viewDate) {
  const gridStart = addDays(startOfMonth(viewDate), -startOfMonth(viewDate).getDay());
  return Array.from({ length: 42 }, (_, i) => addDays(gridStart, i));
}

function formatLabel(date) {
  return `${pad(date.getDate())} ${MONTHS[date.getMonth()].slice(0, 3)} ${date.getFullYear()}`;
}

/**
 * Custom calendar popup that replaces the OS-drawn native <input type="date">
 * picker — same reasoning as Select.jsx: no CSS can restyle the native one,
 * so this re-implements it (month grid, keyboard nav, ARIA) to match the
 * app's own theme.
 *
 * value/onChange use plain "YYYY-MM-DD" strings, same shape a native date
 * input produces, so this drops into existing form state unchanged.
 *
 * Exposes `open()` via ref so a paired "From"/"To" picker can auto-advance:
 * onChange={(v) => { setFrom(v); toRef.current?.open(); }}
 */
const DatePicker = forwardRef(function DatePicker(
  { value, onChange, placeholder = "Select date", disabled = false, name, id, ariaLabel },
  ref
) {
  const [open, setOpen] = useState(false);
  const selected = parseKey(value);
  const [viewDate, setViewDate] = useState(() => selected || new Date());
  const [activeDate, setActiveDate] = useState(() => selected || new Date());
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const gridRef = useRef(null);
  const generatedId = useId();
  const gridId = `${id || generatedId}-grid`;

  useImperativeHandle(ref, () => ({
    open: openCalendar,
    close: () => setOpen(false),
  }));

  // Close on any click/focus outside — same pattern as Select.jsx.
  useEffect(() => {
    if (!open) return;
    function onPointerDown(e) {
      if (!rootRef.current?.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [open]);

  // Always land on a meaningful date — the selected value, or today when the
  // field is still empty — so the grid is never opened with nothing shown.
  useEffect(() => {
    if (!open) return;
    const anchor = selected || new Date();
    setViewDate(startOfMonth(anchor));
    setActiveDate(anchor);
    requestAnimationFrame(() => gridRef.current?.focus());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function openCalendar() {
    if (disabled) return;
    setOpen(true);
  }

  function commit(date) {
    onChange(toKey(date));
    setOpen(false);
    triggerRef.current?.focus();
  }

  function clear() {
    onChange("");
    setOpen(false);
    triggerRef.current?.focus();
  }

  function moveActive(next) {
    setActiveDate(next);
    if (next.getMonth() !== viewDate.getMonth() || next.getFullYear() !== viewDate.getFullYear()) {
      setViewDate(startOfMonth(next));
    }
  }

  function handleTriggerKeyDown(e) {
    if (disabled || open) return;
    if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
      e.preventDefault();
      openCalendar();
    }
  }

  function handleGridKeyDown(e) {
    switch (e.key) {
      case "Escape":
        e.preventDefault();
        setOpen(false);
        triggerRef.current?.focus();
        break;
      case "Tab":
        setOpen(false);
        break;
      case "ArrowLeft":
        e.preventDefault();
        moveActive(addDays(activeDate, -1));
        break;
      case "ArrowRight":
        e.preventDefault();
        moveActive(addDays(activeDate, 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        moveActive(addDays(activeDate, -7));
        break;
      case "ArrowDown":
        e.preventDefault();
        moveActive(addDays(activeDate, 7));
        break;
      case "PageUp":
        e.preventDefault();
        moveActive(addMonths(activeDate, e.shiftKey ? -12 : -1));
        break;
      case "PageDown":
        e.preventDefault();
        moveActive(addMonths(activeDate, e.shiftKey ? 12 : 1));
        break;
      case "Home":
        e.preventDefault();
        moveActive(addDays(activeDate, -activeDate.getDay()));
        break;
      case "End":
        e.preventDefault();
        moveActive(addDays(activeDate, 6 - activeDate.getDay()));
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        commit(activeDate);
        break;
      default:
        break;
    }
  }

  const today = new Date();
  const days = buildGrid(viewDate);

  return (
    <div className={`datepicker${open ? " datepicker-open" : ""}`} ref={rootRef}>
      {name && <input type="hidden" name={name} value={value ?? ""} />}

      <button
        type="button"
        ref={triggerRef}
        id={id}
        className="datepicker-trigger"
        onClick={() => (open ? setOpen(false) : openCalendar())}
        onKeyDown={handleTriggerKeyDown}
        disabled={disabled}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={ariaLabel}
      >
        <IconCalendar className="datepicker-icon" width={16} height={16} />
        <span className={selected ? "datepicker-value" : "datepicker-value datepicker-placeholder"}>
          {selected ? formatLabel(selected) : placeholder}
        </span>
      </button>

      {open && (
        <div className="datepicker-panel" role="dialog" aria-label={ariaLabel || "Choose date"}>
          <div className="datepicker-header">
            <button
              type="button"
              className="datepicker-nav"
              onClick={() => setViewDate((v) => addMonths(v, -1))}
              aria-label="Previous month"
            >
              <IconChevronDown width={16} height={16} style={{ transform: "rotate(90deg)" }} />
            </button>
            <span className="datepicker-month">
              {MONTHS[viewDate.getMonth()]} {viewDate.getFullYear()}
            </span>
            <button
              type="button"
              className="datepicker-nav"
              onClick={() => setViewDate((v) => addMonths(v, 1))}
              aria-label="Next month"
            >
              <IconChevronDown width={16} height={16} style={{ transform: "rotate(-90deg)" }} />
            </button>
          </div>

          <div className="datepicker-weekdays">
            {WEEKDAYS.map((w) => (
              <span key={w}>{w}</span>
            ))}
          </div>

          <div
            className="datepicker-grid"
            role="grid"
            id={gridId}
            ref={gridRef}
            tabIndex={0}
            onKeyDown={handleGridKeyDown}
          >
            {days.map((date) => {
              const inMonth = date.getMonth() === viewDate.getMonth();
              const classes = [
                "datepicker-day",
                !inMonth && "is-outside",
                sameDay(date, today) && "is-today",
                sameDay(date, activeDate) && "is-active",
                sameDay(date, selected) && "is-selected",
              ]
                .filter(Boolean)
                .join(" ");
              return (
                <button
                  type="button"
                  key={toKey(date)}
                  role="gridcell"
                  aria-selected={sameDay(date, selected)}
                  tabIndex={-1}
                  className={classes}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    commit(date);
                  }}
                  onMouseEnter={() => setActiveDate(date)}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>

          <div className="datepicker-footer">
            <button type="button" className="datepicker-quick" onClick={() => commit(today)}>
              Today
            </button>
            {selected && (
              <button type="button" className="datepicker-quick" onClick={clear}>
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
});

export default DatePicker;
