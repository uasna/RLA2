import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

const root = document.getElementById("root");

if (!root) {
  document.body.innerHTML = "NO EXISTE #root";
} else {
  createRoot(root).render(
    React.createElement(
      React.StrictMode,
      null,
      React.createElement(App)
    )
  );
}