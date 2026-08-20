import { IconMoon, IconSun } from "./icons";

function ThemeSwitch({ theme, onToggle }) {
  return (
    <button
      type="button"
      className="theme-switch"
      data-on={theme === "dark"}
      onClick={onToggle}
      aria-label="Toggle dark mode"
    >
      <span className="theme-switch-thumb">
        {theme === "dark" ? <IconMoon width={12} height={12} /> : <IconSun width={12} height={12} />}
      </span>
    </button>
  );
}

export default ThemeSwitch;
