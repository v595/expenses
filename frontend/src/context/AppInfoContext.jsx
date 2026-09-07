import { createContext, useContext, useEffect, useState } from "react";

import { getAppInfo } from "../services/api";

const AppInfoContext = createContext({ appName: "Hisaab" });

// The name is admin-configurable (System Settings > Application Name), so
// the brand text on screen shouldn't be hardcoded — fetched once and shared
// via context rather than every header/logo doing its own request.
export function AppInfoProvider({ children }) {
  const [appName, setAppName] = useState("Hisaab");

  useEffect(() => {
    getAppInfo()
      .then((data) => {
        if (data.app_name) {
          setAppName(data.app_name);
          document.title = data.app_name;
        }
      })
      .catch(() => {}); // keep the "Hisaab" fallback if this fails
  }, []);

  return <AppInfoContext.Provider value={{ appName }}>{children}</AppInfoContext.Provider>;
}

export function useAppInfo() {
  return useContext(AppInfoContext);
}
