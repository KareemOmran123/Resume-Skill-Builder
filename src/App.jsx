import React, { useMemo, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import TopNav from "./components/TopNav.jsx";
import Landing from "./pages/Landing.jsx";
import SelectFocus from "./pages/SelectFocus.jsx";
import Results from "./pages/Results.jsx";

export default function App() {
  const navigate = useNavigate();

  const [filters, setFilters] = useState({
    role: "Software Engineer",
    focusArea: "Backend",
    location: "San Francisco Bay Area",
    level: "Junior / New Grad",
  });

  const ctx = useMemo(
    () => ({
      filters,
      setFilters: (patch) => setFilters((prev) => ({ ...prev, ...patch })),
      go: (path) => navigate(path),
    }),
    [filters, navigate]
  );

  return (
    <div className="appShell">
      <TopNav />
      <Routes>
        <Route path="/" element={<Landing ctx={ctx} />} />
        <Route path="/select" element={<SelectFocus ctx={ctx} />} />
        <Route path="/results" element={<Results ctx={ctx} />} />
      </Routes>
    </div>
  );
}
