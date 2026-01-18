# SkillPulse — Sprint 0 Ground Truth (Job Postings)

This README captures **Sprint 0 findings** for SkillPulse: title patterns, role keywords, where skills appear in postings, an initial hard-skill inventory, and known noise terms to exclude.

---

## 1) Entry-Level Title Patterns (Include)

### Seniority / Level Tokens
Use these to match *entry-level / junior / new-grad* roles:

- `new grad`, `graduate`, `university grad`, `early career`
- `entry level`, `entry-level`
- `junior`, `jr`
- `associate`
- `I`, `1`, `L1`, `level 1`

### Years-of-Experience Patterns
Common “entry/junior-ish” ranges found in postings:

- `0-2 years`
- `1-3 years`
- `2-3 years`

---

## 2) Senior Titles to Exclude (Default)

Exclude postings containing these (unless the user explicitly wants senior roles):

- `senior`, `sr`
- `lead`
- `staff`
- `principal`
- `architect`
- `manager`
- `director`

---

## 3) Role Classification Keywords

### Backend (Include Keywords)
**Role terms:**
- `backend`, `back end`
- `server-side`
- `platform`
- `api`, `services`, `microservices`

**Infra / operations:**
- `cloud`, `aws`
- `devops`, `devsecops`
- `sre`, `reliability`

**Stack hints:**
- `java`
- `spring`, `spring boot`
- `hibernate`, `jpa`
- `sql`
- `postgres`, `oracle`

---

### Frontend (Include Keywords)
**Role terms:**
- `frontend`, `front end`
- `ui`, `web`
- `client-side`

**Stack hints:**
- `react`
- `typescript`, `javascript`
- `html`, `css`
- `angular`
- `next.js`

---

### Full Stack (Include Keywords)
**Role terms:**
- `full stack`, `full-stack`

**Common phrasing signals:**
- “fluently code as a full stack developer”
- “work across the stack”
- “both sides” language

**Combination hints:**
- `react + (java/spring)`
- `react + node`

---

## 4) Where Skills Appear in Job Postings

### Best Extraction Targets (Most Common Sections)
- **Responsibilities / What you’ll do**  
  (skills embedded in verbs + tech nouns)
- **Basic Qualifications / Required Experience**  
  (usually clean bullet lists; often includes years)
- **Preferred Qualifications / Nice to have**  
  (often “plus” items like DBs, cloud, tooling)

### Board-Generated “Skills” Fields (Use Carefully)
- **Built In**: often shows a **“Top Skills:”** list  
  (useful but not always complete)
- **Dice**: often shows a **“Skills”** list mixing hard skills + soft skills + tag noise  
  (do **not** treat as ground truth without validating in the body)

### Variability Notes (Important for Later Extraction)
- Skills show up as:
  - bullet lists
  - comma-separated stacks
  - buried in paragraphs
- Posts may list `REST`, `SOAP`, and `API` separately  
  → normalization needed
- “Junior” labels can still require `2–3 years`  
  → title seniority ≠ true seniority

---

## 5) Raw Hard-Skills Inventory (v1)

### Languages
- Python
- Java
- JavaScript, TypeScript
- SQL
- C, C++, C#, Go (GoLang)
- HTML, CSS
- Shell scripting

### Frameworks / Libraries
- Spring Framework, Spring Boot
- Hibernate, JPA
- React, React Native
- Angular
- Next.js

### APIs / Architecture Keywords (Countable Skills)
- REST, SOAP, Web Services
- Microservices
- CI/CD
- DevOps / DevSecOps

### Cloud / DevOps Tooling
- AWS (general)
- AWS services: S3, SQS, RDS/Aurora, ECS, Lambda, SNS, ELB/ALB
- Docker
- Terraform, Ansible
- GitHub Actions, GitLab

### Databases
- PostgreSQL, Oracle
- MySQL
- DynamoDB, MongoDB

### Dev Tools / IDEs / Version Control
- Git
- SVN / TortoiseSVN
- Eclipse, NetBeans, Visual Studio

### Testing / Performance / Security
- JMeter
- Vulnerability assessment / application security testing (as explicitly stated)
- Observability tools (e.g., Splunk)

---

## 6) Skill Noise List (Exclude From Hard-Skill Counting)

These terms commonly appear in “skills” tags or generic phrasing, but should **not** be counted as hard skills:

### Soft Skills
- collaboration
- communication
- problem solving
- accountability
- writing

### Vague Concepts
- customer experience
- scalability
- reliability
- focus

### HR / Compliance / Location / Industry Tags
- recruiting
- immigration
- policies and procedures
- security clearance (not a skill)
- industry tags like finance, health care

---

## Notes for Next Sprints (Quick Reminders)
- Sprint 1: ingestion should retain section headers where possible (helps extraction)
- Sprint 2: normalize synonyms (e.g., `React.js` → `React`, `NodeJS` → `Node.js`)
- Sprint 3: compute prevalence using **# of postings containing skill** / **total postings in cohort**
