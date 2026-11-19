CREATE TABLE cluster (
    slug    TEXT PRIMARY KEY,
    name_zh TEXT NOT NULL,
    color   TEXT,
    sort    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE source (
    id      INTEGER PRIMARY KEY,
    code    TEXT UNIQUE,
    name    TEXT NOT NULL,
    type    TEXT NOT NULL CHECK (type IN ('ats_api', 'scrape', 'manual')),
    url     TEXT,
    company TEXT,
    region  TEXT
);

CREATE TABLE job_posting (
    id                       INTEGER PRIMARY KEY,
    source_id                INTEGER NOT NULL REFERENCES source(id),
    company                  TEXT,
    title                    TEXT NOT NULL,
    location                 TEXT,
    url                      TEXT,
    posted_at                TEXT,
    first_seen_at            TEXT,
    fetched_at               TEXT,
    raw_text                 TEXT,
    section_responsibilities TEXT,
    section_requirements     TEXT,
    section_bonus            TEXT,
    content_hash             TEXT,
    lang                     TEXT,
    role_family              TEXT,
    status                   TEXT NOT NULL DEFAULT 'open',
    UNIQUE (source_id, title)
);
CREATE INDEX idx_job_posting_content_hash ON job_posting(content_hash);

CREATE TABLE skill (
    id                  INTEGER PRIMARY KEY,
    slug                TEXT NOT NULL UNIQUE,
    name_zh             TEXT NOT NULL,
    name_en             TEXT,
    cluster             TEXT REFERENCES cluster(slug),
    description         TEXT,
    aliases             TEXT NOT NULL DEFAULT '[]',
    concepts            TEXT NOT NULL DEFAULT '[]',
    practice            TEXT,
    reference_companies TEXT NOT NULL DEFAULT '[]',
    status              TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'proposed', 'merged')),
    merged_into         INTEGER REFERENCES skill(id),
    sort                INTEGER
);
CREATE INDEX idx_skill_cluster ON skill(cluster);

CREATE TABLE posting_skill (
    posting_id        INTEGER NOT NULL REFERENCES job_posting(id) ON DELETE CASCADE,
    skill_id          INTEGER NOT NULL REFERENCES skill(id),
    evidence_span     TEXT,
    strength          TEXT NOT NULL CHECK (strength IN ('required', 'preferred', 'bonus')),
    confidence        REAL,
    extractor_version TEXT NOT NULL,
    PRIMARY KEY (posting_id, skill_id, extractor_version)
);
CREATE INDEX idx_posting_skill_skill ON posting_skill(skill_id);

CREATE TABLE skill_edge (
    from_skill INTEGER NOT NULL REFERENCES skill(id),
    to_skill   INTEGER NOT NULL REFERENCES skill(id),
    type       TEXT NOT NULL CHECK (type IN ('prereq', 'related')),
    UNIQUE (from_skill, to_skill, type)
);
CREATE INDEX idx_skill_edge_to ON skill_edge(to_skill);

CREATE TABLE resource (
    id            INTEGER PRIMARY KEY,
    url           TEXT,
    title         TEXT NOT NULL UNIQUE,
    type          TEXT CHECK (type IN ('doc', 'paper', 'blog', 'course', 'repo')),
    lang          TEXT,
    summary       TEXT,
    quality_score REAL,
    fetched_at    TEXT,
    added_by      TEXT
);

CREATE TABLE skill_resource (
    skill_id    INTEGER NOT NULL REFERENCES skill(id),
    resource_id INTEGER NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
    rank        INTEGER,
    reason      TEXT,
    PRIMARY KEY (skill_id, resource_id)
);
CREATE INDEX idx_skill_resource_resource ON skill_resource(resource_id);

CREATE TABLE roadmap (
    id          INTEGER PRIMARY KEY,
    role_family TEXT NOT NULL,
    params      TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roadmap_step (
    id          INTEGER PRIMARY KEY,
    roadmap_id  INTEGER NOT NULL REFERENCES roadmap(id) ON DELETE CASCADE,
    phase       INTEGER NOT NULL,
    phase_title TEXT,
    step_order  INTEGER NOT NULL,
    skill_id    INTEGER NOT NULL REFERENCES skill(id),
    UNIQUE (roadmap_id, phase, step_order)
);

CREATE TABLE progress (
    skill_id   INTEGER PRIMARY KEY REFERENCES skill(id),
    status     TEXT NOT NULL,
    notes      TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
