// Simplified SVG flags for the currency picker.
//
// Deliberately NOT emoji flags (🇮🇳 etc.): Windows ships no flag glyphs at all,
// so those render as bare letter pairs like "IN" — and this app is used on
// Windows. Inline SVG renders identically everywhere.
//
// These are recognisable simplifications, not heraldically exact reproductions;
// they're 20x14 chips displayed at roughly icon size.

const box = { width: 20, height: 14, viewBox: "0 0 20 14" };

function Frame({ children }) {
  return (
    <svg {...box} className="flag" role="presentation" focusable="false">
      {children}
      {/* Hairline keeps white flags (JP) from vanishing on a white menu. */}
      <rect x="0.25" y="0.25" width="19.5" height="13.5" rx="1.5" fill="none" stroke="rgba(0,0,0,0.18)" />
    </svg>
  );
}

export function FlagIN() {
  return (
    <Frame>
      <rect width="20" height="14" rx="1.5" fill="#fff" />
      <rect width="20" height="4.67" rx="1.5" fill="#FF9933" />
      <rect y="9.33" width="20" height="4.67" rx="1.5" fill="#138808" />
      <circle cx="10" cy="7" r="1.9" fill="none" stroke="#000080" strokeWidth="0.55" />
      <circle cx="10" cy="7" r="0.4" fill="#000080" />
    </Frame>
  );
}

export function FlagUS() {
  return (
    <Frame>
      <rect width="20" height="14" rx="1.5" fill="#fff" />
      {[0, 2, 4, 6].map((i) => (
        <rect key={i} y={i * 2.15 + 1.08} width="20" height="1.08" fill="#B22234" />
      ))}
      <rect width="20" height="1.08" fill="#B22234" />
      <rect width="9" height="7.5" fill="#3C3B6E" />
    </Frame>
  );
}

export function FlagEU() {
  return (
    <Frame>
      <rect width="20" height="14" rx="1.5" fill="#003399" />
      {Array.from({ length: 12 }).map((_, i) => {
        const a = (i * Math.PI) / 6;
        return (
          <circle
            key={i}
            cx={10 + Math.sin(a) * 4}
            cy={7 - Math.cos(a) * 4}
            r="0.6"
            fill="#FFCC00"
          />
        );
      })}
    </Frame>
  );
}

export function FlagGB() {
  return (
    <Frame>
      <rect width="20" height="14" rx="1.5" fill="#012169" />
      <path d="M0 0l20 14M20 0L0 14" stroke="#fff" strokeWidth="2.8" />
      <path d="M0 0l20 14M20 0L0 14" stroke="#C8102E" strokeWidth="1.2" />
      <path d="M10 0v14M0 7h20" stroke="#fff" strokeWidth="4" />
      <path d="M10 0v14M0 7h20" stroke="#C8102E" strokeWidth="2.2" />
    </Frame>
  );
}

export function FlagJP() {
  return (
    <Frame>
      <rect width="20" height="14" rx="1.5" fill="#fff" />
      <circle cx="10" cy="7" r="4" fill="#BC002D" />
    </Frame>
  );
}

export function FlagAU() {
  return (
    <Frame>
      <rect width="20" height="14" rx="1.5" fill="#00008B" />
      <rect width="9" height="7" fill="#00008B" />
      <path d="M0 0l9 7M9 0L0 7" stroke="#fff" strokeWidth="1.4" />
      <path d="M4.5 0v7M0 3.5h9" stroke="#fff" strokeWidth="2" />
      <path d="M4.5 0v7M0 3.5h9" stroke="#C8102E" strokeWidth="1" />
      <circle cx="14.5" cy="9" r="1" fill="#fff" />
      <circle cx="16.5" cy="4" r="0.7" fill="#fff" />
      <circle cx="4.5" cy="11" r="0.7" fill="#fff" />
    </Frame>
  );
}

export function FlagCA() {
  return (
    <Frame>
      <rect width="20" height="14" rx="1.5" fill="#fff" />
      <rect width="5" height="14" rx="1.5" fill="#FF0000" />
      <rect x="15" width="5" height="14" rx="1.5" fill="#FF0000" />
      <path
        d="M10 3.2l.75 1.65 1.6-.6-.6 1.6 1.65.75-1.65.75.6 1.6-1.6-.6L10 10.8l-.75-1.85-1.6.6.6-1.6L6.6 7.2l1.65-.75-.6-1.6 1.6.6z"
        fill="#FF0000"
      />
    </Frame>
  );
}

export const FLAGS = {
  INR: <FlagIN />,
  USD: <FlagUS />,
  EUR: <FlagEU />,
  GBP: <FlagGB />,
  JPY: <FlagJP />,
  AUD: <FlagAU />,
  CAD: <FlagCA />,
};
