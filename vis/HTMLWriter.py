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
    return [(x + pastel_factor) / (1.0 + pastel_factor) for x in [random.uniform(0, 1.0) for i in [1, 2, 3]]]


def color_distance(c1, c2):
    """inspired by https://www.compuphase.com/cmetric.htm"""
    r1, g1, b1 = c1
    r2, g2, b2 = c2

    mean_r = (r1 + r2) / 2
    delta_r = (r1 - r2) ** 2
    delta_g = (g1 - g2) ** 2
    delta_b = (b1 - b2) ** 2

    return (2 + mean_r) * delta_r + 4 * delta_g + (3 - mean_r) * delta_b


def generate_new_color(existing_colors, pastel_factor=0, n_attempts=1000):
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


def get_name_style(name, background_color):
    if 'RESOURCE REQUIRED' in name or 'RESOURCE_REQUIRED' in name:
        background_color = rgb2hex(background_color)

        style = """.RESOURCE_REQUIRED {{
                  background-color: red;
                  color: yellow;
                  font-weight: bold;
                }} """.format(background_color=background_color)
    else:
        name_id = get_name_id(name)

        text_color = get_text_color(background_color)
        background_color = rgb2hex(background_color)

        style = """.{name_id} {{
          background-color: {background_color};
          color: {text_color};
        }} """.format(name_id=name_id,
                      text_color=text_color,
                      background_color=background_color)

    return style


def write_style(colors, display='print'):
    style = """<style  type="text/css" > """

    if display == 'print':
        style += get_print_style()
    elif display == 'screen':
        style += get_screen_style()
    else:
        raise ValueError('display must be print or screen')

    for name, color in colors.items():
        style += get_name_style(name, color)

    style += '</style>'

    return style


def get_screen_style():
    style = """table {
          font-size: 10;
       } td {
          text-align:  center;
          height:  4em;
          padding:  1mm;
          font-family:  Helvetica;
          text-align:  center;
        } th {
          height:  2em;
          padding:  1mm;
          font-family:  Helvetica;
        } .title {
          height: 2em;
          text-align:  center;
          font-family:  Helvetica;
          font-weight: bold;
          font-size: 20;
        } .index {
          text-align:  right;
          vertical-align: center;
        } .header {
          text-align:  center;
          vertical-align: bottom;
        } .separator {
          height:  1.5em;
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


def get_print_style():
    style = """td {
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
        } .title {
          text-align:  center;
          font-family:  Helvetica;
          font-weight: bold;
          font-size: 36;
        } .index {
          text-align:  right;
          vertical-align: center;
        } .header {
          text-align:  center;
          vertical-align: bottom;
        } .separator {
          height:  3em;
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


def write_header(columns, title='Research Engineering Project Allocations'):
    header = """<thead> <tr>
            <th></th>
            <th></th>
            <td class="title" colspan={n_columns}>{title}</td>
     </tr><tr>
     <th class="blank" ></th>
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
        <th class="index" rowspan=1></th>
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

    table += write_header(df.columns, title=title)

    table += """<tbody>
    """

    groups = df.groupby(level=0)
    n_groups = len(groups)

    for group_idx, group in enumerate(groups):
        group_label, group_content = group
        n_rows = len(group_content)

        table += """<tr>
        <th class="index" rowspan={n_rows}>{group_label}</th>
        """.format(n_rows=n_rows, group_label=group_label)

        for i in range(n_rows):
            row_label = group_content.iloc[i].name[1]
            table += """<th>{row_label}</th>
            """.format(row_label=row_label)

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

    table += """</tbody>
       </table>"""

    return table


def get_colors(df):
    # unique names in each column - [:-9] to remove time allocation/html tags at end
    names = [df[col].str[:-9].unique() for col in df]
    # unpack list of lists
    names = [cell for column in names for cell in column if cell is not '']
    # set of names (i.e. unique names in whole sheet)
    # changed to using pd.Series then drop_duplicates to preserve order, i.e. from name appearing first to name
    # appearing last, which helps with keeping colours distinct
    names = pd.Series(names).drop_duplicates().values

    colors = {}

    # don't want white or black to be used as a person/project colour
    colors['WHITE'] = (1, 1, 1)
    colors['BLACK'] = (0, 0, 0)
    colors['RESOURCE_REQUIRED'] = (1, 0, 0)

    for key in names:
        if "RESOURCE REQUIRED" not in key:
            colors[key] = generate_new_color(colors.values())

    return colors


def make_whiteboard(df, key_type, display):
    colors = get_colors(df)
    html = write_style(colors, display=display)
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
