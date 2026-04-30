export const API_BASE_URL = "http://127.0.0.1:8000";

const LEVEL_MAP = {
  "Junior / New Grad": "entry",
};

export async function fetchSkillsFor(filters) {
  const params = new URLSearchParams({
    location: filters.location ?? "United States",
    role: "any",
    level: LEVEL_MAP[filters.level] ?? "entry",
    days: "30",
    top: "5",
  });

  const response = await fetch(`${API_BASE_URL}/api/skills?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch skills: ${response.status}`);
  }

  return response.json();
}

export async function fetchAvailableLocations() {
  const params = new URLSearchParams({
    days: "30",
    limit: "100",
  });

  const response = await fetch(`${API_BASE_URL}/api/locations?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch locations: ${response.status}`);
  }

  const payload = await response.json();
  return Array.isArray(payload.locations) ? payload.locations : ["United States"];
}
