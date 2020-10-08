"""The functions in this file take a dataframe output from a Wimbledon.whiteboard dataframe
and convert it into a styled HTML table.

The primary function is make_whiteboard(df, key_type, display)"""

from distinctipy import distinctipy
import pandas as pd

from wimbledon import Wimbledon

import string
import re
import sys
import os.path
from datetime import datetime

def get_name_id(name):
    """name is a string of cell contents which may include:
    HTML tags
    A time allocation of format (x.x)
    Punctuation

    get_name_id converts name into a style suitable for a CSS class name by removing all the above.
    """

    if "RESOURCE REQUIRED" in name:
        name_id = "RESOURCE_REQUIRED"
    elif "UNCONFIRMED" in name:
        name_id = "UNCONFIRMED"
    elif "DEFERRED" in name:
        name_id = "DEFERRED"
    elif "NOT FUNDED" in name:
        name_id = "NOT_FUNDED"
    else:
        # remove everything between a < and a > (html tags)
        name = re.sub(r"(?<=\<)(.*?)(?=\>)", "", name)
        name = name.replace("<", "")
        name = name.replace(">", "")

        # remove time allocation of format (x.x)
        name = re.sub(r"\(\d\.\d\)", "", name)

        # strip punctuation (apparently quickest way: https://stackoverflow.com/a/266162)
        name_id = name.translate(str.maketrans("", "", string.punctuation))
        name_id = name_id.replace(" ", "_")

        # remove all digits at start of name (CSS class names can't start with
        # digits)
        name_id = re.sub(r"^\d*", "", name_id)

    return name_id


def get_name_style(name, background_color=None, name_type=None):
    """Generate the css style class for the entity represented by string name. Pre-defined styles for
    placeholders or generate distinct colours for other names."""

    if "RESOURCE REQUIRED" in name or "RESOURCE_REQUIRED" in name:
        style = """
        .RESOURCE_REQUIRED {
            background-color: white;
            color: red;
            font-weight: 600;
            border: 1px solid red;
        }
        """

    elif "NOT FUNDED" in name or "NOT_FUNDED" in name:
        style = """
        .NOT_FUNDED {
            background-color: white;
            color: green;
            font-weight: 600;
            border: 1px solid green;
        }
        """

    elif "UNCONFIRMED" in name:
        style = """
        .UNCONFIRMED {
            background-color: white;
            color: gray;
            font-weight: 600;
            border: 1px solid gray;
        }
        """

    elif "DEFERRED" in name:
        style = """.DEFERRED {
                          background-color: white;
                          color: orange;
                          font-weight: 600;
                          border: 1px solid orange;
                } """
    elif "UNAVAILABLE" in name:
        style = """.UNAVAILABLE {
                          background-color: white;
                          color: gray;
                          font-weight: 600;
                          border: 1px solid gray;
                } """

    elif "UNALLOCATED" in name:
        style = """.UNALLOCATED {
                          background-color: white;
                          color: green;
                          font-weight: 600;
                          border: 1px solid green;
                } """

    elif "OVER CAPACITY" in name or "OVER_CAPACITY" in name:
        style = """.OVER_CAPACITY {
                          background-color: white;
                          color: red;
                          font-weight: 600;
                          border: 1px solid red;
                } """
    else:
        name_id = get_name_id(name)

        text_color = distinctipy.get_hex(distinctipy.get_text_color(background_color))
        background_color = distinctipy.get_hex(background_color)

        if name_type == "client":
            style = """.{name_id} {{
              background-color: {background_color};
              color: {text_color};
              font-weight: 600;
              font-size: 16;
              white-space:  normal;
              width: 300px;
            }} """.format(
                name_id=name_id,
                text_color=text_color,
                background_color=background_color,
            )
        else:
            style = """.{name_id} {{
              background-color: {background_color};
              color: {text_color};
            }} """.format(
                name_id=name_id,
                text_color=text_color,
                background_color=background_color,
            )

    return style


def write_style(df, display="print"):
    """write the CSS to style the table"""

    if display == "nostyle":
        return ""

    else:
        style = """<style  type="text/css" > """
        style += get_base_style()

        if display == "screen":
            style += get_screen_style()

        colors = get_colors(df)

        for name, color in colors.items():
            style += get_name_style(name, color)

        style += get_name_style("RESOURCE REQUIRED")
        style += get_name_style("UNCONFIRMED")
        style += get_name_style("DEFERRED")
        style += get_name_style("UNAVAILABLE")

        group_colors = get_group_colors(df)

        for client, color in group_colors.items():
            style += get_name_style(client, color, name_type="client")

        style += "</style>"

        return style


def get_base_style():
    """css used for general table style: fonts, alignments, sizes etc."""

    style = """table {
          font-size: 13;
          font-family: neue-haas-unica, sans-serif;
          font-style: normal;
          font-weight: 400;
          border-spacing: 1mm;
          border-collapse: separate;
       } td {
          text-align:  center;
          height:  3em;
          white-space:  nowrap;
          padding:  2mm;
          font-family:  Helvetica;
          text-align:  center;
          background-color: white;
        } th {
          height:  3em;
          white-space:  nowrap;
          padding:  2mm;
          font-family:  Helvetica;
          font-weight: 400;
          background-color: white;
        }  th a {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        } a {
          color: inherit;
          text-decoration: inherit;
         } .title {
          text-align:  center;
          font-family:  Helvetica;
          font-weight: 300;
          font-size: 55;
          background-color: white;
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
          background-color: white;
        } .separator {
          height:  2em;
          vertical-align: bottom;
          padding:  0mm;
          font-weight: bold;
          background-color: white;
        } .colwidth {
          background-color:  white;
          color: white;
          height: 2em;
        } .blank {
          background-color:  white;
        }"""

    return style


def get_screen_style():
    """additional css used for screen display mode to:
    * Freeze row and column headers and add scroll bars
    * Highlight index group (project/person name) on hover (for project sheet - click sends to GitHub issue)
    """

    style = """ div.container {
          overflow: scroll;
          max-height: 100%;
          max-width: 100%;
        } thead th {
          position: sticky;
          top: 0;
        } tbody th {
          position: sticky;
          left: 0;
        } .index {
          position: sticky;
          left: 120;
        }  th a {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }  .index:hover {
          background-color: #ffff99;
        }"""

    return style


def write_header(columns, title="Research Engineering Project Allocations"):
    """write the table header (title and column names)"""

    header = """<thead> <tr>
        <th></th>
        <th></th>
        <td class="title" colspan={n_columns}>{title}</td>
    </tr><tr>
        <th class="blank" ></th>
        <th class="blank" ></th>
    """.format(
        n_columns=len(columns), title=title
    )

    for colname in columns:
        header += """<th class="header" >{colname}</th>
        """.format(
            colname=colname
        )

    header += """</tr></thead>
    """

    return header


def get_separator(columns=None):
    """blank row used to get visible separation between row groups (i.e. gap between people/projects)"""

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
            """.format(
                title=title
            )

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
        """.format(
            width_str=width_str
        )

    html += """</tr>
    """

    return html


def write_table(df, title):
    """creates the html for the whiteboard visualisation using:
    df: a dataframe  with data periods as columns, a multi-index of (role, person) for the people sheet or
    (programme, project) for the project sheet, and cell values of format "name (allocation)"
    """

    table = """
    <div class="container">
        <table>
    """

    table += write_header(df.columns, title=title)

    table += """<tbody>
    """

    groups = df.groupby(level=0, sort=False)
    n_groups = len(groups)

    # Loop over index groupings (either project client/programmes, or people role type)
    for group_idx, group in enumerate(groups):

        group_label, group_content = group

        n_rows = len(group_content)

        index_groups = group_content.groupby(level=1, sort=False)
        n_index_groups = len(index_groups)

        table += """<tr>
        <th class="{group_id}" rowspan={n_rows}>{group_label}</th>
        """.format(
            group_id=get_name_id(group_label),
            n_rows=n_rows + n_index_groups - 1,
            group_label=group_label,
        )  # n_rows+n_index_groups to take into account separator rows

        # Loop over rows in this index group (each row being a project or a person)
        for index_idx, index_group in enumerate(index_groups):
            index_name, index_content = index_group

            n_index = len(index_content)

            table += """<th class="index" rowspan={n_index}>{index_name}</th>
            """.format(
                n_index=n_index, index_name=index_name
            )

            for i in range(n_index):
                row_content = index_content.iloc[i].values

                for cell in row_content:
                    name = get_name_id(cell)
                    if name.strip() == "":
                        table += """<td class="blank"></td>
                        """
                    else:
                        table += """<td class="{name}" >{cell}</td>
                        """.format(
                            name=name, cell=cell
                        )

                table += """</tr>"""

                if i < n_index - 1:
                    table += """
                    <tr>"""

            if index_idx + 1 < n_index_groups:
                table += get_separator()
                table += """
                            <tr>"""

        # end of inner loop over client projects

        if group_idx + 1 < n_groups:
            table += get_separator()
            table += """
            <tr>"""
        else:
            table += fix_colwidth(df.shape[1])

    table += """
            </tbody>
        </table>
    </div>"""

    return table


def get_colors(df):
    """generate distinct colours for all unique names in the cells of df"""

    # remove time allocation/html tags at end of names
    strip_df = df.copy(deep=True)
    for col in strip_df:
        strip_df[col] = strip_df[col].str.replace(r"<br>", "", regex=True)
        strip_df[col] = strip_df[col].str.replace(r"\(\d\.\d\)", "", regex=True)

    # unique names in each column
    names = [strip_df[col].unique() for col in strip_df]

    # unpack list of lists
    names = [cell for column in names for cell in column if cell is not ""]
    # set of names (i.e. unique names in whole sheet)
    # changed to using pd.Series then drop_duplicates to preserve order, i.e. from name appearing first to name
    # appearing last, which helps with keeping colours distinct
    names = pd.Series(names).drop_duplicates().values

    colors = dict()

    # to avoid white, uncomment this line:
    colors["WHITE"] = (1, 1, 1)

    # to avoid black/dark colours, uncomment this line:
    # colors['BLACK'] = (0, 0, 0)

    # to avoid red uncomment this line:
    # colors['RED'] = (1, 0, 0)

    for key in names:
        if "RESOURCE REQUIRED" in key:
            continue
        elif "UNCONFIRMED" in key:
            continue
        elif "DEFERRED" in key:
            continue
        else:
            colors[key] = distinctipy.get_colors(
                1, exclude_colors=list(colors.values())
            )[0]

    return colors


def get_group_colors(df):
    """colour index groups (project programme area or people role)"""
    groups = df.index.get_level_values(0).unique()
    colors = distinctipy.get_colors(len(groups))

    group_colors = {groups[idx]: colors[idx] for idx in range(len(groups))}
    return group_colors


def make_whiteboard(df, key_type, display, update_timestamp=None):
    """Main function to generate the whiteboard visualisation - string containing CSS and HTML code.

    df: a dataframe  with data periods as columns, a multi-index of (role, person) for the people sheet or
    (programme, project) for the project sheet, and cell values of format "name (allocation)"

    key_type: whether this is a project or person visualisation (only used to pick title)

    display: whether to optimise the visualisation for display on a screen or for printing
    """

    if key_type == "project":
        title = "Research Engineering Project Allocations"
    elif key_type == "person":
        title = "Research Engineering Person Allocations"

    if update_timestamp is not None:
        title += " (" + update_timestamp + ")"

    html = write_style(df, display=display)
    html += write_table(df, title)

    return html


if __name__ == "__main__":
    key_type = sys.argv[1]
    display = sys.argv[2]

    if key_type == "person":
        save_dir = "../../data/figs/people"
        file_name = "people.html"
    elif key_type == "project":
        save_dir = "../../data/figs/projects"
        file_name = "projects.html"
    else:
        raise ValueError("first argument (key_type) must be project or person")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print("MAKE WIMBLEDON OBJECT")
    wim = Wimbledon(with_tracked_time=False)

    print("GET WHITEBOARD DATAFRAME")
    df = wim.whiteboard(
        key_type,
        datetime.now() - pd.Timedelta("30 days"),
        datetime.now() + pd.Timedelta("365 days"),
        "MS",
    )

    print("GET FORMATTED HTML WHITEBOARD")
    html = make_whiteboard(df, key_type, display)

    print("SAVE WHITEBOARD")
    with open(save_dir + "/" + file_name, "w") as f:
        f.write(html)
