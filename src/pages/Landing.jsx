import React from "react";

export default function Landing({ ctx }) {
  return (
    <main className="page pageLanding">
      <div className="container">
        <section className="heroPanel centerStack">
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

          <button className="primaryBtn" onClick={() => ctx.go("/select")}>
            Select a Role <span aria-hidden="true">&rarr;</span>
          </button>

          <div className="footerNote">
            Data refreshed weekly from real junior software engineering job postings
          </div>
        </section>
      </div>
    </main>
  );
}
