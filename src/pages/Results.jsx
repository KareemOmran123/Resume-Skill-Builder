import React, { useEffect, useState } from "react";
import { fetchSkillsFor } from "../api/skillsApi.js";

function ProgressBar({ pct }) {
  return (
    <div className="progressTrack" aria-label={`Appears in ${pct}% of postings`}>
      <div className="progressFill" style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function Results({ ctx }) {
  const { filters } = ctx;
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    async function loadSkills() {
      setLoading(true);
      setError(null);

      try {
        const nextDataset = await fetchSkillsFor(filters);
        if (active) {
          setDataset(nextDataset);
        }
      } catch (err) {
        if (active) {
          setError(err);
          setDataset(null);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadSkills();

    return () => {
      active = false;
    };
  }, [filters]);

  const skills = dataset?.skills ?? [];
  const postingsCount = dataset?.totals?.postings_count ?? 0;
  const companiesCount = dataset?.totals?.unique_companies_count ?? 0;

  return (
    <main className="page pageResults">
      <div className="container">
        <header className="resultsHeader">
          <h2 className="h2">{dataset?.title ?? "Top Skills"}</h2>
          <p className="meta">
            {loading ? "Loading current skill insights..." : dataset?.subtitle ?? "No skill insight data loaded."}
          </p>
          {!loading && !error && dataset ? (
            <p className="meta">
              {postingsCount} postings analyzed from {companiesCount} companies
            </p>
          ) : null}
        </header>

        <section className="card">
          <div className="cardPad">
            <p className="cardTitle">Top 5 In-Demand Skills</p>
          </div>
          <div className="hr" />

          {loading ? (
            <div className="cardPad noteText">Loading skill insights...</div>
          ) : error ? (
            <div className="cardPad noteText">Unable to load skill insights. Make sure the backend API is running.</div>
          ) : skills.length === 0 ? (
            <div className="cardPad noteText">No skills found for these filters yet.</div>
          ) : (
            skills.map((s, i) => (
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

                {i !== skills.length - 1 ? <div className="hr" /> : null}
              </React.Fragment>
            ))
          )}
        </section>

        <section className="card cardNote">
          <div className="cardPad noteText">
            These insights are compiled from broad junior software engineering postings in the selected scope.
            Skills are ranked by frequency of appearance across all analyzed postings.
          </div>
        </section>
      </div>
    </main>
  );
}
