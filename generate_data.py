import os
import json
import glob
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import markdown

class LearningContentViewer:
    def __init__(self, directory_path, content_filter="Testing Frameworks", type_filter="tech_choices"):
        self.directory_path = directory_path
        self.content_filter = content_filter
        self.type_filter = type_filter
        self.json_files = self.get_json_files()
        
    def get_json_files(self):
        """Get all JSON files in the specified directory."""
        file_pattern = os.path.join(self.directory_path, "*_learnings.json")
        files = glob.glob(file_pattern)
        return [os.path.basename(f) for f in files]
    
    def filter_and_load_files(self):
        """Load all files and filter by content and type."""
        filtered_files = []
        
        for file_name in self.json_files:
            file_path = os.path.join(self.directory_path, file_name)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if any(
                        isinstance(item, dict) and 
                        item.get("type") == self.type_filter and
                        "summary" in item and 
                        isinstance(item["summary"], str) and
                        self.content_filter in item["summary"]
                        for item in data
                    ):
                        filtered_files.append(file_name)
            except Exception as e:
                print(f"Error loading {file_name}: {e}")
                
        return filtered_files
    
    def load_json_file(self, file_name):
        """Load all data from a selected JSON file."""
        file_path = os.path.join(self.directory_path, file_name)
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return [{"type": "error", "summary": f"Error loading file: {str(e)}", "data": None}]

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Learning Content Viewer"

# Configure for GitHub Pages
server = app.server

# Directory path - modify this to your data directory
directory_path = "data/learnings"

# Initialize the viewer
viewer = LearningContentViewer(directory_path)

# Get filtered files
filtered_files = viewer.filter_and_load_files()
display_files = filtered_files if filtered_files else viewer.json_files

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Learning Content Viewer", className="mt-3 mb-4"),
            
            # Filter indicator
            html.Div(
                id="filter-indicator",
                children=(f"Showing {len(filtered_files)} files containing '{viewer.content_filter}' " +
                          f"in '{viewer.type_filter}' sections") if filtered_files else 
                         f"No files found containing '{viewer.content_filter}' in '{viewer.type_filter}' sections. " +
                         "Showing all files.",
                className="mb-3"
            ),
            
            # File selection dropdown
            dbc.Label("Select file:"),
            dcc.Dropdown(
                id='file-dropdown',
                options=[{'label': file, 'value': file} for file in display_files],
                value=display_files[0] if display_files else None,
                className="mb-4"
            ),
            
            # Type buttons
            html.Div([
                dbc.Label("Select content type:"),
                html.Div(id='type-buttons', className="mb-4")
            ]),
            
            # Content display
            html.Div(id='content-output', className="p-3 border rounded")
        ], width=12)
    ])
], fluid=True)

@app.callback(
    Output('type-buttons', 'children'),
    Output('content-output', 'children'),
    Input('file-dropdown', 'value'),
    State('content-output', 'children')
)
def update_content(selected_file, current_content):
    if not selected_file:
        return [], html.P("Please select a file to view content")
        
    # Load JSON file
    json_data = viewer.load_json_file(selected_file)
    
    # Get unique types from the JSON data
    types = set(item.get("type", "") for item in json_data if isinstance(item, dict) and item.get("type"))
    
    # Create type buttons
    type_buttons = dbc.ButtonGroup([
        dbc.Button(
            type_name.replace('_', ' ').title(),
            id={'type': 'type-button', 'index': type_name},
            color="primary",
            outline=True,
            className="me-2 mb-2"
        ) for type_name in sorted(types) if type_name
    ])
    
    # Find the default type to display
    default_type = None
    
    # First look for the type containing our filter text
    matching_items = [
        item for item in json_data 
        if isinstance(item, dict) and 
        item.get("type") == viewer.type_filter and
        "summary" in item and
        viewer.content_filter in item.get("summary", "")
    ]
    
    if matching_items:
        default_type = viewer.type_filter
    elif json_data and isinstance(json_data, list) and len(json_data) > 0:
        # If no match, show the first available type
        first_item = json_data[0]
        if isinstance(first_item, dict) and "type" in first_item:
            default_type = first_item["type"]
    
    if not default_type:
        return type_buttons, html.P("No content found in the selected file")
    
    # Get content for the default type
    return type_buttons, generate_content_html(selected_file, json_data, default_type, viewer.content_filter, viewer.type_filter)

@app.callback(
    Output('content-output', 'children', allow_duplicate=True),
    Input({'type': 'type-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    State('file-dropdown', 'value'),
    prevent_initial_call=True
)
def display_content_by_type(button_clicks, selected_file):
    if not button_clicks or not any(button_clicks) or not selected_file:
        return dash.no_update
    
    # Find which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if not button_id:
        return dash.no_update
        
    # Extract the type_name from the button ID
    try:
        button_dict = json.loads(button_id)
        type_name = button_dict['index']
    except:
        return dash.no_update
    
    # Load JSON file
    json_data = viewer.load_json_file(selected_file)
    
    # Generate content HTML
    return generate_content_html(selected_file, json_data, type_name, viewer.content_filter, viewer.type_filter)

def generate_content_html(file_name, json_data, type_name, content_filter, type_filter):
    """Generate HTML content for the specified type."""
    content_items = [item for item in json_data if isinstance(item, dict) and item.get("type") == type_name]
    
    if not content_items:
        return html.P(f"No content found for type: {type_name}")
    
    # Extract the repository name
    repo_name = file_name.replace('_learnings.json', '')
    
    # Create the content elements
    content_elements = [
        html.H2(f"{repo_name} - {type_name.replace('_', ' ').title()}")
    ]
    
    # Check if any item contains our filter
    has_matching_content = any(
        content_filter in item.get("summary", "")
        for item in content_items
    )
    
    # If this is our target type and has our filter, add a note
    if type_name == type_filter and has_matching_content:
        content_elements.append(
            html.Em(f"This section contains '{content_filter}'")
        )
    
    # Add each item's summary
    for item in content_items:
        summary = item.get("summary", "No summary available")
        
        # Highlight the filtered content if present
        if content_filter in summary and type_name == type_filter:
            # Split text at the filter term and wrap it with bold tag
            parts = summary.split(content_filter)
            marked_content = []
            
            for i, part in enumerate(parts):
                marked_content.append(part)
                if i < len(parts) - 1:  # Don't add filter text after the last part
                    marked_content.append(html.Strong(content_filter))
            
            content_elements.append(html.P(marked_content))
        else:
            content_elements.append(
                html.P(summary)
            )
    
    return content_elements

if __name__ == '__main__':
    app.run_server(debug=True)