CREATE TABLE role (
    slug       TEXT PRIMARY KEY,
    name_zh    TEXT NOT NULL,
    root_label TEXT NOT NULL,
    sort       INTEGER NOT NULL UNIQUE
);
INSERT INTO role (slug, name_zh, root_label, sort) VALUES
    ('agent-infra',  'Agent Infra 工程师', 'Agent Infra 工程师', 0),
    ('ai-app',       'AI 应用工程师',      'AI 应用工程师',      1),
    ('backend',      '后端工程师',         '后端工程师',         2),
    ('sre-platform', 'SRE / 平台工程师',   'SRE / 平台工程师',   3),
    ('frontend',     '前端工程师',         '前端工程师',         4),
    ('data-eng',     '数据工程师',         '数据工程师',         5);

ALTER TABLE cluster ADD COLUMN role_family TEXT REFERENCES role(slug);
CREATE INDEX idx_cluster_role ON cluster(role_family);

CREATE TABLE role_skill (
    role_family         TEXT NOT NULL REFERENCES role(slug),
    skill_id            INTEGER NOT NULL REFERENCES skill(id),
    cluster_slug        TEXT NOT NULL REFERENCES cluster(slug),
    reference_companies TEXT NOT NULL DEFAULT '[]',
    sort                INTEGER NOT NULL,
    PRIMARY KEY (role_family, skill_id)
);
CREATE INDEX idx_role_skill_skill ON role_skill(skill_id);

CREATE TABLE role_company (
    role_family TEXT NOT NULL REFERENCES role(slug),
    source_id   INTEGER NOT NULL REFERENCES source(id),
    sort        INTEGER NOT NULL,
    PRIMARY KEY (role_family, source_id)
);

-- SQLite cannot alter a UNIQUE constraint; rebuild the table (db.migrate runs this with foreign_keys off).
CREATE TABLE job_posting_new (
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
    role_family              TEXT REFERENCES role(slug),
    status                   TEXT NOT NULL DEFAULT 'open',
    UNIQUE (source_id, title, role_family)
);
INSERT INTO job_posting_new SELECT * FROM job_posting;
DROP TABLE job_posting;
ALTER TABLE job_posting_new RENAME TO job_posting;
CREATE INDEX idx_job_posting_content_hash ON job_posting(content_hash);
CREATE INDEX idx_job_posting_role ON job_posting(role_family);
