/* ------------------------------------------------- */
/* CREATE HARVEST SCHEMA */
/* ------------------------------------------------- */
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
  "name" text
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

/* ------------------------------------------------- */
/* CREATE FORECAST SCHEMA */
/* ------------------------------------------------- */
CREATE SCHEMA forecast;

CREATE TABLE forecast.projects (
  "id" int PRIMARY KEY,
  "name" text,
  "code" text,
  "start_date" date,
  "end_date" date,
  "client_id" int,
  "harvest_id" int,
  "notes" text,
  "archived" boolean
);

CREATE TABLE forecast.roles (
  "id" int PRIMARY KEY,
  "name" text,
  "harvest_role_id" int
);

CREATE TABLE forecast.people (
  "id" int PRIMARY KEY,
  "first_name" text,
  "last_name" text,
  "email" text,
  "role" int,
  "harvest_user_id" int,
  "login" text,
  "subscribed" boolean,
  "admin" boolean,
  "archived" boolean,
  "weekly_capacity" int,
  "working_days_monday" boolean,
  "working_days_tuesday" boolean,
  "working_days_wednesday" boolean,
  "working_days_thursday" boolean,
  "working_days_friday" boolean,
  "working_days_saturday" boolean,
  "working_days_sunday" boolean
);

CREATE TABLE forecast.placeholders (
  "id" int PRIMARY KEY,
  "name" text,
  "role" int,
  "archived" boolean
);

CREATE TABLE forecast.clients (
  "id" int PRIMARY KEY,
  "name" text,
  "harvest_id" int,
  "archived" boolean
);

CREATE TABLE forecast.milestones (
  "id" int PRIMARY KEY,
  "date" date,
  "project_id" int
);

CREATE TABLE forecast.assignments (
  "id" int PRIMARY KEY,
  "person_id" int,
  "placeholder_id" int,
  "project_id" int,
  "start_date" date,
  "end_date" date,
  "allocation" int,
  "notes" text
);

ALTER TABLE forecast.projects ADD FOREIGN KEY ("client_id") REFERENCES forecast.clients ("id");
ALTER TABLE forecast.projects ADD FOREIGN KEY ("harvest_id") REFERENCES harvest.projects ("id");
ALTER TABLE forecast.people ADD FOREIGN KEY ("harvest_user_id") REFERENCES harvest.users ("id");
ALTER TABLE forecast.roles ADD FOREIGN KEY ("harvest_role_id") REFERENCES harvest.roles ("id");
ALTER TABLE forecast.clients ADD FOREIGN KEY ("harvest_id") REFERENCES harvest.clients ("id");
ALTER TABLE forecast.milestones ADD FOREIGN KEY ("project_id") REFERENCES forecast.projects ("id");
ALTER TABLE forecast.assignments ADD FOREIGN KEY ("person_id") REFERENCES forecast.people ("id");
ALTER TABLE forecast.assignments ADD FOREIGN KEY ("placeholder_id") REFERENCES forecast.placeholders ("id");
ALTER TABLE forecast.assignments ADD FOREIGN KEY ("project_id") REFERENCES forecast.projects ("id");