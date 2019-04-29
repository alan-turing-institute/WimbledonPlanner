CREATE SCHEMA harvest;

CREATE TABLE harvest.projects (
  "id" int PRIMARY KEY,
  "name" text,
  "budget" float,
  "code" text,
  "starts_on" date,
  "ends_on" date,
  "client_id" int,
  "notes" text,
  "is_active" boolean
);

CREATE TABLE harvest.roles (
  "id" int PRIMARY KEY,
  "name" text,
);

CREATE TABLE harvest.users (
  "id" int PRIMARY KEY,
  "first_name" text,
  "last_name" text,
  "email" text,
  "role" int,
  "weekly_capacity" int,
  "is_active" boolean,
  "is_project_manager" boolean,
  "is_contractor" boolean
);

CREATE TABLE harvest.clients (
  "id" int PRIMARY KEY,
  "name" text,
  "is_active" boolean
);

CREATE TABLE harvest.tasks (
  "id" int PRIMARY KEY,
  "name" text,
  "is_active" boolean
);

CREATE TABLE harvest.time_entries (
  "id" int PRIMARY KEY,
  "user_id" int,
  "project_id" int,
  "task_id" int,
  "spent_date" date,
  "hours" float,
  "notes" text
);

CREATE TABLE harvest.user_assignments (
  "id" int PRIMARY KEY,
  "user_id" int,
  "project_id" int,
  "is_active" boolean,
  "is_project_manager" boolean
);

CREATE TABLE harvest.task_assignments (
  "id" int PRIMARY KEY,
  "project_id" int,
  "task_id" int
);

ALTER TABLE harvest.projects ADD FOREIGN KEY ("client_id") REFERENCES harvest.clients ("id");

ALTER TABLE harvest.users ADD FOREIGN KEY ("role") REFERENCES harvest.roles ("id");

ALTER TABLE harvest.time_entries ADD FOREIGN KEY ("user_id") REFERENCES harvest.users ("id");

ALTER TABLE harvest.time_entries ADD FOREIGN KEY ("project_id") REFERENCES harvest.projects ("id");

ALTER TABLE harvest.time_entries ADD FOREIGN KEY ("task_id") REFERENCES harvest.tasks ("id");

ALTER TABLE harvest.user_assignments ADD FOREIGN KEY ("user_id") REFERENCES harvest.users ("id");

ALTER TABLE harvest.user_assignments ADD FOREIGN KEY ("project_id") REFERENCES harvest.projects ("id");

ALTER TABLE harvest.task_assignments ADD FOREIGN KEY ("project_id") REFERENCES harvest.projects ("id");

ALTER TABLE harvest.task_assignments ADD FOREIGN KEY ("task_id") REFERENCES harvest.tasks ("id");