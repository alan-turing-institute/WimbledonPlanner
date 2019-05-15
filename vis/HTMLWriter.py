"""The functions in this file take a dataframe output from a DataHandlers.Forecast.spreadsheet_sheet dataframe
and convert it into a styled HTML table.

The primary function is make_whiteboard(df, key_type, display)"""
import random
from matplotlib.colors import rgb2hex
import pandas as pd
import DataHandlers
import string
import re
import sys
import os.path


# Functions to generate some distinct colours, inspired by:
# https://gist.github.com/adewes/5884820
def get_random_color(pastel_factor=0):
    """Generate a random r,g,b colour. If pastel_factor>0 paler colours tend to be generated."""
    return [(x + pastel_factor) / (1.0 + pastel_factor) for x in [random.uniform(0, 1.0) for i in [1, 2, 3]]]


def color_distance(c1, c2):
    """Value representing the visual distinction between two r,g,b colours,
    inspired by https://www.compuphase.com/cmetric.htm"""
    r1, g1, b1 = c1
    r2, g2, b2 = c2

    mean_r = (r1 + r2) / 2
    delta_r = (r1 - r2) ** 2
    delta_g = (g1 - g2) ** 2
    delta_b = (b1 - b2) ** 2

    return (2 + mean_r) * delta_r + 4 * delta_g + (3 - mean_r) * delta_b


def generate_new_color(existing_colors, pastel_factor=0, n_attempts=1000):
    """Generate a colour as distinct as possible from the colours defined in existing_colors (a list of (r,g,b)
    tuples). n_attempts random colours are generated, and the one with the largest minimum colour distance """
    max_distance = None
    best_color = None
    for i in range(n_attempts):
        color = get_random_color(pastel_factor=pastel_factor)

        if not existing_colors:
            return color

        else:
            best_distance = min([color_distance(color, c) for c in existing_colors])

            if not max_distance or best_distance > max_distance:
                max_distance = best_distance
                best_color = color

    return best_color


def get_text_color(background_color, threshold=0.6):
    """decide whether to use black or white font
     based on: https://stackoverflow.com/a/3943023"""

    r, g, b = background_color[0], background_color[1], background_color[2]

    if (r * 0.299 + g * 0.587 + b * 0.114) > threshold:
        text_color = 'black'
    else:
        text_color = 'white'

    return text_color


def get_name_id(name):
    if "RESOURCE REQUIRED" in name:
        name_id = "RESOURCE_REQUIRED"
    else:
        # remove html tags and digits, if present
        name = re.sub(r'<br>', '', name)
        name = re.sub(r'\(\d\.\d\)', '', name)

        # strip punctuation (apparently quickest way: https://stackoverflow.com/a/266162)
        name_id = name.translate(str.maketrans('', '', string.punctuation))
        name_id = name_id.replace(' ', '_')

    return name_id


def get_name_style(name, background_color, name_type=None):
    if 'RESOURCE REQUIRED' in name or 'RESOURCE_REQUIRED' in name:
        background_color = rgb2hex(background_color)

        style = """.RESOURCE_REQUIRED {{
                  background-color: white;
                  color: red;
                  font-weight: 600;
                  border: 1px solid red;
                }} """.format(background_color=background_color)
    else:
        name_id = get_name_id(name)

        text_color = get_text_color(background_color)
        background_color = rgb2hex(background_color)

        if name_type == 'client':
            style = """.{name_id} {{
              background-color: {background_color};
              color: {text_color};
              font-weight: 600;
              font-size: 16;
              white-space:  normal;
              width: 300px; 
            }} """.format(name_id=name_id,
                          text_color=text_color,
                          background_color=background_color)
        else:
            style = """.{name_id} {{
              background-color: {background_color};
              color: {text_color};
            }} """.format(name_id=name_id,
                          text_color=text_color,
                          background_color=background_color)

    return style


def write_style(colors, client_colors=None, display='print'):
    style = """<style  type="text/css" > """

    if display == 'print':
        style += get_print_style()
    elif display == 'screen':
        style += get_screen_style()
    else:
        raise ValueError('display must be print or screen')

    for name, color in colors.items():
        style += get_name_style(name, color)

    if client_colors is not None:
        for client, color in client_colors.items():
            style += get_name_style(client, color, name_type='client')

    style += '</style>'

    return style


def get_screen_style():
    style = """table {
          font-size: 13;
          font-family: neue-haas-unica, sans-serif;
          font-style: normal;
          font-weight: 400;
       } td {
          text-align:  center;
          height:  4em;
          padding:  1mm;
          text-align:  center;
        } th {
          height:  2em;
          padding:  1mm;
          font-weight: 400;
        } .title {
          height: 2em;
          text-align:  center;
          font-weight: 300;
          font-size: 55;
        } .index {
          text-align:  center;
          vertical-align: center;
          font-weight: 600;
          background-color: #dedede;
        } .header {
          text-align:  center;
          vertical-align: bottom;
          font-weight: 400;
        } .separator {
          height:  1.5em;
          vertical-align: bottom;
          padding:  0mm;
        } .colwidth {
          background-color:  white;
          color: white;
          height: 2em;
        } .blank {
          background-color:  white;
        }"""

    return style


def get_print_style():
    style = """table {
          font-size: 13;
          font-family: neue-haas-unica, sans-serif;
          font-style: normal;
          font-weight: 400;
       } td {
          text-align:  center;
          height:  3em;
          white-space:  nowrap;
          padding:  2mm;
          font-family:  Helvetica;
          text-align:  center;
        } th {
          height:  3em;
          white-space:  nowrap;
          padding:  2mm;
          font-family:  Helvetica;
          font-weight: 400;
        } .title {
          text-align:  center;
          font-family:  Helvetica;
          font-weight: 300;
          font-size: 55;
        } .index {
          text-align:  center;
          vertical-align: center;
          font-weight: 600;
          background-color: #dedede;
        } .header {
          font-size: 21;
          font-weight: 400;
          text-align:  center;
          vertical-align: bottom;
        } .separator {
          height:  2em;
          vertical-align: bottom;
          padding:  0mm;
          font-weight: bold;
        } .colwidth {
          background-color:  white;
          color: white;
          height: 2em;
        } .blank {
          background-color:  white;
        }"""

    return style


def write_header(key_type, columns, title='Research Engineering Project Allocations'):
    # header = """<thead> <tr>
    #         <th></th>
    #         <th></th>
    #         """

    header = """<thead> <tr>
            <th></th>
            """

    if key_type == 'project':
        # project has extra column for client (programme area) groupings
        header += """<th></th>
        <td class="title" colspan={n_columns}>{title}</td>
        </tr><tr>
        <th class="blank" ></th>
        <th class="blank" ></th>
        """.format(n_columns=len(columns), title=title)

    elif key_type == 'person':
        header += """<td class="title" colspan={n_columns}>{title}</td>
         </tr><tr>
         <th class="blank" ></th>
        """.format(n_columns=len(columns), title=title)

    for colname in columns:
        header += """<th class="header" >{colname}</th>
        """.format(colname=colname)

    header += """</tr></thead>
    """

    return header


def get_separator(columns=None):
    if columns is None:
        separator = """<tr class="separator">
        </tr> """
    else:
        separator = """<tr class="separator">
        <th></th>
        <th></th>
        """
        for title in columns:
            separator += """<td class="separator" >{title}</td>
            """.format(title=title)

        separator += """</tr>"""

    return separator


def fix_colwidth(n_columns, width_str="MAKE COLUMN THIS WIDE"):
    """adds a hidden row to the bottom of the table with text width_str, forcing each column to be at least
    as wide as width_str"""

    html = """<tr>
        <th class="colwidth" rowspan=1></th>
        <th></th>
        """

    for _ in range(n_columns):
        html += """<td class="colwidth" >{width_str}</td>
        """.format(width_str=width_str)

    html += """</tr>
    """

    return html


def write_table(df, key_type, display='print'):
    if display == 'print':
        table = """<table cellspacing="5mm"; border-collapse:collapse;>
        """
    elif display == 'screen':
        table = """<table cellspacing="2mm"; border-collapse:collapse;>
        """
    else:
        raise ValueError('display must be print or screen')

    if key_type == 'project':
        title = 'Research Engineering Project Allocations'
    elif key_type == 'person':
        title = 'Research Engineering Person Allocations'
    else:
        raise ValueError('key_type must be project or person')

    table += write_header(key_type, df.columns, title=title)

    table += """<tbody>
    """

    groups = df.groupby(level=0)
    n_groups = len(groups)

    for group_idx, group in enumerate(groups):

        group_label, group_content = group

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # !!!!!!!!!!!! PERSON !!!!!!!!!!!!!!!!!
        if key_type == 'person':

            n_rows = len(group_content)

            table += """<tr>
            <th class="index" rowspan={n_rows}>{group_label}</th>
            """.format(n_rows=n_rows, group_label=group_label)

            for i in range(n_rows):
                # row_label = group_content.iloc[i].name[1]
                # table += """<th>{row_label}</th>
                # """.format(row_label=row_label)

                row_content = group_content.iloc[i].values
                for cell in row_content:
                    name = get_name_id(cell)
                    if name.strip() == '':
                        table += """<td class="blank"></td>
                        """
                    else:
                        table += """<td class="{name}" >{cell}</td>
                        """.format(name=name, cell=cell)

                table += """</tr> """

            if group_idx+1 < n_groups:
                table += get_separator()
            else:
                table += fix_colwidth(df.shape[1])
        # -------------- END OF PERSON --------------

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # !!!!!!!!!!!! PROJECT !!!!!!!!!!!!!!!!
        elif key_type == 'project':
            # extra level for client grouping (project area)

            n_rows = len(group_content)

            project_groups = group_content.groupby(level=1)
            n_projects = len(project_groups)

            table += """<tr>
            <th class="{group_id}" rowspan={n_rows}>{group_label}</th>
            """.format(group_id=get_name_id(group_label), n_rows=n_rows+n_projects-1, group_label=group_label)  # n_rows+n_projects to take into account separator rows

            # loop over projects in this client group
            for project_idx, project_group in enumerate(project_groups):
                project_name, project_content = project_group

                n_people = len(project_content)

                table += """<th class="index" rowspan={n_people}>{project_name}</th>
                """.format(n_people=n_people, project_name=project_name)

                for i in range(n_people):
                    # row_label = project_content.iloc[i].name[2]

                    # table += """<th>{row_label}</th>
                    #                 """.format(row_label=row_label)

                    row_content = project_content.iloc[i].values

                    for cell in row_content:
                        name = get_name_id(cell)
                        if name.strip() == '':
                            table += """<td class="blank"></td>
                            """
                        else:
                            table += """<td class="{name}" >{cell}</td>
                            """.format(name=name, cell=cell)

                    table += """</tr> """

                if project_idx+1 < n_projects:
                    table += get_separator()
            # end of inner loop over client projects

            if group_idx+1 < n_groups:
                table += get_separator()
            else:
                table += fix_colwidth(df.shape[1])
        # -------------- END OF PROJECT --------------

    table += """</tbody>
       </table>"""

    return table


def get_colors(df):
    # remove time allocation/html tags at end of names
    strip_df = df.copy(deep=True)
    for col in strip_df:
        strip_df[col] = strip_df[col].str.replace(r'<br>', '', regex=True)
        strip_df[col] = strip_df[col].str.replace(r'\(\d\.\d\)', '', regex=True)

    # unique names in each column
    names = [strip_df[col].unique() for col in strip_df]

    # unpack list of lists
    names = [cell for column in names for cell in column if cell is not '']
    # set of names (i.e. unique names in whole sheet)
    # changed to using pd.Series then drop_duplicates to preserve order, i.e. from name appearing first to name
    # appearing last, which helps with keeping colours distinct
    names = pd.Series(names).drop_duplicates().values

    colors = {}

    # don't want white to be used as a person/project colour
    colors['WHITE'] = (1, 1, 1)
    # to avoid black/dark colours, uncomment this line:
    colors['BLACK'] = (0, 0, 0)

    # colour used for resource required cells
    colors['RESOURCE_REQUIRED'] = (1, 0, 0)

    for key in names:
        if "RESOURCE REQUIRED" not in key:
            colors[key] = generate_new_color(colors.values())

    return colors


def get_client_colors(df):
    clients = df.index.get_level_values(0).unique()

    # secondary colours from Turing design guidelines
    turing_colors = [(0, 0.49, 1), (1, 0.49, 0), (0, 1, 0.49), (1, 0, 0.49),
                     (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1),
                     (0.49, 0, 1), (0, 1, 0)]

    client_colors = {clients[idx]: turing_colors[idx % len(turing_colors)] for idx in range(len(clients))}
    return client_colors


def make_whiteboard(df, key_type, display):
    colors = get_colors(df)

    if key_type == 'project':
        client_colors = get_client_colors(df)
    else:
        client_colors = None

    html = write_style(colors, client_colors, display=display)
    html += write_table(df, key_type, display=display)

    return html


if __name__ == '__main__':
    key_type = sys.argv[1]
    display = sys.argv[2]

    if key_type == 'person':
        save_dir = '../data/figs/people'
        file_name = 'people.html'
    elif key_type == 'project':
        save_dir = '../data/figs/projects'
        file_name = 'projects.html'
    else:
        raise ValueError('first argument (key_type) must be project or person')

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    fc = DataHandlers.Forecast()
    df = fc.spreadsheet_sheet(key_type,
                              pd.datetime(2019, 3, 1),
                              pd.datetime(2020, 4, 1),
                              'MS')

    html = make_whiteboard(df, key_type, display)

    with open(save_dir+'/'+file_name, 'w') as f:
        f.write(html)
