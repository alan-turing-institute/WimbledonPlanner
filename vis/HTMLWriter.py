import random
from matplotlib.colors import rgb2hex
import pandas as pd
import DataHandlers


# Functions to generate some distinct colours, from:
# https://gist.github.com/adewes/5884820
def get_random_color(pastel_factor=0.5):
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


def generate_new_color(existing_colors, pastel_factor=0.5, n_attempts=1000):
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
        return "RES_REQ"
    else:
        return name[:-9].replace(' ', '_').replace("'", "")


def get_name_style(name, background_color):
    if name == 'RES_REQ':
        background_color = rgb2hex(background_color)

        style = """.RES_REQ {{
                  background-color: {background_color};
                  color: yellow;
                  font-weight: bold;
                }} """.format(background_color=background_color)
    else:
        name_id = name.replace(' ', '_').replace("'", "")
        text_color = get_text_color(background_color)
        background_color = rgb2hex(background_color)

        style = """.{name_id} {{
          background-color: {background_color};
          color: {text_color};
        }} """.format(name_id=name_id,
                      text_color=text_color,
                      background_color=background_color)


    return style


def write_style(colors):
    style = """<style  type="text/css" > td {
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
        } .index {
          text-align:  right;
          vertical-align: center;
        } .header {
          text-align:  center;
          vertical-align: bottom;
        } .separator {
          height:  2em;
          vertical-align: bottom;
          padding:  0mm;
          font-weight: bold;
        } .blank {
          background-color:  white;
        }"""

    for name, color in colors.items():
        style += get_name_style(name, color)

    style += '</style>'

    return style


def write_header(columns):
    header = """<thead> <tr>
     <th class="blank" ></th>
     <th class="blank" ></th>
    """

    for title in columns:
        header += """<th class="header" >{title}</th>
        """.format(title=title)

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


def write_table(df):
    table = """<table cellspacing="5mm"; border-collapse:collapse;>
    """
    table += write_header(df.columns)

    table += """<tbody>
    """

    for group_label, group_content in df.groupby(level=0):
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

        table += get_separator()  # get_separator(df.columns)

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
    colors['RES_REQ'] = (1, 0, 0)

    for key in names:
        colors[key] = generate_new_color(colors.values())

    return colors


def make_whiteboard(df):
    colors = get_colors(df)
    html = write_style(colors)
    html += write_table(df)

    return html


if __name__ == '__main__':
    fc = DataHandlers.Forecast()
    df = fc.spreadsheet_sheet('project',
                              pd.datetime(2019, 3, 1),
                              pd.datetime(2020, 4, 1),
                              'MS')

    html = make_whiteboard(df)

    with open('tmp.html', 'w') as f:
        f.write(html)
