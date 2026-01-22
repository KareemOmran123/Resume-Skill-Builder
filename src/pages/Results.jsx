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
    <main className="page">
      <div className="container">
        <div className="resultsHeader">
          <h2 className="h2">{dataset.title}</h2>
          <p className="meta">{dataset.subtitle}</p>
        </div>

        <div className="card" style={{ margin: "0 auto" }}>
          <div className="cardPad">
            <p className="cardTitle">Top 5 In-Demand Skills</p>
          </div>
          <div className="hr" />

          {dataset.skills.map((s, i) => (
            <React.Fragment key={s.name}>
              <div className="skillRow">
                <div className="skillIdx">{i + 1}</div>

                <div>
                  <p className="skillName">{s.name}</p>
                  <div className="skillSub">Appears in {s.pct}% of postings</div>
                  <ProgressBar pct={s.pct} />
                </div>

                <div className="skillPct">{s.pct}%</div>
              </div>

              {i !== dataset.skills.length - 1 ? <div className="hr" /> : null}
            </React.Fragment>
          ))}
        </div>

        <div className="card" style={{ margin: "18px auto 0", maxWidth: 760 }}>
          <div className="cardPad" style={{ color: "#556070", lineHeight: 1.6, fontSize: 14 }}>
            These insights are compiled from real job postings for junior software engineering roles.
            Skills are ranked by frequency of appearance across all analyzed postings.
          </div>
        </div>
      </div>
    </main>
  );
}
