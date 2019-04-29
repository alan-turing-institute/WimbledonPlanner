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

ALTER TABLE forecast.people ADD FOREIGN KEY ("harvest_user_id") REFERENCES forecast.users ("id");

ALTER TABLE forecast.roles ADD FOREIGN KEY ("harvest_role_id") REFERENCES harvest.roles ("id");

ALTER TABLE forecast.clients ADD FOREIGN KEY ("harvest_id") REFERENCES harvest.clients ("id");

ALTER TABLE forecast.milestones ADD FOREIGN KEY ("project_id") REFERENCES forecast.projects ("id");

ALTER TABLE forecast.assignments ADD FOREIGN KEY ("person_id") REFERENCES forecast.people ("id");

ALTER TABLE forecast.assignments ADD FOREIGN KEY ("placeholder_id") REFERENCES forecast.placeholders ("id");

ALTER TABLE forecast.assignments ADD FOREIGN KEY ("project_id") REFERENCES forecast.projects ("id");