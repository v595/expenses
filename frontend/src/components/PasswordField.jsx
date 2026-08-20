import { useState } from "react";

import { IconEye, IconEyeOff } from "./icons";

function PasswordField({ label, ...inputProps }) {
  const [visible, setVisible] = useState(false);

  return (
    <label>
      {label}
      <div className="password-field">
        <input {...inputProps} type={visible ? "text" : "password"} />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          tabIndex={-1}
        >
          {visible ? <IconEyeOff width={18} height={18} /> : <IconEye width={18} height={18} />}
        </button>
      </div>
    </label>
  );
}

export default PasswordField;
