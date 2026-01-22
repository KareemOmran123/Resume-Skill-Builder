import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function TopNav() {
  const nav = useNavigate();
  const loc = useLocation();
  const showBack = loc.pathname !== "/";

  return (
    <div className="topNav">
      <div className="container" style={{ display: "flex", alignItems: "center", gap: 14 }}>
        {showBack ? (
          <div className="secondaryLink" onClick={() => nav(-1)} role="button" tabIndex={0}>
            <span aria-hidden="true">←</span>
            <span>Back</span>
          </div>
        ) : (
          <div style={{ width: 72 }} />
        )}

        <div className="brand" style={{ marginLeft: showBack ? 0 : 0 }}>
          SkillPulse
        </div>
      </div>
    </div>
  );
}
