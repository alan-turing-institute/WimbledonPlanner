from Forecast import Forecast
import pandas as pd
import random
from matplotlib.colors import rgb2hex
import matplotlib.pyplot as plt
import seaborn as sns


class Visualise:

    def __init__(self, start_date=None, end_date=None, freq=None):
        pd.options.mode.chained_assignment = None  # default='warn' # Gets rid of SettingWithCopy warnings
        pd.options.display.float_format = '{:.1f}'.format  # only print one decimal place
        sns.set(font_scale=1.5)  # have bigger fonts by default

        self.fc = Forecast()

        #  set default time parameters
        if start_date is None:
            self.START_DATE = pd.datetime.now()
        else:
            self.START_DATE = start_date

        if end_date is None:
            self.END_DATE = pd.datetime.now() + pd.Timedelta('365 days')
        else:
            self.END_DATE = end_date

        if freq is None:
            self.FREQ = 'MS'
        else:
            self.FREQ = freq

    def get_time_parameters(self, start_date=None, end_date=None, freq=None):

        if start_date is None:
            start_date = self.START_DATE

        if end_date is None:
            end_date = self.END_DATE

        if freq is None:
            freq = self.FREQ

        return start_date, end_date, freq

    def format_date_index(self, df, freq=None):
        _, _, freq = self.get_time_parameters(freq=freq)

        # change date format for prettier printing
        if freq == 'MS':
            df = pd.DataFrame(df, index=df.index.strftime("%b-%Y"))
        elif freq == 'W-MON':
            df = pd.DataFrame(df, index=df.index.strftime("%d-%b-%Y"))
        else:
            df = pd.DataFrame(df, index=df.index.strftime("%Y-%m-%d"))

        return df

    # Functions to generate some distinct colours, from:
    # https://gist.github.com/adewes/5884820
    def get_random_color(self, pastel_factor=0.5):
        return [(x + pastel_factor) / (1.0 + pastel_factor) for x in [random.uniform(0, 1.0) for i in [1, 2, 3]]]

    def color_distance(self, c1, c2):
        return sum([abs(x[0] - x[1]) for x in zip(c1, c2)])

    def generate_new_color(self, existing_colors, pastel_factor=0.5):
        max_distance = None
        best_color = None
        for i in range(0, 100):
            color = self.get_random_color(pastel_factor=pastel_factor)
            if not existing_colors:
                return color
            best_distance = min([self.color_distance(color, c) for c in existing_colors])
            if not max_distance or best_distance > max_distance:
                max_distance = best_distance
                best_color = color
        return best_color

    def styled_sheet(self, key_type,
                     start_date=None,
                     end_date=None,
                     freq=None):
        """colour the cells in sheet by name"""

        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        sheet = self.fc.spreadsheet_sheet(key_type, start_date, end_date, freq)

        # unique names in each column - [:-6] to remove time allocation of format (x.x) at end
        names = [sheet[col].str[:-6].unique() for col in sheet]
        # unpack list of lists
        names = [cell for column in names for cell in column if cell is not '']
        # set of names (i.e. unique names in whole sheet)
        names = set(names)

        colors = {}
        for key in names:
            colors[key] = self.generate_new_color(colors.values(), pastel_factor=0.9)

        # Assign a different colour to each project
        def highlight_name(cell):
            # strip time allocation of format '(x.x)' from cell values
            cell = cell[:-6]
            if 'RESOURCE REQUIRED' in cell:
                return 'background-color: red; color: white; border: 5px solid black'

            elif cell in names:
                return 'background-color: ' + rgb2hex(colors[cell]) + '; border: 1px solid black'

            else:
                return 'background-color: white'

        styled_df = sheet.style.applymap(highlight_name).set_properties(**{'text-align': 'center'})

        return styled_df

    def get_allocations(self, id_value, id_type, start_date, end_date, freq):

        if id_type == 'person':
            if id_value == 'ALL':
                # initialise df
                df = self.fc.people_totals.copy()

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=False)

                # replace person ids with names
                df.columns = [self.fc.get_person_name(person_id) for person_id in df.columns]

            else:
                # extract the person's allocations, and replace ids with names
                df = self.fc.people_allocations[id_value].copy()

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]
                df.columns.name = self.fc.get_person_name(id_value)

        elif id_type == 'project':

            if id_value == 'ALL_TOTALS':
                # initialise df
                df = self.fc.project_totals.copy()

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                # replace person ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            elif id_value == 'ALL_REQUIREMENTS':
                # initialise df
                df = self.fc.project_reqs.copy()

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                # replace person ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            elif id_value == 'ALL_NETALLOC':
                # initialise df
                df = self.fc.project_netalloc.copy()

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                # replace person ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            else:
                # extract the project's people allocations, and replace ids with names
                df = self.fc.project_allocations[id_value].copy()

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                df.columns = [self.fc.get_person_name(person_id) for person_id in df.columns]
                df.columns.name = self.fc.get_project_name(id_value)

        else:
            raise ValueError('id_type must be person or project')

        # check whether there's anything to plot
        rows, cols = df.shape
        if rows > 0 and cols > 0:
            df = df.resample(freq).mean()
            return df

        else:
            raise ValueError('No {:s} data to plot for id {:s} between {:s} and {:s}'.format(id_type,
                                                                                             str(id_value),
                                                                                             str(start_date.date()),
                                                                                             str(end_date.date())))

    def plot_allocations(self, id_value, id_type,
                         start_date=None,
                         end_date=None,
                         freq='W-MON'):
        """Make a stacked area plot of a person's project allocations between
        a start date and an end date."""

        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        try:
            df = self.get_allocations(id_value, id_type, start_date, end_date, freq)

            if id_type == 'person':
                # people nominally allocated 100%
                nominal_allocation = pd.Series(1, index=df.index)
                time_label = 'Time Capacity'

            elif id_type == 'project':
                # get the project's person allocations
                nominal_allocation = self.fc.project_reqs[id_value]
                nominal_allocation = self.fc.select_date_range(nominal_allocation, start_date, end_date,
                                                               drop_zero_cols=False)
                time_label = 'Time Requirement'

            # plot the data
            fig = plt.figure(figsize=(15, 5))
            ax = fig.gca()

            df.plot.area(ax=ax, linewidth=0)

            ax.set_title(df.columns.name)
            ax.set_ylabel('Total FTE @ 6.4 hrs/day')

            nominal_allocation = nominal_allocation.resample(freq).mean()
            nominal_allocation.plot(ax=ax, color='k', linewidth=3, linestyle='--', label=time_label)

            ax.legend(title='', loc='best')
            ax.set_xlim([start_date, end_date])
            ax.set_ylim([0, 1.1 * max([nominal_allocation.max(), df.max().max()])])

            return fig

        except ValueError as e:
            print(e)
            return None

    def highlight_allocations(self, df):
        """Function to conditionally style a data frame:
            Total allocations above 1.0 are highlighted red,
            above 0.8 orange, 0.8 yellow, and below 0.8 green.

            Individual project allocations are coloured blue when
            the person is active and grey when inactive on that project"""

        def highlight_tot(series):
            """function used to apply highlighting to the TOTAL column"""
            is_over = series > 1.21
            is_marginal = (series > 1.1) & (is_over is False)
            is_under = series < 0.9

            style = []
            for i in range(len(series)):
                if is_over[i]:
                    style.append('background-color: red')
                elif is_marginal[i]:
                    style.append('background-color: orange')
                elif is_under[i]:
                    style.append('background-color: lime')
                else:
                    style.append('background-color: yellow')

            return style

        def highlight_active(series):
            """Function used to apply highlighting to all columns except the TOTAL column"""
            style = []
            for i in range(len(series)):
                if series[i] > 0:
                    style.append('background-color: lightblue')
                else:
                    style.append('background-color: dimgrey')

            return style

        def highlight_unallocated(series):
            """function used to apply highlighting to UNALLOCATED project requirements column"""
            one_person_req = (series > 0) & (series <= 0.5)
            two_person_req = series > 0.5
            is_good = series == 0

            style = []
            for i in range(len(series)):
                if two_person_req[i]:
                    style.append('background-color: red')
                elif one_person_req[i]:
                    style.append('background-color: orange')
                elif is_good[i]:
                    style.append('background-color: lime')
                else:
                    style.append('background-color: yellow')

            return style

        # Apply the style. In order:
        #   - sort column names A-Z (excluding TOTAL column, if that exists)
        #   - display percentages to nearest integer
        #   - centre align text
        #   - centre align and word wrap column names
        #   - conditional formatting for TOTAL column
        #   - conditional formatting for remaining columns
        if 'TOTAL' in df.columns:
            return df[sorted(df.columns.drop('TOTAL'))+['TOTAL']].style. \
                format('{:.0%}'). \
                set_properties(**{'text-align': 'center'}). \
                set_table_styles([dict(selector="th", props=[('max-width', '100px'),
                                                             ('text-align', 'center')])]). \
                apply(highlight_active, subset=df.columns.drop('TOTAL')). \
                apply(highlight_tot, subset=['TOTAL'])

        elif 'UNALLOCATED' in df.columns:
            return df[sorted(df.columns.drop('UNALLOCATED'))+['UNALLOCATED']].style. \
                format('{:.0%}'). \
                set_properties(**{'text-align': 'center'}). \
                set_table_styles([dict(selector="th", props=[('max-width', '100px'),
                                                             ('text-align', 'center')])]). \
                apply(highlight_active, subset=df.columns.drop('UNALLOCATED')). \
                apply(highlight_unallocated, subset=['UNALLOCATED'])

        else:
            return df[sorted(df.columns)].style. \
                format('{:.0%}'). \
                set_properties(**{'text-align': 'center'}). \
                set_table_styles([dict(selector="th", props=[('max-width', '100px'),
                                                             ('text-align', 'center')])]). \
                apply(highlight_tot)

    def table_allocations(self, id_value, id_type,
                          start_date=None, end_date=None, freq=None):
        """Display a formatted table of a person's project allocations in a given
        date range, and with a certain date frequency. E.g. if freq='MS' each row
        will correspond to a month. 'D' for days, or 'W-MON' for weeks."""

        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        try:
            df = self.get_allocations(id_value, id_type, start_date, end_date, freq)

            if id_type == 'project' and 'ALL' not in str(id_value):
                # add the project's missing resource allocation
                df['UNALLOCATED'] = self.fc.project_netalloc[id_value].resample(freq).mean()

            elif id_type == 'person' and 'ALL' not in str(id_value):
                # add the person's total project assignment to the data frame
                df['TOTAL'] = self.fc.people_totals[id_value].resample(freq).mean()

            df = self.format_date_index(df, freq)

            return self.highlight_allocations(df)

        except ValueError as e:
            print(e)

    def heatmap_allocations(self, id_value, id_type,
                            start_date=None, end_date=None, freq=None):
        """Display a formatted table of a person's project allocations in a given
        date range, and with a certain date frequency. E.g. if freq='MS' each row
        will correspond to a month. 'D' for days, or 'W-MON' for weeks."""

        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        try:
            df = self.get_allocations(id_value, id_type, start_date, end_date, freq)

            if id_type == 'person':
                fmt = '.0%'

                if id_value == 'ALL':
                    title = 'Total Person Allocation (% FTE @ 6.4hrs/day)'
                else:
                    title = df.columns.name + ' Allocation (% FTE @ 6.4hrs/day)'

            elif id_type == 'project':
                fmt = '.1f'

                if id_value == 'ALL_TOTALS':
                    title = 'Project Resource Allocation (FTE @ 6.4 hrs/day)'

                elif id_value == 'ALL_REQUIREMENTS':
                    title = 'Project Resource Requirements (FTE @ 6.4 hrs/day)'

                elif id_value == 'ALL_NETALLOC':
                    title = 'Project Resource Not Yet Allocated (FTE @ 6.4 hrs/day)'

                else:
                    title = df.columns.name + ' Allocation (FTE @ 6.4hrs/day)'

            # change date format for prettier printing
            df = self.format_date_index(df, freq)

            fig = plt.figure(figsize=(df.shape[0], df.shape[1]))
            ax = fig.gca()
            # sort by largest values (proceeding through columns to find differences)
            sns.heatmap(df.T.sort_values(by=[col for col in df.T.columns], ascending=False), linewidths=1,
                        cmap='Reds', cbar=False,
                        annot=True, fmt=fmt, annot_kws={'fontsize': 14}, ax=ax)

            ax.set_title(title)

            return fig

        except ValueError as e:
            print(e)
            return None

    def plot_capacity_check(self, start_date=None, end_date=None, figsize=(10, 7)):
        """Plot of total project requirements, total team allocation and total team capacity over time."""

        start_date, end_date, _ = self.get_time_parameters(start_date, end_date)

        reqs = self.fc.project_reqs.sum(axis=1)
        reqs = self.fc.select_date_range(reqs, start_date, end_date, drop_zero_cols=False)
        reqs = reqs.resample('W-MON').mean()

        alloc = self.fc.project_totals.sum(axis=1)
        alloc = self.fc.select_date_range(alloc, start_date, end_date, drop_zero_cols=False)
        alloc = alloc.resample('W-MON').mean()

        # Weekly capacity just a constant based on number of people for now -
        # no way to know e.g. when people started/stopped in REG in current data
        team100 = self.fc.people['weekly_capacity'].sum()

        fig = plt.figure(figsize=figsize)
        ax = fig.gca()

        reqs.plot(ax=ax, label='Project Required')
        alloc.plot(ax=ax, label='Team Allocated')
        xlim = ax.get_xlim()
        ax.plot(xlim, [team100, team100], 'k--', label='Team Total')
        ax.set_xlim(xlim)
        ax.legend()
        ax.set_ylabel('FTE @ 6.4hrs/day')

        return fig
