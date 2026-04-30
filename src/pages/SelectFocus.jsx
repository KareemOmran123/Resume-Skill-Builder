import React, { useEffect, useMemo, useState } from "react";
import { fetchAvailableLocations } from "../api/skillsApi.js";

const ROLES = ["Software Engineer"];
const FALLBACK_LOCATIONS = ["United States"];
const LEVELS = ["Junior / New Grad"];

export default function SelectFocus({ ctx }) {
  const { filters, setFilters } = ctx;
  const [locations, setLocations] = useState(FALLBACK_LOCATIONS);

  useEffect(() => {
    let isMounted = true;

    fetchAvailableLocations()
      .then((available) => {
        if (!isMounted) return;
        setLocations(available.length > 0 ? available : FALLBACK_LOCATIONS);
      })
      .catch(() => {
        if (isMounted) setLocations(FALLBACK_LOCATIONS);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const locationOptions = useMemo(() => {
    if (locations.includes(filters.location)) return locations;
    return [filters.location, ...locations].filter(Boolean);
  }, [filters.location, locations]);

  return (
    <main className="page pageForm">
      <div className="container centerStack">
        <header className="pageIntro">
          <h1 className="h1 h1Compact">Select Your Scope</h1>
          <p className="subhead subheadCompact">Analyze junior software engineering skills across US-wide or local postings</p>
        </header>

        <section className="formCard">
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
              <label className="label">Scope</label>
              <select
                className="select"
                value={filters.location}
                onChange={(e) => setFilters({ location: e.target.value })}
              >
                {locationOptions.map((l) => (
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

            <button className="primaryBtn fullWidthBtn" onClick={() => ctx.go("/results")}>
              View Software Engineer Skills <span aria-hidden="true">&rarr;</span>
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
