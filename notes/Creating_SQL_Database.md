# Creating a SQL Database for Harvest & Forecast

**Current status:**

* Created an Azure PostgreSQL database in Jack's local subscription.

* Defined the Harvest and Forecast schemas on it in a database called "Wimbledon" using pure SQL.

* Imported data to the SQL database from CSV files using `python`, `pandas` and `SQLAlchemy`.

**TODO:**

* Refactor/document code.

* Import data to the database directly from the Harvest and Forecast APIs (without CSV step).
  * Amaani found https://www.singer.io/, https://github.com/singer-io/tap-harvest and https://github.com/singer-io/tap-harvest-forecast which may be useful for this.
  
* Add functionality to create visualisations via the SQL database rather than from the CSVs.

* Make a local SQL database rather than an Azure one.

* Make an Azure database in the REG subscription and figure out how to deal with authentication etc.

* Figure out how to build Azure database reproducibly. Believe clean air project is using https://www.terraform.io/ to help with this, and
investigating Kubernetes/Helm.

## Creating a PostgreSQL Server on Azure

Go to https://portal.azure.com and login, then perform the steps below.

Create a resource group for the database:
1) Click Resource Groups
2) Create a Resource Group
3) Give a name
4) Review & Create

Create a PostgreSQL server in the resource group:
1) Go to "Azure Database for PostgreSQL servers" (search at top)
2) Click Add
3) Give server a name
4) Pick subscription and resource group
5) Enter admin login name (**can't be changed later!**)
6) Enter admin password (can be changed)
7) Select pricing tier - configure - probably pick basic unless good reason not to (but can't change pricing tier later, can only customise within tier)
8) Click Ok
9) Click Create
10) Wait for deployment to finish (can check in notifications via bell in menu bar at top)

Modify connection security rules:
1) Go to Resource groups - select group you created - select database you created
2) Go to Connection security
3) Add IP addresses you want to be able to connect from (e.g. google what's my IP address whilst at the Turing)
4) Click Save

## Local PostgreSQL Setup

To install PostgreSQL and associated command line tools:
```bash
> brew install postgresql
```

To connect to the Azure PostgreSQL server you can run:
```bash
> psql --host=<SERVER-NAME>.postgres.database.azure.com --port=5432 --username=<USERNAME>@<SERVER-NAME> --dbname=postgres
```
This will prompt for your (admin) password and then connect to the `postgres` database on the server - from here you
can run SQL commands to create other databases, tables etc.

To avoid having to enter your password every time, it can be entered in the file `~/.pgpass`:
1) Create the file `~/.pgpass`
2) Insert the following line: `<SERVER-NAME>.postgres.database.azure.com:*:*:<USERNAME>@<SERVER-NAME>:<PASSWORD>`
3) Save the file.
4) Change the permissions of the file with `chmod 0600 ~/.pgpass` (disallow access to world or group)

Now you should not be prompted for your password when running `psql` to connect to the server.

Presumably all the above can easily be changed to point at a local PostgreSQL database instead, but I haven't tried this yet.

## Creating the Data Schema on the Server

The bash script `sql/create_schema.sh` does the following:

1) Creates a database called `wimbledon-planner` on the server using the `createdb` command.
2) Runs the SQL file `sql/schema.sql` on the server to create Forecast and Harvest tables and the relationships between them,
mimicking the Forecast/Harvest data models.

 The web tool https://dbdiagram.io was very useful to help creating the schema.sql file (and to make pretty data model 
 diagrams). For example:
 * Forecast: https://dbdiagram.io/d/5cbf2115f7c5bb70c72fba4b
 * Harvest: https://dbdiagram.io/d/5cb5a0b0f7c5bb70c72fa5c9

The diagrams can be exported to PDF, MySQL or PostgreSQL - most of the `sql/schema.sql` was created via a PostgreSQL
export from dbdiagram.

## Putting Data on the Server

The Jupyter notebook `sql/SQLAlchemy.ipynb` loads the Harvest and Forecast data from the CSV files created from the
Harvest/Forecast APIs by the scripts in `api/`, and then inserts them to the appropriate tables in the PostgreSQL 
database using a mixture of `pandas` and `SQLAlchemy`.

Caveats:
* Some data wrangling needed to get rid of columns not ported to the SQL database and to ensure correct data types.
In particular, I'm using a new pandas feature (as of version 0.24) which allows integer columns with missing values (NaNs)
to avoid any ID columns being converted to floats.
* The order of populating the tables matters - tables that reference a value in another table must be filled after the
parent table (otherwise you'll get a PostgreSQL error about a missing reference/similar.)
* This is a one run only script. If you run it again nothing will happen because you'll get errors about IDs not being
unique (i.e. it tries to add the same rows into the table but can't because the primary keys already exist). To get around
this you can run the `delete_db.sh` script and then `create_schema.sh` to delete and then recreate the table schema.
* Still relies on CSV files.

## Azure Data Studio

To have a quick look at the status of the server (e.g. the databases, tables and data it contains) Azure Data Studio is
quite useful, available here (or from the Turing Self Service App): 
https://docs.microsoft.com/en-us/sql/azure-data-studio/download?view=sql-server-2017

To connect:
1) Open Azure Data Studio
2) Open Extensions tab (square one at the bottom on the left)
3) Search for and install PostgreSQL
4) Open Connections tab (rectangular one top left)
5) Create a new connection (hover over "SERVERS" then it's the first icon to the right)
6) Choose connection type "PostgreSQL"
7) Enter your server name of the form <database-name>.postgres.database.azure.come (can get this from the Azure portal)
8) Enter your admin username of the form <username>@<server-name> (can get this from the Azure portal)
9) Enter your admin password (can change this from the Azure portal if your forgot it)
10) You should now be able to browse through the server from the connections tab. 
You can also run SQL queries from Azure data studio to see some of the data etc.
