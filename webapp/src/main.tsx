import { setupIonicReact } from "@ionic/react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@ionic/react/css/core.css";
import "@ionic/react/css/normalize.css";
import "@ionic/react/css/structure.css";
import "@ionic/react/css/typography.css";
import "@ionic/react/css/padding.css";
import "./theme/variables.css";

import { App } from "./app/App";

setupIonicReact();

const root = document.getElementById("root");
if (root === null) {
  throw new Error("No existe el elemento #root");
}
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
