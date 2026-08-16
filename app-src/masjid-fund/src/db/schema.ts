/**
 * Database shape for Masjid Fund.
 *
 * Money is stored as integer minor units (cents) — never floats. Every
 * donation row carries its own currency so the ledger stays unambiguous.
 *
 * BOOTSTRAP_SQL is idempotent and runs on first boot for both drivers
 * (embedded PGlite in development, managed PostgreSQL in production).
 */
export const BOOTSTRAP_SQL = `
CREATE TABLE IF NOT EXISTS projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  name text NOT NULL,
  city text NOT NULL,
  country text NOT NULL,
  summary text NOT NULL,
  story text NOT NULL,
  status text NOT NULL DEFAULT 'planning',
  goal_cents bigint NOT NULL,
  offline_raised_cents bigint NOT NULL DEFAULT 0,
  capacity integer NOT NULL DEFAULT 0,
  zakat_eligible boolean NOT NULL DEFAULT false,
  accent text NOT NULL DEFAULT 'emerald',
  position integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_costs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  label text NOT NULL,
  detail text NOT NULL,
  unit_cost_cents bigint NOT NULL,
  position integer NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_updates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title text NOT NULL,
  body text NOT NULL,
  posted_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS donations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reference text NOT NULL UNIQUE,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  amount_cents bigint NOT NULL,
  currency text NOT NULL DEFAULT 'USD',
  frequency text NOT NULL DEFAULT 'one_time',
  intent text NOT NULL DEFAULT 'sadaqah_jariyah',
  donor_name text,
  donor_email text NOT NULL,
  anonymous boolean NOT NULL DEFAULT false,
  dedication text,
  message text,
  status text NOT NULL DEFAULT 'pending',
  provider text NOT NULL,
  provider_ref text,
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

-- Columns added after the first release. ADD COLUMN IF NOT EXISTS keeps the
-- bootstrap safe to re-run against a database that already holds donations.
ALTER TABLE donations ADD COLUMN IF NOT EXISTS manage_token text;
ALTER TABLE donations ADD COLUMN IF NOT EXISTS subscription_ref text;
ALTER TABLE donations ADD COLUMN IF NOT EXISTS cancelled_at timestamptz;
ALTER TABLE donations ADD COLUMN IF NOT EXISTS receipt_sent_at timestamptz;

CREATE TABLE IF NOT EXISTS admin_sessions (
  token text PRIMARY KEY,
  email text NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Delivery log, so support can answer "did my receipt go out?" without
-- digging through the email provider's dashboard.
CREATE TABLE IF NOT EXISTS email_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  recipient text NOT NULL,
  subject text NOT NULL,
  kind text NOT NULL,
  donation_reference text,
  status text NOT NULL,
  error text,
  provider text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Applications from communities asking for their masjid to be funded. Nothing
-- here is public until staff approve it and publish a project.
CREATE TABLE IF NOT EXISTS applications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reference text NOT NULL UNIQUE,
  status text NOT NULL DEFAULT 'submitted',
  masjid_name text NOT NULL,
  city text NOT NULL,
  country text NOT NULL,
  location_note text,
  congregation_now integer NOT NULL DEFAULT 0,
  capacity_planned integer NOT NULL DEFAULT 0,
  estimated_cost_cents bigint NOT NULL,
  already_raised_cents bigint NOT NULL DEFAULT 0,
  currency text NOT NULL DEFAULT 'USD',
  land_title_number text NOT NULL,
  land_ownership text NOT NULL,
  titled_to_trust boolean NOT NULL DEFAULT false,
  trust_name text,
  trust_registration text,
  contact_name text NOT NULL,
  contact_role text NOT NULL,
  contact_email text NOT NULL,
  contact_phone text NOT NULL,
  story text NOT NULL,
  status_note text,
  manage_token text NOT NULL UNIQUE,
  ip_hash text,
  project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  decided_at timestamptz
);

-- Supporting documents: title deed, drawings, bill of quantities and the rest.
-- Bytes live in the database so the app needs no object store to run; the
-- FileStore boundary in src/lib/files/ is where S3 or R2 would slot in.
CREATE TABLE IF NOT EXISTS application_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id uuid NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  kind text NOT NULL,
  filename text NOT NULL,
  content_type text NOT NULL,
  byte_size integer NOT NULL,
  data bytea NOT NULL,
  uploaded_at timestamptz NOT NULL DEFAULT now()
);

-- Audit trail: who moved an application to which state, and why.
CREATE TABLE IF NOT EXISTS application_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id uuid NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  actor text NOT NULL,
  action text NOT NULL,
  note text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS applications_status_idx ON applications (status);
CREATE INDEX IF NOT EXISTS application_documents_application_idx ON application_documents (application_id);
CREATE INDEX IF NOT EXISTS application_events_application_idx ON application_events (application_id);
CREATE INDEX IF NOT EXISTS donations_project_idx ON donations (project_id);
CREATE INDEX IF NOT EXISTS donations_status_idx ON donations (status);
CREATE UNIQUE INDEX IF NOT EXISTS donations_manage_token_idx ON donations (manage_token);
CREATE INDEX IF NOT EXISTS project_costs_project_idx ON project_costs (project_id);
CREATE INDEX IF NOT EXISTS project_updates_project_idx ON project_updates (project_id);
CREATE INDEX IF NOT EXISTS email_log_reference_idx ON email_log (donation_reference);
`;

/**
 * Sample building projects so the site is browsable before a real programme
 * team loads its own. Fixed UUIDs keep the seed idempotent — re-running it
 * never duplicates rows. Replace with real project data before launch.
 */
export const SEED_SQL = `
INSERT INTO projects (id, slug, name, city, country, summary, story, status, goal_cents, offline_raised_cents, capacity, zakat_eligible, accent, position) VALUES
(
  '11111111-1111-4111-8111-111111111111',
  'masjid-al-noor-garissa',
  'Masjid al-Noor',
  'Garissa',
  'Kenya',
  'A 400-capacity masjid replacing a leaking iron-sheet prayer shed that serves eleven surrounding villages.',
  'The community has prayed under corrugated iron for nine years. In the rains the floor floods and jumu''ah moves outdoors. Foundations and the ground-floor columns are complete; the fund now covers walling, roofing and the wudu block. Land was donated by the village council and titled to a local waqf trust, so the masjid can never be sold.',
  'building',
  8500000, 4125000, 400, false, 'emerald', 1
),
(
  '22222222-2222-4222-8222-222222222222',
  'baitul-rahma-kano',
  'Baitul Rahma Masjid',
  'Kano',
  'Nigeria',
  'A 750-capacity masjid with an attached madrasah of four classrooms for a fast-growing neighbourhood.',
  'The nearest masjid is a forty-minute walk, and the two hundred children studying Qur''an there sit outside in the sun. The design pairs the prayer hall with four classrooms and a small library so the building works seven days a week. Drawings are approved and the contractor is appointed; ground-breaking begins once the foundation stage is funded.',
  'planning',
  12000000, 2640000, 750, false, 'teal', 2
),
(
  '33333333-3333-4333-8333-333333333333',
  'masjid-as-salam-sylhet',
  'Masjid as-Salam',
  'Sylhet',
  'Bangladesh',
  'Rebuilding a flood-damaged masjid on a raised plinth, with a 300-capacity hall and a shelter floor above.',
  'The 2024 floods took the roof and half the walls. The rebuild sits on a 1.5 m plinth and adds an upper floor that doubles as a flood shelter for roughly 200 people. Structural work is done and the roof is on — remaining costs are finishes, the minaret and the sound system.',
  'building',
  6200000, 5890000, 300, false, 'emerald', 3
),
(
  '44444444-4444-4444-8444-444444444444',
  'masjid-al-huda-kigali',
  'Masjid al-Huda',
  'Kigali',
  'Rwanda',
  'A 500-capacity masjid with a women''s prayer hall, wudu facilities and a rainwater harvesting system.',
  'A congregation of about 600 currently rents a converted warehouse with no women''s section and no running water. The new build includes a dedicated women''s hall with its own entrance, twelve wudu stations and 20,000 litres of rainwater storage that also serves neighbouring households in the dry season.',
  'planning',
  9600000, 1280000, 500, false, 'sky', 4
),
(
  '55555555-5555-4555-8555-555555555555',
  'masjid-al-fajr-mombasa',
  'Masjid al-Fajr',
  'Mombasa',
  'Kenya',
  'Completed in 2025 — a 350-capacity masjid and community hall now open five times a day.',
  'Funded by 1,842 donors over fourteen months and handed to a local waqf board in March 2025. The masjid runs a daily maktab for 90 children and its hall hosts the neighbourhood''s nikah and janazah gatherings. Final accounts are published in the transparency report.',
  'completed',
  7400000, 7400000, 350, false, 'amber', 5
)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO project_costs (id, project_id, label, detail, unit_cost_cents, position) VALUES
('aaaaaaa1-0000-4000-8000-000000000001', '11111111-1111-4111-8111-111111111111', 'A bag of cement', 'Nine bags lay one square metre of the prayer hall floor.', 900, 1),
('aaaaaaa1-0000-4000-8000-000000000002', '11111111-1111-4111-8111-111111111111', 'One square metre of walling', 'Blocks, mortar and plaster for a finished wall.', 4500, 2),
('aaaaaaa1-0000-4000-8000-000000000003', '11111111-1111-4111-8111-111111111111', 'A roofing truss', 'One of the 38 trusses spanning the hall.', 22000, 3),
('aaaaaaa1-0000-4000-8000-000000000004', '11111111-1111-4111-8111-111111111111', 'A wudu station', 'Tap, drainage and seating for one worshipper.', 60000, 4),
('aaaaaaa2-0000-4000-8000-000000000001', '22222222-2222-4222-8222-222222222222', 'One square metre of foundation', 'Excavation, blinding and reinforced slab.', 5200, 1),
('aaaaaaa2-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222222', 'A classroom desk set', 'Bench and desk for four madrasah students.', 8000, 2),
('aaaaaaa2-0000-4000-8000-000000000003', '22222222-2222-4222-8222-222222222222', 'A full classroom', 'Walls, roof, floor and furniture for 40 students.', 950000, 3),
('aaaaaaa3-0000-4000-8000-000000000001', '33333333-3333-4333-8333-333333333333', 'A prayer mat row', 'Carpet for one full row of the hall.', 7500, 1),
('aaaaaaa3-0000-4000-8000-000000000002', '33333333-3333-4333-8333-333333333333', 'A window with flood shutters', 'Frame, glazing and storm shutters.', 31000, 2),
('aaaaaaa3-0000-4000-8000-000000000003', '33333333-3333-4333-8333-333333333333', 'The minaret and sound system', 'Speakers, amplifier and wiring for the adhan.', 480000, 3),
('aaaaaaa4-0000-4000-8000-000000000001', '44444444-4444-4444-8444-444444444444', 'A rainwater tank', 'Five thousand litres of storage with filtration.', 68000, 1),
('aaaaaaa4-0000-4000-8000-000000000002', '44444444-4444-4444-8444-444444444444', 'One square metre of the women''s hall', 'Structure and finishes for the dedicated hall.', 5800, 2),
('aaaaaaa4-0000-4000-8000-000000000003', '44444444-4444-4444-8444-444444444444', 'A wudu station', 'Tap, drainage and seating for one worshipper.', 62000, 3)
ON CONFLICT (id) DO NOTHING;

INSERT INTO project_updates (id, project_id, title, body, posted_at) VALUES
('bbbbbbb1-0000-4000-8000-000000000001', '11111111-1111-4111-8111-111111111111', 'Ground-floor columns cast', 'All 24 columns are cast and cured. The engineer''s inspection report is filed with the waqf trust. Walling starts as soon as the block order is funded.', now() - interval '18 days'),
('bbbbbbb1-0000-4000-8000-000000000002', '11111111-1111-4111-8111-111111111111', 'Block order priced', 'Three suppliers quoted; the lowest compliant bid was accepted. The saving of roughly 4% against budget stays in the project and goes to the wudu block.', now() - interval '5 days'),
('bbbbbbb3-0000-4000-8000-000000000001', '33333333-3333-4333-8333-333333333333', 'Roof complete', 'The roof sheets and ridge are fixed and the hall is watertight for the first time since the floods. Taraweeh was prayed inside this month.', now() - interval '26 days'),
('bbbbbbb3-0000-4000-8000-000000000002', '33333333-3333-4333-8333-333333333333', 'Plinth signed off', 'The flood plinth passed inspection at 1.5 m above the 2024 high-water mark.', now() - interval '9 days'),
('bbbbbbb5-0000-4000-8000-000000000001', '55555555-5555-4555-8555-555555555555', 'Handed over to the waqf board', 'Keys, title and final accounts were handed to the local waqf board. The first jumu''ah drew 410 worshippers.', now() - interval '150 days')
ON CONFLICT (id) DO NOTHING;
`;
