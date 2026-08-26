import xarray as xr
# import cf_xarray as cf
import pandas as pd
import dash_design_kit as ddk
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import csv
import re
import math
import numpy as np

from portal_core.utils.logger import app_logger as log
import logging

def make_preview(file):

    log.setLevel(logging.ERROR)
    previous_level = log.getEffectiveLevel()

    cards = []
    if file.endswith('.nc'):
        try:
            ds = xr.open_dataset(file)
        except Exception as e:
            return [ddk.Card(children=[ddk.CardHeader(title='netCDF error opening the file.'), str(e)])]
        ds = ds.squeeze()
        df = ds.to_dataframe()
        df.reset_index(inplace=True)
        dsg_type = None
        if 'cdm_data_type' in ds.attrs:
            dsg_type = ds.attrs['cdm_data_type']
        else:
            return [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),'No cdm_data_type attribute.'])]
        if 'profile' in dsg_type.lower():
            variables = []
            for var in ds.data_vars:
                if ds[var].dtype.kind in 'iuf':
                    variables.append(var)
            # Find depth and time
            vertical = []
            depth = None
            times = []
            time = None
            for var in ds.variables:
                if 'depth' in var.lower() or 'pres' in var.lower():
                    vertical.append(var)
                if 'time' in var.lower():
                    times.append(var)
            if len(vertical) > 0:
                depth = vertical[0]
            if depth is None:
                return [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),'Data type is profile, but no depth or pressure variable found.'])]
            # Find time
            if len(times) > 0:
                if 'time' in times:
                    time = 'time'
                else:
                    time = times[0]
            if time is None:
                return  [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),'Data type is profile, but no time variable found.'])]
            data_lat = None
            data_lon = None
            for var in ds.cf[['latitude']].variables:
                if var in ds.data_vars:
                    if ds.cf[var].dims[0] == "obs" or ds.cf[var].dims[0] == "sample":
                        data_lat = var
            for var in ds.cf[['longitude']].variables:
                if var in ds.data_vars:
                    if ds.cf[var].dims[0] == "obs" or ds.cf[var].dims[0] == "sample":
                        data_lon = var
            # Get the profile_id:
            profile_id = None
            if 'profile_id' in ds.cf.cf_roles:
                profile_id = ds.cf.cf_roles['profile_id'][0]
            if profile_id is None:
                return  [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),'Data type is profile, but no profile id variable found.'])]
            variables = []
            for var in ds.data_vars:
                if ds[var].dtype.kind in 'iuf':
                    # Plot only int, unsigned int and float variables, others don't need a preview
                    variables.append(var)
            log.debug('[make_preview] total before sample', f'{df.shape[0] * df.shape[1]:,}')
            per_plot = math.ceil(50_000/len(variables))
            log.debug('[make_preview] points per variable', per_plot)
            # TOTO need a better way to sub-sample profiles. With large collections this crashed the whole pod
            # sample_df = stratified_sample_2cols(df, profile_id, depth, time, per_plot/(df.shape[0]*df.shape[1]))
            pids = list(df[profile_id].unique())
            first_id = pids[0]
            sample_df = df.loc[df[profile_id]==first_id]
            log.debug('[make_preview] total after sample', f'{sample_df.shape[0] * sample_df.shape[1]:,}')
            vlen = (len(variables))/3
            rows = math.ceil(vlen)
            log.debug('[make_preview] rows',rows)
            figure = make_subplots(rows=rows, cols=3, subplot_titles=variables, row_heights=rows*[1/rows])
            row = 1
            column = 1

            for idx, var in enumerate(variables):
                sample_vars = [profile_id, var, time]
                if depth not in sample_vars:
                    sample_vars.append(depth)
                if data_lon in df.columns and df[data_lon].size == df[var].size:
                    if data_lon not in sample_vars:
                        sample_vars.append(data_lon)
                if data_lat in df.columns and df[data_lat].size == df[var].size:
                    if data_lat not in sample_vars:
                        sample_vars.append(data_lat)
                if df[sample_vars].shape[0] > per_plot:
                    sample_df = df[sample_vars].sample(n=per_plot)
                else:
                    sample_df = df[sample_vars]
                sample_df['text'] = sample_df.apply(lambda row: expression(row, sample_vars), axis=1)
                plot = go.Scattergl(x=sample_df[time],
                                    y=sample_df[depth],
                                    mode='markers',                                    
                                    text=sample_df['text'],
                                    hoverinfo='text',
                                    marker=dict(
                                        # size=10,
                                        color=sample_df[var],
                                        colorscale='Viridis',  # Apply a colorscale
                                        showscale=False  # Show colorbar
                                    )
                )
                figure.add_trace(plot, row=row, col=column)
                column = column + 1
                if column == 4:
                    column = 1
                    row = row + 1
            profile_count = len(pids)
            figure.update_layout(height=350*rows, margin={'t':60}, coloraxis_showscale=False, showlegend=False, title=f'Preview of first profile of {profile_count} profiles.')
            figure.update_yaxes(autorange='reversed')
            cards.append(ddk.Graph(figure=figure))
            return cards
        elif 'timeseries' in dsg_type.lower() or 'trajectory' in dsg_type.lower():
            vertical = []
            times = []
            time_name = None
            for var in ds.variables:
                if 'depth' in var.lower() or 'pres' in var.lower():
                    vertical.append(var)
                if 'time' in var.lower():
                    times.append(var)
            if len(times) > 0:
                if 'time' in times:
                    time_name = 'time'
                else:
                    time_name = times[0]
            if time_name is None:
                return  [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),'Could not determine the time varaible for timeseries.'])]
            variables = []
            for var in ds.data_vars:
                if ds[var].dtype.kind in 'iuf':
                    variables.append(var)
            per_plot = math.ceil(50_000/len(variables))
            log.debug('[make_preview] points per variable', per_plot)
            vlen = (len(variables))/3
            rows = math.ceil(vlen)
            log.debug('[make_preview] rows',rows)
            figure = make_subplots(rows=rows, cols=3, subplot_titles=variables, row_heights=rows*[1/rows])
            row = 1
            column = 1
            for idx, var in enumerate(variables):
                ts_vars = [time_name, var]
                log.debug(f'[make_preview] plotting {ts_vars}')
                log.debug(f'[make_preview] from {list(df.columns)}')
                if df.shape[0] > per_plot:
                    sample_df = df[ts_vars].sample(n=per_plot)
                else:
                    sample_df = df
                log.debug(f'[make_preview] resulting in {list(sample_df.columns)}')
                sample_df['text'] = sample_df.apply(lambda row: expression(row, ts_vars), axis=1)
                plot = px.scatter(sample_df,
                            x=time_name,
                            y=var,
                            hover_data=[time_name,var],
                        )
                plot.update_layout(showlegend=False)
                traces = list(plot.select_traces())
                figure.add_traces(traces, row, column)
                column = column + 1
                if column == 4:
                    column = 1
                    row = row + 1
            figure.update_layout(height=350*rows, margin={'t':20}, coloraxis_showscale=False, showlegend=False)
            cards.append(ddk.Graph(figure=figure))
            return cards
        elif 'point' in dsg_type.lower():
            return ['a point data set']
        else:
            return  [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),f'Unknown geometry type: {dsg_type}'])]
    elif file.endswith('.csv'):
        log.debug(f'[make_preview] Opending file {file}')
        skips, header_rows = find_data_start(file)
        log.debug(f'[make_preview] Skipping {skips}')
        try:
            df = pd.read_csv(file, skiprows=skips)
        except Exception as e:
            return [ddk.Card(children=[ddk.CardHeader(title='Error opening the file.'), str(e)])]
        log.debug(f'[make_preview] File read complete {df.head()}')
        # This will remove any character that is not in the RegEx set, like some column names have \r and the like
        df.rename(columns=lambda c: re.sub('[^a-zA-Z0-9 ]', '_', c), inplace=True)
        columns = list(df.columns)
        log.debug(f"column names {columns}")
        time_col = [item for item in columns if 'time' in item.lower()]
        date_col = [item for item in columns if 'date' in item.lower()]
        time_name = None
        date_name = None
        time_column = None
        if len(time_col) > 0:
            # DEBUG 
            log.debug('[make_preview] columns with time', time_col, 'potential name', time_col[0])
            time_name = time_col[0]
            # DEBUG 
            log.debug(f'[make_preview] time name found {time_name}')
        if len(date_col) > 0:
            # DEBUG
            log.debug('[make_preview] columns with date {date_col} potential name {date_col[0]}')
            date_name = date_col[0]
            log.debug('[make_preview] date name found', date_name)
        if time_name is None and date_name is None:
            return  [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),'Unable to find time or date column.'])]
        elif time_name is not None:
            time_column = time_name
        elif date_name is not None:
            time_column = date_name
        if time_column is None:
            return  [ddk.Card(children=[ddk.CardHeader(title='No preview available.'),'Unable to find time column.'])]
        # DEBUG 
        log.debug(f'[make_preview] time column is called {time_column}')
        df = df.sort_values([time_column])
        variables = list(df.columns)
        variables.remove(time_column)
        vlen = (len(variables))/3
        rows = math.ceil(vlen)
        log.debug('[make_preview] rows',rows)
        figure = make_subplots(rows=rows, cols=3, subplot_titles=variables, row_heights=rows*[1/rows])
        row = 1
        column = 1
        for idx, var in enumerate(variables):
            log.debug(f'[make_preview] ploting variable {var}')
            limit = math.ceil(50_000/len(variables))
            if df.shape[0] < limit:
                sample_df = df
            else:
                sample_df = df[[time_column, var]].sample(n=limit)
            sample_df = sample_df.sort_values([time_name])
            plot = px.scatter(sample_df,
                        x=time_name,
                        y=var,
                        hover_data=[time_name,var],
                    )
            plot.update_layout(showlegend=False)
            traces = list(plot.select_traces())
            figure.add_traces(traces, row, column)
            column = column + 1
            if column == 4:
                column = 1
                row = row + 1
        figure.update_layout(height=350*rows, margin={'t':20}, showlegend=False)
        cards.append(ddk.Graph(figure=figure))
        return cards
    else:
        cards = ["No preview available."]
    log.setLevel(previous_level)
    return cards


def expression(row, svars):
    text = ''
    for var in svars:
        text = text + f'{var}={row[var]}<br>'
    return text

def count_headers(filename, max_header_rows=2):
    sniffer = csv.Sniffer()
    header_rows = 0
    for offset in range(max_header_rows):
        sample = sample_lines(filename, offset, max_header_rows)
        if (sniffer.has_header(sample)):
            header_rows = header_rows + 1
    return header_rows


def sample_lines(filename, start, sample_size):
    sample = ''
    with open(filename,"r") as fp:
        for i in range(start):
            discard = fp.readline()
        for i in range(sample_size):
            sample = sample + fp.readline()
    return sample


def stratified_sample_2cols(df, col1, col2, time_column, size_percent):
    """
    Generates a stratified random sample from a Pandas DataFrame,
    based on the combination of two columns, with a defined percentage
    of the total number of points. 
    
    Also keep only about half the profiles, by keeping only half the times.

    Args:
        df (pd.DataFrame): The input DataFrame.
        col1 (str): The name of the first column for stratification.
        col2 (str): The name of the second column for stratification.
        size_percent (float): The desired sample size as a percentage of the total data, e.g., 0.2 for 20%.

    Returns:
        pd.DataFrame: A DataFrame containing the stratified sample.
    """
    if not 0 < size_percent <= 1:
        raise ValueError("size_percent must be between 0 and 1")

    # Combine the two columns to create unique groups
    df['combined_group'] = df[col1].astype(str) + '_' + df[col2].astype(str)

    # Calculate the sample size per group, ensuring it's at least 1
    sample_size_per_group = np.maximum(1, (df['combined_group'].value_counts(normalize=True) * len(df) * size_percent).round().astype(int))

    sampled_df = df.groupby('combined_group', group_keys=False).apply(lambda x: x.sample(n=min(len(x), sample_size_per_group[x.name])))

    # Only keep about half the times

    times = sampled_df[time_column].unique()
    sample_times = times[::2]

    sampled_df = sampled_df.loc[sampled_df['time'].isin(sample_times)]

    sampled_df = sampled_df.drop(columns=['combined_group'])

    return sampled_df


def find_data_start(csv_filepath):
    """
    Examines a CSV file with potential random text at the top and finds the row where the data starts.

    Args:
        csv_filepath (str): The path to the CSV file.

    Returns:
        int: The row number (0-based index) where the data starts, or None if no valid data is found.
    """
    skips = []
    headers = []
    try:
        header_count = -1
        max_row_len = -1
        with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            row_num = 0
            for row in reader:
                if row:  # Check if the row is not empty
                    try:
                        if len(row) > max_row_len:
                            max_row_len = len(row)
                        # Attempt to convert the first element of the row to a number (or some other data type)
                        # to determine if it is a header or data row.
                        row_floats = 0
                        for item in row:
                            try:
                                float(item)
                                row_floats = row_floats + 1
                            except:
                                pass
                        if row_floats/len(row) > .5:
                            log.debug('[make_preview] breaking')
                            header_count = row_num - 1 # if the prior check does not throw an error, we have found the data.
                            break # I hate this, but we have more work to do
                    except (ValueError, IndexError):
                        # If conversion fails or the row is empty, it's likely a header or random text.
                        pass
                row_num += 1
            csvfile.seek(0)
            reader = csv.reader(csvfile)
            row_num = 0
            for row in reader:
                if len(row) < max_row_len:
                    skips.append(row_num)
                else:
                    log.debug(row)
                    log.debug('[make_preview] blank entries', row.count(''))
                    if row.count('') == 0:
                        log.debug('[make_preview] adding to headers')
                        headers.append(row_num)
                    else:
                        log.debug('[make_preview] adding to skips')
                        skips.append(row_num)
                row_num += 1
                if row_num > header_count:
                    break
            return skips, headers
    except FileNotFoundError:
        log.debug(f"Error: File not found at {csv_filepath}")
        return skips, headers
    except Exception as e:
        log.debug(f"An unexpected error occurred: {e}")
        return skips, headers