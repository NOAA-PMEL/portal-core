"""
Utility functions for displaying file lists across the application
(in wizard and submission table)
"""
import os
from dash import html
from portal_core.constants import UPLOAD_DIRECTORY

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes is None:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def create_file_item(filename, file_size=None, file_type=None, file_id=None, show_delete=True, context='wizard'):
    """
    Helper function to create a styled file list item.
    Return htmlDiv containg the formatted file item
    """
    # Format file_size if its a number
    if isinstance(file_size, (int, float)):
        file_size = format_file_size(file_size)

    # Choose delete button ID based on context
    if context == 'wizard':
        delete_id = {'type': 'wizard-delete-file', 'index': file_id}
    elif context == 'dropdown':
        delete_id = {'type': 'dropdown-delete-file', 'index': file_id}
    else:
        delete_id = {'type': 'generic-delete-file', 'index': file_id}

    return html.Div([
        html.Div([
            # FIle icon and name
            html.Span('📄', style={'marginRight': '8px', 'fontSize': '16px'}),
            html.Span(filename, style={
                'color': '#e0e0e0',
                'fontWeight': 'bold',
                'flex': 1,
                'wordBreak': 'break-word'
            }),
        ], style={'display': 'flex', 'alignItems': 'center', ' marginBottom': '5px'}),

        # File details row
        html.Div([
            html.Span(f"Type: {file_type or 'Unknown'}", style={
                'color': '#999',
                'fontSize': '12px',
                'marginRight': '15px'
            }),
            html.Span(f"Size: {file_size or 'Unknown'}", style={
                'color': '#999', 
                'fontSize': '12px'
            }),
            html.Span('Delete', 
            id=delete_id if file_id else None,
            n_clicks=0, 
            style={
                'color': 'red',
                'fontSize': '12px',
                'marginLeft': 'auto',
                'cursor': 'pointer',
                'textDecoration': 'underline',
                'display': 'inline-block' if show_delete else 'none'
            }
            ) if show_delete else None
        ], style={'display': 'flex', 'alignItems': 'center'}),      
    ], style={
        'padding': '12px',
        'backgroundColor': '#212121',
        'borderRadius': '5px',
        'marginBottom': '10px',
        'border': '1px solid #444'
    })

def create_file_list_from_dataframe(df, submission_id, show_delete=True, context='wizard', empty_message=None):
    """
    Create a list of file items from a dataframe.
    Returns a list of html.Div elements representing files
    """
    if df.empty:
        default_message = "No files uploaded yet" if context=='wizard' else " No files in this submission"
        message = empty_message or default_message
        return [html.Div(message, style={'color': '#999', 'fontStyle': 'italic', 'padding': '10px'})]

    file_list = []
    for _, row in df.iterrows():
        # Calculate file size
        file_path = os.path.join(UPLOAD_DIRECTORY, str(submission_id), row['filename'])
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None

        file_list.append(
            create_file_item(
                filename=row['filename'],
                file_size=file_size,
                file_type=row['filename'].split('.')[-1].upper(),
                file_id=row['id'],
                show_delete=show_delete,
                context=context
            )
        )
    return file_list

def _normalize_upload(contents, filename):
    """
    dcc.Upload return scalars when mutliple=False and lists when multiple=True. 
    instance config varies by portal, so normalize by runtime.
    """
    if contents is None:
        return [], []
    if not isinstance(contents, list):
        return [contents], [filename]
    return contents, filename

