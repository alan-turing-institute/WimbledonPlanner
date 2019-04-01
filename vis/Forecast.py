import pandas as pd


class Forecast:

    def __init__(self):
        self.people, self.projects, self.placeholders, self.assignments, self.date_range = self.load_data()

        self.people_allocations, self.people_totals = self.get_allocations('person_id')
        self.project_allocations, self.project_totals = self.get_allocations('project_id')
        self.placeholder_allocations, self.placeholder_totals = self.get_allocations('placeholder_id')

        self.project_reqs, self.project_netalloc = self.get_project_required()

    def load_data(self):
        people = pd.read_csv('../data/forecast/people.csv',
                             index_col='id',
                             parse_dates=['updated_at'],
                             infer_datetime_format=True)

        # assign missing capacities as 6.4 hour days, 5 days per week
        people['weekly_capacity'].fillna(6.4 * 5 * 60 * 60, inplace=True)

        # convert capacity into FTE at 6.4 hrs/day
        people['weekly_capacity'] = people['weekly_capacity'] / (6.4 * 5 * 60 * 60)

        # remove project managers
        people = people[people.roles != "['Research Project Manager']"]

        # manually remove misc cases
        people = people[people.first_name != 'Joel']
        people = people[people.first_name != 'Angus']
        people = people[people.first_name != 'Amaani']

        projects = pd.read_csv('../data/forecast/projects.csv',
                               index_col='id',
                               parse_dates=['updated_at', 'start_date', 'end_date'],
                               infer_datetime_format=True)

        placeholders = pd.read_csv('../data/forecast/placeholders.csv',
                                   index_col='id',
                                   parse_dates=['updated_at'],
                                   infer_datetime_format=True)

        assignments = pd.read_csv('../data/forecast/assignments.csv',
                                  index_col='id',
                                  parse_dates=['start_date', 'end_date', 'updated_at'],
                                  infer_datetime_format=True)

        # convert assignments in seconds per day to fractions of 6.4 hour days
        assignments['allocation'] = assignments['allocation'] / (6.4 * 60 * 60)

        # Find the earliest and latest date in the data
        date_range = pd.date_range(start=assignments['start_date'].min(),
                                   end=assignments['end_date'].max(),
                                   freq='D')

        return people, projects, placeholders, assignments, date_range

    def get_person_name(self, person_id):
        """Get the full name of someone from their person_id"""
        return self.people.loc[person_id, 'first_name'] + ' ' + self.people.loc[person_id, 'last_name']

    def get_person_id(self, first_name, last_name=None):
        """Get the person_id of someone from their first_name and last_name."""
        if last_name is None:
            person_id = self.people.loc[(self.people['first_name'] == first_name)]

            if len(person_id) != 1:
                raise ValueError('Could not unique person with name ' + first_name)

        else:
            person_id = self.people.loc[(self.people['first_name'] == first_name) & (self.people['last_name'] == last_name)]

            if len(person_id) != 1:
                raise ValueError('Could not unique person with name ' + first_name + ' ' + last_name)

        return person_id.index[0]

    def get_project_name(self, project_id):
        """Get the name of a project from its project_id"""
        return self.projects.loc[project_id, 'name']

    def get_project_id(self, project_name):
        """Get the id of a project from its name"""
        return self.projects.index[self.projects.name == project_name][0]

    def get_placeholder_name(self, placeholder_id):
        """Get the name of a placeholder from its id"""
        return self.placeholders.loc[placeholder_id, 'name']

    def get_placeholder_id(self, placeholder_name):
        """Get the id of a placeholder from its name"""
        return self.placeholders.index[self.placeholders.name == placeholder_name][0]

    def get_name(self, id_value, id_type):
        """Get the name of an id based on the type of id it is. id_type can be
        'person_id', 'project_id' or 'placeholder_id'"""
        if id_type == 'person_id':
            return self.get_person_name(id_value)
        elif id_type == 'project_id':
            return self.get_project_name(id_value)
        elif id_type == 'placeholder_id':
            return self.get_placeholder_name(id_value)
        else:
            raise ValueError('id_type must be person_id, project_id or placeholder_id')

    def select_date_range(self, df, start_date, end_date, drop_zero_cols=True):
        """Extract a range of dates from a dataframe with a datetime index,
        then remove any columns which are left empty (full of zeros)."""
        mask = (df.index >= start_date) & (df.index <= end_date)
        df_slice = df.loc[mask]

        if drop_zero_cols:
            nonzero_cols = df_slice.columns[df_slice.sum() != 0]
            df_slice = df_slice[nonzero_cols]

        return df_slice

    def get_allocations(self, id_column):
        """For each unique value in id_column, create a dataframe where the rows are dates,
        the columns are projects/people/placeholders depending on id_column, and the values are
        time allocations for that date. id_column can be 'person_id', 'project_id', or 'placeholder_id'."""
        if id_column == 'person_id':
            grouped_allocations = self.assignments.groupby(
                ['person_id', 'project_id', 'start_date', 'end_date']).allocation.sum()
            id_values = self.people.index
            ref_column = 'project_id'

        elif id_column == 'project_id':
            grouped_allocations = self.assignments.groupby(
                ['project_id', 'person_id', 'start_date', 'end_date']).allocation.sum()
            id_values = self.projects.index
            ref_column = 'person_id'

        elif id_column == 'placeholder_id':
            grouped_allocations = self.assignments.groupby(
                ['placeholder_id', 'project_id', 'start_date', 'end_date']).allocation.sum()
            id_values = self.placeholders.index
            ref_column = 'project_id'

        else:
            raise ValueError('id_column must be person_id, project_id or placeholder_id')

        allocations = {}

        for idx in id_values:
            # check whether the this id has any assignments, i.e. whether the id
            # exists in the index (get_level_values to deal with MultiIndex)
            if idx in grouped_allocations.index.get_level_values(0):
                # get the allocations
                id_allocs = grouped_allocations.loc[idx]

                # unstack the MultiIndex
                id_allocs = id_allocs.reset_index()

                # Initialise dataframe to store results
                id_alloc_days = pd.DataFrame(index=self.date_range, columns=id_allocs[ref_column].unique())
                id_alloc_days.fillna(0, inplace=True)

                # Loop over each assignment
                for _, row in id_allocs.iterrows():
                    # Create the range of dates that this assignment corresponds to, with daily frequency
                    dates = pd.date_range(start=row['start_date'], end=row['end_date'], freq='D')

                    # Add the allocation to the corresponding project for the range of dates.
                    id_alloc_days.loc[dates, row[ref_column]] += row['allocation']

            else:
                # no projects, just make an empty dataframe
                id_alloc_days = pd.DataFrame(index=self.date_range)

            # Add the person's name as a label - just nice for printing later.
            id_alloc_days.columns.name = self.get_name(idx, id_column)

            allocations[idx] = id_alloc_days

        # total assignment each day
        totals = pd.DataFrame(index=self.date_range, columns=id_values)
        for idx in allocations.keys():
            totals[idx] = allocations[idx].sum(axis=1)

        return allocations, totals

    def get_project_required(self):
        """Get amount of additional resource that needs to be required over time, i.e. difference between
        project requirements and project allocations."""
        # Project requirements = Project assignments + Resource required assignments
        project_reqs = self.project_totals.copy()

        # add resource req info from placeholders
        resource_req_ids = self.placeholders[self.placeholders.name.str.lower().str.contains('resource required')].index

        for idx in resource_req_ids:
            allocs = self.placeholder_allocations[idx]

            for col in allocs.columns:
                project_reqs[col] += allocs[col]

        project_netalloc = project_reqs - self.project_totals

        return project_reqs, project_netalloc

    def spreadsheet_sheet(self, key_type, start_date, end_date, freq):
        """Create a spreadsheet style dataframe with the rows being key_type (project_id or person_id), the columns
        dates and the cell values being either a person or project and their time allocation, sorted by time allocation."""

        if key_type == 'project_id':
            data_dict = self.project_allocations
            mask = (self.project_netalloc.index >= start_date) & (self.project_netalloc.index <= end_date)
            resreq = self.project_netalloc.loc[mask]

        elif key_type == 'person_id':
            data_dict = self.people_allocations

        else:
            return ValueError('key type must be person_id or project_id')

        sheet = {}

        # set of unique project names used for cell colouring later
        names = set()

        # for each project
        for key in data_dict.keys():

            # get the projects's person allocations
            df = data_dict[key].copy()

            # extract the date range of interest
            df = self.select_date_range(df, start_date, end_date)

            # check there are project allocations to display
            rows, cols = df.shape
            if rows > 0 and cols > 0:

                # replace ids with names. for project id: include resource required.
                if key_type == 'project_id':
                    df.columns = [self.get_person_name(person_id) for person_id in df.columns]
                    df.columns.name = self.get_project_name(key)
                    df['RESOURCE REQUIRED'] = resreq[key]

                elif key_type == 'person_id':
                    df.columns = [self.get_project_name(project_id) for project_id in df.columns]
                    df.columns.name = self.get_person_name(key)

                else:
                    return ValueError('key type must be person_id or project_id')

                # update the set of names
                [names.add(col) for col in df.columns]

                # resample the data to the given date frequency
                df = df.resample(freq).mean()

                # max number items assigned to this key at a time
                n_columns = (df > 0).sum(axis=1).max()

                # initialise data frame to store projects/people ranked by time assignment
                df_ranked = pd.DataFrame(index=df.index, columns=range(1, n_columns + 1))

                # for each date period
                for date in df_ranked.index:

                    # rank the items for this date period by time allocation
                    sorted_df = df.loc[date, df.loc[date] > 0].sort_values(ascending=False)

                    if len(sorted_df) > 0:
                        for i in range(len(sorted_df)):
                            # Fill with format <NAME> (<ALLOCATION>)
                            df_ranked.loc[date, i + 1] = sorted_df.index[i] + ' ({:.1f})'.format(sorted_df.iloc[i])

                        # empty strings for unused ranks
                        df_ranked.loc[date, range(len(sorted_df) + 1, n_columns + 1)] = ''

                    else:
                        df_ranked.loc[date, :] = ''

                # remove unused columns
                [df_ranked.drop(col, axis=1, inplace=True) for col in df_ranked.columns if
                 df_ranked[col].str.len().sum() == 0]

                # format dates nicely
                if freq == 'MS':
                    df_ranked = pd.DataFrame(df_ranked, index=df_ranked.index.strftime("%b-%Y"))
                elif freq == 'W-MON':
                    df_ranked = pd.DataFrame(df_ranked, index=df_ranked.index.strftime("%d-%b-%Y"))
                else:
                    df_ranked = pd.DataFrame(df_ranked, index=df_ranked.index.strftime("%Y-%m-%d"))

                # store the allocations - transpose to get rows as keys and columns as dates
                sheet[self.get_name(key, key_type)] = df_ranked.T

        # merge everything together into one large dataframe, sorted by key
        sheet = pd.concat(sheet).sort_index()

        return sheet
