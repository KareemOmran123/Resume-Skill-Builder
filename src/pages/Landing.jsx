import React from "react";

export default function Landing({ ctx }) {
  return (
    <main className="page">
      <div className="container centerStack">
        <div className="spacer32" />

        <h1 className="h1">
          See the Top Skills Employers Want for
          <br />
          Junior Software Engineers
        </h1>

        <p className="subhead">
          Get fast, clear insights based on real job postings from the last 30 days.
          <br />
          Know exactly which hard skills matter most for your next role.
        </p>

        <div className="spacer40" />

        <button className="primaryBtn" onClick={() => ctx.go("/select")}>
          Select a Role <span aria-hidden="true">→</span>
        </button>

        <div className="footerNote">
          Data refreshed weekly from real junior software engineering job postings
        </div>
      </div>
    </main>
  );
}
