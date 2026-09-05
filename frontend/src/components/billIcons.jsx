// Bill-category icons. Pure inline SVG (no icon font, no image files) so they
// inherit currentColor, stay crisp at any size, and add no network requests.

const base = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.9,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

const Electricity = (p) => (
  <svg {...base} {...p}>
    <path d="M13 2 4.5 13.5H11l-1 8.5 8.5-11.5H12z" />
  </svg>
);

const Water = (p) => (
  <svg {...base} {...p}>
    <path d="M12 2.7s6 6.1 6 10.3a6 6 0 0 1-12 0c0-4.2 6-10.3 6-10.3z" />
  </svg>
);

const Gas = (p) => (
  <svg {...base} {...p}>
    <path d="M12 2s4.5 4 4.5 8a4.5 4.5 0 0 1-9 0c0-1.6.8-3 1.6-4 .3 1.2 1 2 1.9 2 1 0 1-2 1-6z" />
  </svg>
);

const Internet = (p) => (
  <svg {...base} {...p}>
    <path d="M2 8.5a15 15 0 0 1 20 0M5 12a10.5 10.5 0 0 1 14 0M8 15.5a6 6 0 0 1 8 0" />
    <circle cx="12" cy="19.5" r="1.1" fill="currentColor" stroke="none" />
  </svg>
);

const Phone = (p) => (
  <svg {...base} {...p}>
    <rect x="6.5" y="2" width="11" height="20" rx="2.5" />
    <path d="M10.5 18.5h3" />
  </svg>
);

const Rent = (p) => (
  <svg {...base} {...p}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5.5 9.5V20h13V9.5" />
    <path d="M10 20v-5.5h4V20" />
  </svg>
);

const Insurance = (p) => (
  <svg {...base} {...p}>
    <path d="M12 2.5 20 6v6c0 4.7-3.4 8.4-8 9.5-4.6-1.1-8-4.8-8-9.5V6z" />
    <path d="M9.2 12.2l2 2 3.6-3.8" />
  </svg>
);

const Subscription = (p) => (
  <svg {...base} {...p}>
    <path d="M20.5 12a8.5 8.5 0 1 1-2.6-6.1" />
    <path d="M20.5 3.5V9H15" />
  </svg>
);

const CreditCard = (p) => (
  <svg {...base} {...p}>
    <rect x="2.5" y="5" width="19" height="14" rx="2.5" />
    <path d="M2.5 10h19" />
    <path d="M6.5 15h3" />
  </svg>
);

const Education = (p) => (
  <svg {...base} {...p}>
    <path d="M12 3.5 22 8l-10 4.5L2 8z" />
    <path d="M6 10.2V15c0 1.6 2.7 3 6 3s6-1.4 6-3v-4.8" />
  </svg>
);

const Loan = (p) => (
  <svg {...base} {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M14.5 9.2a3 3 0 0 0-2.5-1.2c-1.5 0-2.6.8-2.6 2s1 1.7 2.6 2 2.8.8 2.8 2.1-1.2 2.1-2.8 2.1a3.2 3.2 0 0 1-2.6-1.2" />
    <path d="M12 6.2v11.6" />
  </svg>
);

const Medical = (p) => (
  <svg {...base} {...p}>
    <rect x="3" y="6.5" width="18" height="13" rx="2.5" />
    <path d="M9 6.5V4.5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 4.5v2" />
    <path d="M12 10.5v5M9.5 13h5" />
  </svg>
);

const Transport = (p) => (
  <svg {...base} {...p}>
    <path d="M4 16.5V8.8L6 5h12l2 3.8v7.7" />
    <path d="M4 12h16" />
    <circle cx="7.5" cy="16.5" r="1.6" />
    <circle cx="16.5" cy="16.5" r="1.6" />
  </svg>
);

const Other = (p) => (
  <svg {...base} {...p}>
    <rect x="3.5" y="4" width="17" height="16" rx="2.5" />
    <path d="M7.5 9h9M7.5 13h9M7.5 17h5" />
  </svg>
);

// One row per bill kind. `value` is what gets stored, so keep these stable.
export const BILL_TYPES = [
  { value: "electricity", label: "Electricity", Icon: Electricity },
  { value: "water", label: "Water", Icon: Water },
  { value: "gas", label: "Gas / LPG", Icon: Gas },
  { value: "internet", label: "Internet / Broadband", Icon: Internet },
  { value: "mobile", label: "Mobile / Phone", Icon: Phone },
  { value: "rent", label: "Rent", Icon: Rent },
  { value: "insurance", label: "Insurance", Icon: Insurance },
  { value: "subscription", label: "Subscription", Icon: Subscription },
  { value: "credit_card", label: "Credit card", Icon: CreditCard },
  { value: "loan", label: "Loan / EMI", Icon: Loan },
  { value: "education", label: "Education / Fees", Icon: Education },
  { value: "medical", label: "Medical", Icon: Medical },
  { value: "transport", label: "Transport / Fuel", Icon: Transport },
  { value: "other", label: "Other", Icon: Other },
];

export function billTypeIcon(value) {
  const match = BILL_TYPES.find((t) => t.value === value);
  const Icon = match ? match.Icon : Other;
  return <Icon />;
}

export function billTypeLabel(value) {
  return BILL_TYPES.find((t) => t.value === value)?.label || "Other";
}

// Ready-made options for <Select>.
export const BILL_TYPE_OPTIONS = BILL_TYPES.map(({ value, label, Icon }) => ({
  value,
  label,
  icon: <Icon />,
}));
