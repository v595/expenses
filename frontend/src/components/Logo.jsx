// Brand mark: three ascending bars that read as an "H" for Hisaab, with the
// crossbar doubling as a ledger rule. Bars = the spending/growth idea, the
// rule = the khaata line items are written on.
//
// `tile` renders the mark inside the brand-red app tile (sidebar, favicon,
// app icon). Without it the bars inherit currentColor, so the mark can sit on
// coloured backgrounds — e.g. white-on-red in the auth hero.

export function LogoMark({ size = 30, tile = true, className }) {
  const bars = (
    <>
      <rect x="17" y="30" width="7" height="18" rx="3.5" opacity="0.72" />
      <rect x="28.5" y="22" width="7" height="26" rx="3.5" opacity="0.86" />
      <rect x="40" y="14" width="7" height="34" rx="3.5" />
      <rect x="17" y="31.5" width="30" height="5" rx="2.5" opacity="0.95" />
    </>
  );

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role="img"
      aria-label="Hisaab"
    >
      {tile && <rect width="64" height="64" rx="16" fill="url(#hisaab-tile)" />}
      {tile && (
        <defs>
          <linearGradient id="hisaab-tile" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="100%" stopColor="#b91c1c" />
          </linearGradient>
        </defs>
      )}
      <g fill={tile ? "#fff" : "currentColor"}>{bars}</g>
    </svg>
  );
}

/** Mark plus wordmark, for headers and the auth hero. */
export function Logo({ size = 30, tile = true, className }) {
  return (
    <span className={`logo${className ? ` ${className}` : ""}`}>
      <LogoMark size={size} tile={tile} />
      <span className="logo-word">Hisaab</span>
    </span>
  );
}

export default Logo;
