import React, { useMemo } from "react";
import { getSkillsFor } from "../data/skills.js";

function ProgressBar({ pct }) {
  return (
    <div className="progressTrack" aria-label={`Appears in ${pct}% of postings`}>
      <div className="progressFill" style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function Results({ ctx }) {
  const { filters } = ctx;
  const dataset = useMemo(() => getSkillsFor(filters), [filters]);

  return (
    <main className="page pageResults">
      <div className="container">
        <header className="resultsHeader">
          <h2 className="h2">{dataset.title}</h2>
          <p className="meta">{dataset.subtitle}</p>
        </header>

        <section className="card">
          <div className="cardPad">
            <p className="cardTitle">Top 5 In-Demand Skills</p>
          </div>
          <div className="hr" />

          {dataset.skills.map((s, i) => (
            <React.Fragment key={s.name}>
              <div className="skillRow">
                <div className="skillIdx">{i + 1}</div>

                <div className="skillMain">
                  <p className="skillName">{s.name}</p>
                  <div className="skillSub">Appears in {s.pct}% of postings</div>
                  <ProgressBar pct={s.pct} />
                </div>

                <div className="skillPct">{s.pct}%</div>
              </div>

              {i !== dataset.skills.length - 1 ? <div className="hr" /> : null}
            </React.Fragment>
          ))}
        </section>

        <section className="card cardNote">
          <div className="cardPad noteText">
            These insights are compiled from real job postings for junior software engineering roles.
            Skills are ranked by frequency of appearance across all analyzed postings.
          </div>
        </section>
      </div>
    </main>
  );
}
