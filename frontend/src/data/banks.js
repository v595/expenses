// Major Indian banks for the account picker.
//
// On logos: these are deliberately initial monograms, not the banks' real
// logos. Bank logos are registered trademarks and shipping copies of them in
// the app would be an infringement — a tinted monogram gives the same at-a-
// glance recognition in a list without redistributing anyone's mark. The
// colours are each bank's familiar brand hue, which is fine to use for tinting.
export const INDIAN_BANKS = [
  { value: "sbi", label: "State Bank of India", short: "SBI", color: "#22409A" },
  { value: "hdfc", label: "HDFC Bank", short: "HD", color: "#004C8F" },
  { value: "icici", label: "ICICI Bank", short: "IC", color: "#AE282E" },
  { value: "axis", label: "Axis Bank", short: "AX", color: "#97144D" },
  { value: "kotak", label: "Kotak Mahindra Bank", short: "KM", color: "#ED232A" },
  { value: "pnb", label: "Punjab National Bank", short: "PNB", color: "#A6212E" },
  { value: "bob", label: "Bank of Baroda", short: "BoB", color: "#F15A22" },
  { value: "canara", label: "Canara Bank", short: "CB", color: "#00539F" },
  { value: "union", label: "Union Bank of India", short: "UB", color: "#E4181C" },
  { value: "idfc", label: "IDFC First Bank", short: "ID", color: "#9C1D26" },
  { value: "indusind", label: "IndusInd Bank", short: "IN", color: "#8B1A2B" },
  { value: "yes", label: "Yes Bank", short: "YB", color: "#00518F" },
  { value: "boi", label: "Bank of India", short: "BoI", color: "#F58220" },
  { value: "central", label: "Central Bank of India", short: "CBI", color: "#1D4E9C" },
  { value: "indian", label: "Indian Bank", short: "IB", color: "#12447C" },
  { value: "iob", label: "Indian Overseas Bank", short: "IOB", color: "#004B87" },
  { value: "uco", label: "UCO Bank", short: "UC", color: "#0072BC" },
  { value: "federal", label: "Federal Bank", short: "FB", color: "#F7A800" },
  { value: "rbl", label: "RBL Bank", short: "RB", color: "#B4141E" },
  { value: "au", label: "AU Small Finance Bank", short: "AU", color: "#5C2D8E" },
  { value: "bandhan", label: "Bandhan Bank", short: "BB", color: "#C8102E" },
  { value: "idbi", label: "IDBI Bank", short: "ID", color: "#068C44" },
  { value: "paytm", label: "Paytm Payments Bank", short: "PB", color: "#00BAF2" },
  { value: "airtel", label: "Airtel Payments Bank", short: "AP", color: "#E40000" },
  { value: "other", label: "Other bank", short: "••", color: "#737373" },
];

// Non-bank account kinds, kept alongside so one picker covers every account.
export const OTHER_ACCOUNT_SOURCES = [
  { value: "cash", label: "Cash in hand", short: "₹", color: "#059669" },
  { value: "upi", label: "UPI / Wallet", short: "UP", color: "#6C3FB5" },
  { value: "credit_card", label: "Credit card", short: "CC", color: "#B45309" },
];

export const ALL_ACCOUNT_SOURCES = [...OTHER_ACCOUNT_SOURCES, ...INDIAN_BANKS];
