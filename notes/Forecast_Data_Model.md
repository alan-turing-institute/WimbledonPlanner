# Forecast Data Model

This diagram summarises the fields in the eight main tables in the Forecast data,
and highlights where there are links to the Harvest data:

![ForecastDataModel](forecast_data_model.png)

### Assignments

Each entry defines an allocation (in seconds per day) of a person or placeholder
 (exactly one of person_id and placeholder_id are defined) to a given project
 between a start date end date.

The allocation value is fixed (if someone's allocation to a project varies during
its duration they will have multiple entries in the Assignments table for that
project.)

### Clients

Each entry defines the name of a client, which is a property of the projects.
Examples of clients include: "The Alan Turing Institute", "Hut 23", "Health",
and "Intel".

Clients also have a harvest_id to link them with their Harvest data.


### Milestones

A project can have milestone dates. We don't use this currently.

### People

One entry for each person. We have to pay for Forecast per person, currently
(April 2019) we have 26 people listed.

A person has a first name, last name, email, one or
more roles (e.g. Research Data Scientist) and several other flags which may be
useful but are currently unfilled or unused. For example:

* **Weekly capacity** - not filled so currently assume everyone is 8 hours/day,
5 days per week.
* **Archived** - boolean indicating whether a user has been archived. This seems
to be the right way to deal with people that have left but we're not making use
of it currently (possibly for some reason that we've forgotten). Archived people
don't count towards the total number of users for billing purposes.

People also have a harvest_id to link them with their Harvest data.

### Placeholders

Placeholders are treated separately to "full" users, having their own table as
 well as a separate column in the Assignments table (person_id distinct from
 placeholder_id). Forecast limits the number of placeholders to one per
 every four full users. We currently have placeholders for "Resource Required" and
 external institutes (Newcastle, Edinburgh, Birmingham, Leeds).

### Projects

One entry per project. Projects have a name, a client, a start date, and an end
date. They can also be archived and have a code (distinct from the id), e.g.
R-NATS-001 (are these Finance codes?)

There are also fields for tags and notes - we don't use these but they could be
a place to include e.g. GitHub links or general project keywords/techniques. 

Projects also have a harvest_id to link them with their Harvest data.


### Roles

Roles also have a harvest_id to link them with their Harvest data.
