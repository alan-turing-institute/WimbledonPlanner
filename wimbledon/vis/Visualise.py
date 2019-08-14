import numpy as np
import pandas as pd

from copy import deepcopy
import re

from wimbledon.vis import DataHandlers
from wimbledon.vis import HTMLWriter

import matplotlib.pyplot as plt
import seaborn as sns

import os


def extract_name(text):
    """strip allocation of format (x.x) and html <br> tags from name"""
    name = re.sub(r'<br>', '', text)
    name = re.sub(r'\(\d\.\d\)', '', name)
    return name


class Visualise:

    def __init__(self, init_forecast=True, init_harvest=True,
                 start_date=None, end_date=None, freq=None, hrs_per_day=None,
                 data_source='api', data_dir=''):

        self.script_dir = os.path.dirname(os.path.realpath(__file__))

        pd.options.mode.chained_assignment = None  # default='warn' # Gets rid of SettingWithCopy warnings
        pd.options.display.float_format = '{:.1f}'.format  # only print one decimal place
        sns.set(font_scale=1.5)  # have bigger fonts by default

        # only initiate forecast and harvest objects if requested - to have option to be quicker
        # TODO: Deal with case where hv/fc hasn't been initiated but a function tries to use them.
        if init_forecast:
            self.fc = DataHandlers.Forecast(hrs_per_day=hrs_per_day,
                                            data_source=data_source, data_dir=data_dir+'/forecast')
        else:
            self.fc = None

        if init_harvest:
            self.hv = DataHandlers.Harvest(data_source=data_source, data_dir=data_dir+'/harvest')
        else:
            self.hv = None

        #  set default time parameters
        if start_date is None:
            self.START_DATE = pd.datetime.now() - pd.Timedelta('30 days')
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

    def whiteboard(self, key_type,
                   start_date=None,
                   end_date=None,
                   freq=None,
                   display='screen',
                   update_timestamp=None):
        """Create an HTML table in the style of the whiteboard with cells coloured by name"""

        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        sheet = self.fc.whiteboard(key_type, start_date, end_date, freq)

        html = HTMLWriter.make_whiteboard(sheet, key_type, display, update_timestamp=update_timestamp)

        return html

    def all_whiteboards(self, start_date=None, end_date=None, freq=None, update_timestamp=None):
        """Generate the project and people whiteboards styled for display on screen and for printing.

        Keyword Arguments:
            start_date {datetime} -- start date for whiteboard (default: 1 month before today)
            end_date {datetime} -- end date for whiteboard (default: 1 year after today)
            freq {str} -- Frequency of columns, as pandas time frequency string (default: 'MS' for month start)
            update_timestamp {str} -- time data was obtained (default: {None})
        """

        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        whiteboards = dict()

        # ########
        # PROJECTS
        # ########
        # get unstyled whiteboard
        sheet = self.fc.whiteboard('project', start_date, end_date, freq)
        whiteboard_raw = HTMLWriter.make_whiteboard(sheet, 'project', 'nostyle', update_timestamp=update_timestamp)
       
        # add screen style
        style = HTMLWriter.write_style(sheet, display='screen')
        whiteboards['project_screen'] = style + whiteboard_raw
        
        # add print style
        style = HTMLWriter.write_style(sheet, display='print')
        whiteboards['project_print'] = style + whiteboard_raw

        # ######
        # PEOPLE
        # ######
        # get unstyled whiteboard
        sheet = self.fc.whiteboard('person', start_date, end_date, freq)
        whiteboard_raw = HTMLWriter.make_whiteboard(sheet, 'person', 'nostyle', update_timestamp=update_timestamp)
       
        # add screen style
        style = HTMLWriter.write_style(sheet, display='screen')
        whiteboards['person_screen'] = style + whiteboard_raw
               
        # add print style
        style = HTMLWriter.write_style(sheet, display='print')
        whiteboards['person_print'] = style + whiteboard_raw

        return whiteboards

    def get_allocations(self, id_value, id_type, start_date, end_date, freq):

        if id_type == 'person':
            if id_value == 'ALL':
                # initialise df
                df = self.fc.people_totals.copy()

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=False)

                # replace person ids with names
                df.columns = [self.fc.get_person_name(person_id) for person_id in df.columns]

            else:
                # extract the person's allocations, and replace ids with names
                df = deepcopy(self.fc.people_allocations[id_value])

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]
                df.columns.name = self.fc.get_person_name(id_value)

        elif id_type == 'project':

            if id_value == 'CONFIRMED':
                # initialise df
                df = self.fc.project_confirmed.copy()

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date,
                                                    drop_zero_cols=True)

                # replace person ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            elif id_value == 'RESOURCE_REQ':
                # initialise df
                df = self.fc.project_resourcereq.copy()

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                # replace person ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            elif id_value == 'ALLOCATED':
                # initialise df
                df = self.fc.project_confirmed.copy() - self.fc.project_resourcereq.copy()

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                # replace person ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            else:
                # extract the project's people allocations, and replace ids with names
                df = deepcopy(self.fc.project_allocations[id_value])

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                df.columns = [self.fc.get_name(person_id, 'person') for person_id in df.columns]
                df.columns.name = self.fc.get_project_name(id_value)

        elif id_type == 'placeholder':
            if id_value == 'ALL':
                # initialise df
                df = self.fc.placeholder_totals.copy()

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=False)

                # replace ids with names
                df.columns = [self.fc.get_placeholder_name(placeholder_id) for placeholder_id in df.columns]

                # remove resource required placeholders
                cols = [col for col in df.columns if 'resource required' not in col.lower()]
                df = df[cols]

            else:
                # extract the person's allocations, and replace ids with names
                df = self.fc.placeholder_allocations[id_value].copy()

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]
                df.columns.name = self.fc.get_placeholder_name(id_value)

        elif id_type == 'institute':
            # people and placeholders (i.e. including other universities etc.)
            if id_value == 'ALL_PEOPLE':
                # initialise df

                df = pd.merge(self.fc.people_totals, self.fc.placeholder_totals,
                              left_index=True, right_index=True)

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=False)

                # replace ids with names
                df.columns = [self.fc.get_name(person_id, 'person') for person_id in df.columns]

                # remove resource required placeholders
                cols = [col for col in df.columns if 'resource required' not in col.lower()]
                df = df[cols]

            elif id_value == 'PROJECT_REQUIREMENTS':
                # initialise df
                df = self.fc.project_confirmed.copy(deep=True)

                # add resource allocations from placeholders (excl resource required, which have already been included)
                placeholder_ids = [idx for idx in self.fc.placeholders.index
                                   if 'resource required' not in self.fc.placeholders.loc[idx, 'name'].lower()]

                for idx in placeholder_ids:
                    allocs = self.fc.placeholder_allocations[idx].copy(deep=True)

                    for col in allocs.columns:
                        df[col] += allocs[col]

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                # replace ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            elif id_value == 'PROJECT_ALLOCATED':

                # initialise df
                df = self.fc.project_allocated.copy(deep=True)

                # add resource allocations from placeholders (excl resource required, which have already been included)
                placeholder_ids = [idx for idx in self.fc.placeholders.index
                                   if 'resource required' not in self.fc.placeholders.loc[idx, 'name'].lower()]

                for idx in placeholder_ids:
                    allocs = self.fc.placeholder_allocations[idx].copy(deep=True)

                    for col in allocs.columns:
                        df[col] += allocs[col]

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                # replace ids with names
                df.columns = [self.fc.get_project_name(project_id) for project_id in df.columns]

            elif id_value == 'PROJECT_RESREQ':
                # net allocation (i.e. resource required flags) same whether partner institutes included or not
                # so call function again with appropriate arguments that give same desired result
                df = self.get_allocations('RESOURCE_REQ', 'project', start_date, end_date, freq)

            else:
                # get person and placeholder allocation for a specific project id
                # extract the allocations, and replace ids with names
                df = deepcopy(self.fc.project_allocations[id_value])

                # remove resource required placeholders
                placeholder_ids = [idx for idx in self.fc.placeholders.index
                                   if 'resource required' not in self.fc.placeholders.loc[idx, 'name']]

                for idx in placeholder_ids:
                    allocs = self.fc.placeholder_allocations[idx].copy(deep=True)
                    if id_value in allocs.columns:
                        df.loc[:, idx] = allocs[id_value]

                # slice the given date range from the dataframe
                df = DataHandlers.select_date_range(df, start_date, end_date, drop_zero_cols=True)

                df.columns = [self.fc.get_name(idx, 'person') for idx in df.columns]
                df.columns.name = self.fc.get_name(id_value, 'project')

        else:
            raise ValueError('id_type must be person, project or placeholder')

        # check whether there's anything to plot
        rows, cols = df.shape
        if rows > 0 and cols > 0:
            if freq != 'D':
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

            if id_type == 'person' or id_type == 'institute':
                # people nominally allocated 100%
                nominal_allocation = pd.Series(1, index=df.index)
                time_label = 'Time Capacity'

            elif id_type == 'project':
                # get the project's person allocations
                nominal_allocation = self.fc.project_confirmed[id_value]
                nominal_allocation = DataHandlers.select_date_range(nominal_allocation, start_date, end_date,
                                                                    drop_zero_cols=False)
                time_label = 'Time Requirement'

            else:
                raise ValueError('id_type must be person, institute or project')

            # plot the data
            fig = plt.figure(figsize=(15, 5))
            ax = fig.gca()

            df.plot.area(ax=ax, linewidth=0)

            ax.set_title(df.columns.name)
            ax.set_ylabel('Total FTE @ '+str(self.fc.hrs_per_day)+' hrs/day')

            if id_type != 'placeholder':
                if freq != 'D':
                    nominal_allocation = nominal_allocation.resample(freq).mean()

                nominal_allocation.plot(ax=ax, color='k', linewidth=3, linestyle='--', label=time_label)

                ax.set_ylim([0, 1.1 * max([nominal_allocation.max(), df.sum(axis=1).max()])])

            else:
                ax.set_ylim([0, 1.1 * df.sum(axis=1).max()])

            ax.legend(title='', loc='best')
            ax.set_xlim([start_date, end_date])

            return fig

        except ValueError as e:
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
                if freq == 'D':
                    df['UNALLOCATED'] = self.fc.project_resourcereq[id_value]
                else:
                    df['UNALLOCATED'] = self.fc.project_resourcereq[id_value].resample(freq).mean()

            elif id_type == 'person' and 'ALL' not in str(id_value):
                # add the person's total project assignment to the data frame
                if freq == 'D':
                    df['TOTAL'] = self.fc.people_totals[id_value]
                else:
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
                    title = 'Total Person Allocation (% FTE @  ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                else:
                    title = df.columns.name + ' Allocation (% FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'

            elif id_type == 'project':
                fmt = '.1f'

                if id_value == 'ALL_TOTALS':
                    title = 'Project Allocated Capacity (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                elif id_value == 'ALL_REQUIREMENTS':
                    title = 'Project Demand (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                elif id_value == 'ALL_RESREQ':
                    title = 'Project Resource Required (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                else:
                    title = df.columns.name + ' Allocation (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'

            elif id_type == 'placeholder':
                fmt = '.1f'

                if id_value == 'ALL':
                    title = 'Total Allocation (FTE @  ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                else:
                    title = df.columns.name + ' Allocation (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'

            elif id_type == 'institute':
                # people and non-resource required placeholders
                fmt = '.1f'

                if id_value == 'ALL_PEOPLE':
                    title = 'Institute Allocated Capacity (FTE @  ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                elif id_value == 'PROJECT_REQUIREMENTS':
                    title = 'Project Demand (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                elif id_value == 'PROJECT_ALLOCATED':
                    title = 'Project Allocated Capacity (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                elif id_value == 'PROJECT_RESREQ':
                    title = 'Project Resource Required (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'
                else:
                    title = df.columns.name + ' Allocation (FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day)'

            # change date format for prettier printing
            df = self.format_date_index(df, freq)

            fig = plt.figure(figsize=(df.shape[0], df.shape[1]))
            ax = fig.gca()
            # sort by largest values (proceeding through columns to find differences)
            sns.heatmap(df.T.sort_values(by=[col for col in df.T.columns], ascending=False), linewidths=1,
                        cmap='Reds', cbar=False,
                        annot=True, fmt=fmt, annot_kws={'fontsize': 14}, ax=ax)

            ax.set_ylabel('')

            ax.set_title(title)


            return fig

        except ValueError as e:
            return None

    def plot_capacity_check(self, start_date=None, end_date=None, figsize=(10, 7)):
        """Plot of total project requirements, total team allocation and total team capacity over time."""

        start_date, end_date, _ = self.get_time_parameters(start_date, end_date)

        reqs = self.fc.project_confirmed.sum(axis=1)
        reqs = DataHandlers.select_date_range(reqs, start_date, end_date, drop_zero_cols=False)
        reqs = reqs.resample('W-MON').mean()

        alloc = self.fc.project_allocated.sum(axis=1)
        alloc = DataHandlers.select_date_range(alloc, start_date, end_date, drop_zero_cols=False)
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
        ax.set_ylabel('FTE @ ' + str(self.fc.hrs_per_day) + ' hrs/day')

        return fig

    def plot_demand_vs_capacity(self, start_date=None, end_date=None, freq=None, today=None, figsize=(19, 10)):
        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        if today is None:
            today = pd.datetime.now()

        # ----------
        # DEMAND
        # ----------
        # Get totals for REG management, development and support clients
        research_support_idx = self.fc.get_client_id('REG Support')
        reg_management_idx = self.fc.get_client_id('REG Management')
        reg_dev_idx = self.fc.get_client_id('REG Development Work')

        research_support_projs = self.fc.projects[self.fc.projects.client_id == research_support_idx].index
        reg_management_projs = self.fc.projects[self.fc.projects.client_id == reg_management_idx].index
        reg_dev_projs = self.fc.projects[self.fc.projects.client_id == reg_dev_idx].index

        research_support_reqs = self.fc.project_confirmed[research_support_projs].sum(axis=1)
        reg_management_reqs = self.fc.project_confirmed[reg_management_projs].sum(axis=1)
        reg_dev_reqs = self.fc.project_confirmed[reg_dev_projs].sum(axis=1)

        # Get overall totals
        project_confirmed = self.fc.project_confirmed.drop(self.fc.get_project_id('UNAVAILABLE'), axis=1)
        project_confirmed = project_confirmed.sum(axis=1)

        # project_confirmed = total for all non-research support, REG management or REG development projects
        project_confirmed = project_confirmed - reg_management_reqs - reg_dev_reqs - research_support_reqs

        # Get totals for unconfirmed and deferred projects
        unconfirmed = self.fc.project_unconfirmed.sum(axis=1)
        deferred = self.fc.project_deferred.sum(axis=1)

        # merge all demand types into one dataframe ready for plotting
        demand = pd.DataFrame({'REG Management': reg_management_reqs,
                               'REG Development': reg_dev_reqs,
                               'REG Support': research_support_reqs,
                               'Confirmed projects': project_confirmed,
                               'Projects with funder': unconfirmed,
                               'Deferred projects': deferred})

        demand = DataHandlers.select_date_range(demand, start_date, end_date, drop_zero_cols=False)

        demand = demand.resample(freq).mean()

        # ----------
        # CAPACITY
        # ----------

        # Idx for people on fixed term contracts
        ftc = self.fc.people[self.fc.people['association_group'] == 'REG FTC'].index

        # Idx for REG associates
        assoc = self.fc.people[self.fc.people['association_group'] == 'REG Associate'].index

        # Idx for people on permanent contracts
        select_perm = pd.DataFrame(index=self.fc.people.index)
        select_perm['perm'] = self.fc.people['association_group'] == 'REG Permanent'
        select_perm['senior'] = self.fc.people['association_group'] == 'REG Senior'
        select_perm['princ'] = self.fc.people['association_group'] == 'REG Principal'
        select_perm['direc'] = self.fc.people['association_group'] == 'REG Director'
        select_perm = select_perm.any(axis=1)
        perm = self.fc.people[select_perm].index

        # Merge capacity types into one dataframe
        capacity = pd.DataFrame(index=self.fc.capacity.index)
        capacity['REG FTC'] = self.fc.capacity[ftc].sum(axis=1)
        capacity['REG Associate'] = self.fc.capacity[assoc].sum(axis=1)
        capacity['REG Permanent'] = self.fc.capacity[perm].sum(axis=1)

        capacity = capacity.resample(freq).mean()

        capacity = DataHandlers.select_date_range(capacity, start_date, end_date)

        # Load institute capacity from file
        csv = pd.read_csv(self.script_dir+'/reg_capacity.csv', index_col='Month')
        csv = csv.T
        csv.index = pd.to_datetime(csv.index, format='%b-%y')
        csv = csv.loc[start_date:end_date]

        capacity['University Partner'] = csv['University Partner capacity']

        # order columns
        capacity = capacity[['REG Permanent',
                             'REG FTC',
                             'University Partner',
                             'REG Associate']]

        # ----------
        # PLOT
        # ----------
        fig = plt.figure(figsize=figsize)
        ax = fig.gca()

        demand.plot.area(ax=ax, x_compat=True, rot=90, alpha=0.8,
                         color=['#041165', '#043E65', '#2E86C1', 'g', 'y', 'darkred'],
                         stacked=True, linewidth=0)

        capacity.cumsum(axis=1).plot(ax=ax, rot=90,
                                     linewidth=1.5,
                                     color=['purple', 'red', 'blue', 'black'])

        # axis limits
        xlim = ax.get_xlim()
        ylim = (0, 1.1 * max([capacity.sum(axis=1).max(), demand.sum(axis=1).max()]))

        # add quarter separators
        quarters = pd.date_range(start=demand.index.min(), end=demand.index.max(), freq='QS')
        for q in quarters:
            if q.month == 4:
                linestyle = '-'
                linewidth = '2'

                # Annotate year (Q1) starts
                ax.text(x=q + pd.Timedelta('4 days'),
                        y=ylim[1] * 0.95,
                        s=str(q.year) + '-' + str(q.year + 1)[-2:],
                        rotation=0,
                        fontsize=22)

            elif q.month == 7:
                linestyle = ':'
                linewidth = '1.5'

            elif q.month == 10:
                linestyle = '--'
                linewidth = '1.5'

            elif q.month == 1:
                linestyle = ':'
                linewidth = '1.5'

            ax.plot([q, q], ylim, linestyle=linestyle, linewidth=linewidth, color='grey')

        # format labels and titles
        ax.set_xticks(demand.resample('BQS').mean().index.values)
        ax.set_xticklabels(demand.resample('BQS').mean().index.strftime("%Y-%m").values, fontsize=22)
        plt.yticks(fontsize=22)

        ax.set_ylabel('FTE', fontsize=26)
        ax.set_xlabel('Month', fontsize=26)

        # legend outside plot
        ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", fontsize=20)

        # reset axis limits
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

        # Annotate "today" (today defined in first cell)
        ax.plot([today, today], ylim, color='white', linewidth=4)

        ax.text(today + pd.Timedelta(12, unit='D'), 10, 'TODAY',
                rotation=90, fontsize=24, color='white', fontweight='bold')

        # grey box over the past
        ax.fill([start_date, today, today, start_date],
                [ylim[0], ylim[0], ylim[1], ylim[1]],
                'grey', alpha=0.4)

        return fig

    def table_client_demand(self, start_date=None, end_date=None, freq='AS-APR'):
        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        project_ids = self.fc.project_confirmed.columns

        clients = []
        for project in project_ids:
            client_id = self.fc.projects.loc[project, 'client_id']

            if not np.isnan(client_id) and \
                    not self.fc.clients.loc[client_id, 'name'] == 'UNAVAILABLE':

                clients.append(self.fc.clients.loc[client_id, 'name'])

            else:
                clients.append('NaN')

        client_meanfte = self.fc.project_confirmed.copy()

        client_meanfte = DataHandlers.select_date_range(client_meanfte, start_date, end_date, drop_zero_cols=False)

        client_meanfte = client_meanfte.groupby(clients, axis=1).sum()
        client_meanfte = client_meanfte.resample(freq).mean()

        client_meanfte = client_meanfte.loc[:, client_meanfte.sum() > 0]

        client_meanfte = client_meanfte.T
        client_meanfte.drop('NaN', inplace=True)

        return client_meanfte

    def plot_forecast_harvest(self, forecast_id,
                              start_date=None, end_date=None, freq='W-MON',
                              err_bar=True, err_size=0.2,
                              stack=False):

        """compare planned time for a project in forecast to tracked time in harvest.
        If stack is True: Area plot for harvest data split into each person's contribution.
        If err_bar is True: Add lines representing forecast projection +/- err_size*100 %"""
        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        harvest_id = self.fc.get_harvest_id(forecast_id)
        if np.isnan(harvest_id):
            raise ValueError('No harvest_id exists for forecast_id '+str(forecast_id))

        # NB scale forecast fte by using harvest hours per day property (default 6.4)
        fc_totals = self.hv.proj_hrs_per_day * self.fc.project_confirmed[forecast_id].copy()
        fc_totals = fc_totals.resample(freq).sum().cumsum()
        fc_totals = DataHandlers.select_date_range(fc_totals, start_date, end_date, drop_zero_cols=False)

        if stack:
            hv_totals = self.hv.projects_people[harvest_id].copy()
            hv_totals = hv_totals.resample(freq).sum().cumsum()
            hv_totals = DataHandlers.select_date_range(hv_totals, start_date, end_date, drop_zero_cols=True)
            hv_totals.columns = [self.hv.get_person_name(idx) for idx in hv_totals.columns]
        else:
            hv_totals = self.hv.projects_totals[harvest_id].copy()
            hv_totals = hv_totals.resample(freq).sum().cumsum()
            hv_totals = DataHandlers.select_date_range(hv_totals, start_date, end_date, drop_zero_cols=False)

        if (fc_totals == 0).all(axis=None) & (hv_totals == 0).all(axis=None):
            raise ValueError('forecast_id '+str(forecast_id)+' no data to plot.')

        try:
            fig = plt.figure(figsize=(10, 10))
            ax = fig.gca()

            fc_totals.plot(ax=ax, label='Forecast', linewidth=3, color='k')

            if err_bar:
                ((1+err_size) * fc_totals).plot(linestyle='--', linewidth=1, color='k',
                                                label='Forecast +/- {:.0%}'.format(err_size))
                ((1-err_size) * fc_totals).plot(linestyle='--', linewidth=1, color='k', label='')

            if stack:
                hv_totals.plot.area(ax=ax)
            else:
                hv_totals.plot(ax=ax, label='Harvest', linewidth=3, color='r')

            plt.xlim([start_date, end_date])
            plt.ylabel('Cumulative Hours')
            plt.legend()
            plt.title(self.fc.get_project_name(forecast_id))

            return fig

        except ValueError as e:
            plt.close(fig)
            raise ValueError('forecast_id '+str(forecast_id)+' plot failed')
        except TypeError as e:
            plt.close(fig)
            raise TypeError('forecast_id '+str(forecast_id)+' plot failed')

    def plot_harvest(self, id_type, group_type, harvest_id=None,
                    start_date=None, end_date=None, freq='MS',
                    plot_type='bar'):
        """Bar charts of Harvest time tracking."""

        start_date, end_date, freq = self.get_time_parameters(start_date, end_date, freq)

        e = ValueError('Invalid id_type, group_type combination. Valid options are: person-project, '
                       'person-client, person-task, person-TOTAL, project-person, project-task, '
                       'project-TOTAL, client-TOTAL and task-TOTAL')

        if id_type == 'person':
            if harvest_id is not None and group_type != 'TOTAL':
                id_name = self.hv.get_person_name(harvest_id)
            else:
                id_name = ''

            if group_type == 'project':
                df = self.hv.people_projects[harvest_id].copy()
                df.columns = [self.hv.get_project_name(idx) for idx in df.columns]
                type_name = 'Project'
            elif group_type == 'client':
                df = self.hv.people_clients[harvest_id].copy()
                df.columns = [self.hv.get_client_name(idx) for idx in df.columns]
                type_name = 'Client'
            elif group_type == 'task':
                df = self.hv.people_tasks[harvest_id].copy()
                df.columns = [self.hv.get_task_name(idx) for idx in df.columns]
                type_name = 'Task'
            elif group_type == 'TOTAL':
                df = self.hv.people_totals.copy()
                df.columns = [self.hv.get_person_name(idx) for idx in df.columns]
                type_name = 'People'
            else:
                raise e

        elif id_type == 'project':
            if harvest_id is not None and group_type != 'TOTAL':
                id_name = self.hv.get_project_name(harvest_id)
            else:
                id_name = ''

            if group_type == 'person':
                df = self.hv.projects_people[harvest_id].copy()
                df.columns = [self.hv.get_person_name(idx) for idx in df.columns]
                type_name = 'People'
            elif group_type == 'task':
                df = self.hv.projects_tasks[harvest_id].copy()
                df.columns = [self.hv.get_task_name(idx) for idx in df.columns]
                type_name = 'Task'
            elif group_type == 'TOTAL':
                df = self.hv.projects_totals.copy()
                df.columns = [self.hv.get_project_name(idx) for idx in df.columns]
                type_name = 'Project'
            else:
                raise e

        elif id_type == 'client':
            id_name = ''

            if group_type == 'TOTAL':
                df = self.hv.clients_totals.copy()
                df.columns = [self.hv.get_client_name(idx) for idx in df.columns]
                type_name = 'Client'
            else:
                raise e

        elif id_type == 'task':
            id_name = ''

            if group_type == 'TOTAL':
                df = self.hv.tasks_totals.copy()
                df.columns = [self.hv.get_task_name(idx) for idx in df.columns]
                type_name = 'Task'
            else:
                raise e

        else:
            raise e

        df = DataHandlers.select_date_range(df, start_date, end_date)

        if plot_type == 'bar':
            fig = plt.figure(figsize=(10, df.shape[1]))
            ax = fig.gca()

            df.sum().sort_values().plot.barh(ax=ax)
            ax.set_xlabel('Hours')

        elif plot_type == 'pie':
            fig = plt.figure(figsize=(10, 10))
            ax = fig.gca()

            df.sum().sort_values().plot.pie(ax=ax)
            ax.set_ylabel('')
            ax.set_xlabel('')

        elif plot_type == 'heatmap':
            fig = plt.figure(figsize=(10, df.shape[1]))
            ax = fig.gca()

            df = df.resample(freq).sum()
            df = self.format_date_index(df, freq)
            sns.heatmap(df.T.sort_values(by=[col for col in df.T.columns], ascending=False),
                        ax=ax, cmap='Reds', annot=True, cbar=False, fmt='.0f')

        else:
            raise ValueError('plot_type must be bar or heatmap.')

        title = '{:s} hours from {:s} to {:s}'.format(type_name,
                                                      start_date.strftime('%d %b %y'),
                                                      end_date.strftime('%d %b %y'))

        if id_name != '':
            title = id_name + '\n' + title

        ax.set_title(title)

        return fig

