from Forecast import Forecast
import pandas as pd
import random
from matplotlib.colors import rgb2hex
import matplotlib.pyplot as plt
import seaborn as sns

pd.options.mode.chained_assignment = None  # default='warn' # Gets rid of SettingWithCopy warnings
pd.options.display.float_format = '{:.1f}'.format # only print one decimal place
sns.set(font_scale=1.5) # have bigger fonts by default


class Visualise:

    def __init__(self, start_date=None, end_date=None, freq=None):
        self.fc = Forecast()

        #  set default time parameters
        if start_date is None:
            self.START_DATE = pd.datetime(2019, 1, 1)
        else:
            self.START_DATE = start_date

        if end_date is None:
            self.END_DATE = pd.datetime(2019, 12, 31)
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
                return 'background-color: ' + rgb2hex(colors[cell])

            else:
                return 'background-color: white'

        styled_df = sheet.style.applymap(highlight_name)

        return styled_df

    def plot_allocations(self, id_value, id_type,
                         start_date=None,
                         end_date=None):
        """Make a stacked area plot of a person's project allocations between
        a start date and an end date."""

        start_date, end_date, _ = self.get_time_parameters(start_date, end_date)

        if id_type == 'person_id':
            # get the person's project allocations
            df = self.fc.people_allocations[id_value]

            # extract the date range of interest
            df = self.fc.select_date_range(df, start_date, end_date)

            # replace project_ids in column names with their project names
            df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            df.columns.name = self.fc.get_person_name(id_value)

            # people nominally allocated 100%
            nominal_allocation = pd.Series(1, index=df.index)

            time_label = 'Time Capacity'

        elif id_type == 'project_id':
            # get the project's person allocations
            df = self.fc.project_allocations[id_value]

            # extract the date range of interest
            df = self.fc.select_date_range(df, start_date, end_date)

            # replace person_ids in column names with their names
            df.columns = [self.fc.get_person_name(person_id) for person_id in df.columns]
            df.columns.name = self.fc.get_project_name(id_value)

            nominal_allocation = self.fc.project_reqs.loc[(self.fc.project_reqs.index >= start_date) & (self.fc.project_reqs.index <= end_date), id_value]

            time_label = 'Time Requirement'
        else:
            raise ValueError('id_type must be person_id or project_id')

        # check whether there's anything to plot
        rows, cols = df.shape
        if rows > 0 and cols > 0:
            df = df.resample('W-MON').mean()

            # plot the data
            ax = plt.figure(figsize=(15, 5)).gca()
            df.plot.area(ax=ax, linewidth=0)

            plt.title(df.columns.name)
            plt.ylabel('Proportion 6.4hr days')
            plt.xticks()

            nominal_allocation.plot(ax=ax, color='k', linewidth=3, linestyle='--', label=time_label)

            plt.legend(title='', loc='best')
            plt.xlim([start_date, end_date])

            plt.show()

        else:
            print('Nothing to plot.')

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

        if id_type == 'person_id':

            if id_value == 'ALL':
                # initialise df
                df = self.fc.people_totals.copy()

                # replace person ids with names
                df.columns = [self.fc.get_person_name(person_id) for person_id in df.columns]

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=False)

            else:
                # extract the person's allocations, and replace ids with names
                df = self.fc.people_allocations[id_value].copy()
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]
                df.columns.name = self.fc.get_person_name(id_value)

                # add the person's total project assignment to the data frame
                df['TOTAL'] = self.fc.people_totals[id_value]

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

        elif id_type == 'project_id':

            if id_value == 'ALL_TOTALS':
                # initialise df
                df = self.fc.project_totals.copy()

                # replace person ids with names
                # df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

            elif id_value == 'ALL_REQUIREMENTS':
                # initialise df
                df = self.fc.project_reqs.copy()

                # replace person ids with names
                # df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

            elif id_value == 'ALL_NETALLOC':
                # initialise df
                df = self.fc.project_netalloc.copy()

                # replace person ids with names
                # df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

            else:
                # extract the project's people allocations, and replace ids with names
                df = self.fc.project_allocations[id_value].copy()
                df.columns = [self.fc.get_person_name(person_id) for person_id in df.columns]
                df.columns.name = self.fc.get_project_name(id_value)

                # add the project's missing resource allocation
                df['UNALLOCATED'] = self.fc.project_netalloc[id_value]

                # slice the given date range from the dataframe
                df = self.fc.select_date_range(df, start_date, end_date, drop_zero_cols=True)

        else:
            return ValueError('id_type must be person_id or project_id')

        # check there's something to display
        rows, cols = df.shape
        if rows > 0 and cols > 0:
            # resample the rows to the given date frequency
            df = df.resample(freq).mean()

            # change date format for prettier printing
            if freq == 'MS':
                df = pd.DataFrame(df, index=df.index.strftime("%b-%Y"))
            elif freq == 'W-MON':
                df = pd.DataFrame(df, index=df.index.strftime("%d-%b-%Y"))
            else:
                df = pd.DataFrame(df, index=df.index.strftime("%Y-%m-%d"))

            return self.highlight_allocations(df)

        else:
            print('Nothing to print.')
            return df

