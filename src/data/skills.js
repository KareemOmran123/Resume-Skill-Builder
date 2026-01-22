export const SKILLSETS = {
  "Software Engineer|Backend|San Francisco Bay Area|Junior / New Grad": {
    title: "Junior Backend Software Engineer",
    subtitle: "Based on 312 job postings in San Francisco Bay Area from the last 30 days",
    skills: [
      { name: "Python", pct: 68 },
      { name: "SQL / Databases", pct: 64 },
      { name: "REST APIs", pct: 59 },
      { name: "Git / Version Control", pct: 52 },
      { name: "Docker / Containers", pct: 43 },
    ],
  },

  // fallback set for any other selection
  "__DEFAULT__": {
    title: "Junior Software Engineer",
    subtitle: "Based on recent junior software engineering job postings from the last 30 days",
    skills: [
      { name: "Git / Version Control", pct: 55 },
      { name: "REST APIs", pct: 51 },
      { name: "SQL / Databases", pct: 49 },
      { name: "Testing (Unit / Integration)", pct: 44 },
      { name: "Docker / Containers", pct: 38 },
    ],
  },
};

export function getSkillsFor(filters) {
  const key = `${filters.role}|${filters.focusArea}|${filters.location}|${filters.level}`;
  return SKILLSETS[key] ?? SKILLSETS["__DEFAULT__"];
}
