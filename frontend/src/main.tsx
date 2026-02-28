/**
 * Application entry point.
 *
 * Sets up the React tree:
 * 1. StrictMode -- enables extra development checks (double-renders, etc.)
 * 2. RouterProvider -- connects the data router (defined in App.tsx) to React
 *
 * Auth is handled entirely by the router's loaders and actions
 * (see App.tsx), so there's no AuthProvider wrapper needed here.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { router } from "@/App";
import "@/index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
