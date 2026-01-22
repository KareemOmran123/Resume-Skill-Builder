import React from "react";

const ROLES = ["Software Engineer"]; // keep simple per your screenshots/wireframe
const FOCUS = ["Backend", "Frontend", "Full Stack"];
const LOCATIONS = ["San Francisco Bay Area", "Dallas–Fort Worth", "New York City", "Seattle", "Austin"];
const LEVELS = ["Junior / New Grad"]; // keep simple per screenshot

export default function SelectFocus({ ctx }) {
  const { filters, setFilters } = ctx;

  return (
    <main className="page">
      <div className="container centerStack">
        <div className="spacer24" />

        <h1 className="h1" style={{ fontSize: "44px" }}>Select Your Focus</h1>
        <p className="subhead" style={{ fontSize: "16px" }}>
          Choose the area you’re most interested in pursuing
        </p>

        <div className="spacer32" />

        <div className="formGrid">
          <div className="field">
            <label className="label">Role</label>
            <select
              className="select"
              value={filters.role}
              onChange={(e) => setFilters({ role: e.target.value })}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="label">Focus Area</label>
            <div className="pillRow">
              {FOCUS.map((f) => {
                const active = filters.focusArea === f;
                return (
                  <button
                    key={f}
                    className={`pill ${active ? "pillActive" : ""}`}
                    onClick={() => setFilters({ focusArea: f })}
                    type="button"
                  >
                    {f}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="field">
            <label className="label">Location</label>
            <select
              className="select"
              value={filters.location}
              onChange={(e) => setFilters({ location: e.target.value })}
            >
              {LOCATIONS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="label">Level</label>
            <select
              className="select"
              value={filters.level}
              onChange={(e) => setFilters({ level: e.target.value })}
            >
              {LEVELS.map((lvl) => (
                <option key={lvl} value={lvl}>
                  {lvl}
                </option>
              ))}
            </select>
          </div>

          <div className="spacer32" />

          <button className="primaryBtn fullWidthBtn" onClick={() => ctx.go("/results")}>
            View Top Skills <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </main>
  );
}
