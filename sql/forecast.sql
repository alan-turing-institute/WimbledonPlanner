CREATE TABLE "Projects" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "code" varchar,
  "start_date" date,
  "end_date" date,
  "client_id" int,
  "harvest_id" int,
  "notes" varchar,
  "archived" bit
);

CREATE TABLE "Roles" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "harvest_role_id" int
);

CREATE TABLE "People" (
  "id" int PRIMARY KEY,
  "first_name" varchar,
  "last_name" varchar,
  "email" varchar,
  "role" int,
  "harvest_user_id" int,
  "login" bit,
  "subscribed" bit,
  "admin" bit,
  "archived" bit,
  "weekly_capacity" int,
  "working_days_monday" bit,
  "working_days_tuesday" bit,
  "working_days_wednesday" bit,
  "working_days_thursday" bit,
  "working_days_friday" bit,
  "working_days_saturday" bit,
  "working_days_sunday" bit
);

CREATE TABLE "Placeholders" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "role" int,
  "archived" bit
);

CREATE TABLE "Clients" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "harvest_id" int,
  "archived" bit
);

CREATE TABLE "Milestones" (
  "id" int PRIMARY KEY,
  "date" date,
  "project_id" int
);

CREATE TABLE "Assignments" (
  "id" int PRIMARY KEY,
  "person_id" int,
  "placeholder_id" int,
  "project_id" int,
  "start_date" date,
  "end_date" date,
  "allocation" int,
  "notes" varchar
);

ALTER TABLE "Projects" ADD FOREIGN KEY ("client_id") REFERENCES "Clients" ("id");

ALTER TABLE "Milestones" ADD FOREIGN KEY ("project_id") REFERENCES "Projects" ("id");

ALTER TABLE "Assignments" ADD FOREIGN KEY ("person_id") REFERENCES "People" ("id");

ALTER TABLE "Assignments" ADD FOREIGN KEY ("placeholder_id") REFERENCES "Placeholders" ("id");

ALTER TABLE "Assignments" ADD FOREIGN KEY ("project_id") REFERENCES "Projects" ("id");