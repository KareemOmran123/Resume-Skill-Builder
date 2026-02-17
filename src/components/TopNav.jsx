import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function TopNav() {
  const nav = useNavigate();
  const loc = useLocation();
  const showBack = loc.pathname !== "/";

  return (
    <header className="topNav">
      <div className="container topNavInner">
        {showBack ? (
          <button className="secondaryLink" onClick={() => nav(-1)} type="button">
            <span aria-hidden="true">&larr;</span>
            <span>Back</span>
          </button>
        ) : (
          <div className="navBackPlaceholder" aria-hidden="true" />
        )}

        <div className="brandWrap">
          <span className="brandDot" aria-hidden="true" />
          <div className="brand">SkillPulse</div>
        </div>
      </div>
    </header>
  );
}
