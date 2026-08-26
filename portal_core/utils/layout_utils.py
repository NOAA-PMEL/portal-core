from dash import html
from portal_core.constants import (
    _section_label_style,
    _hr_style
)

def _section_label(text, guidelines=None):
    """Blue uppercase section header with a trailing HR line."""
    
    label_row = html.Div(
        style=_section_label_style,
        children=[
            html.Span(text),
            guidelines
        ] if guidelines else [html.Span(text)]

    )

    return html.Div(
            style=_section_label_style,
            children=[label_row, html.Hr(style=_hr_style)]
        )