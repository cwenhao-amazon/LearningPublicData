import os
import json
import glob
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import markdown
import re

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
                    # Check if any item matches our filters
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
    
    def get_content_types(self, json_data):
        """Get unique content types from the JSON data."""
        if not json_data:
            return []
        types = set(item.get("type", "") for item in json_data if isinstance(item, dict))
        return sorted([t for t in types if t])
    
    def get_content_by_type(self, json_data, type_name):
        """Get content items of the selected type."""
        if not json_data:
            return []
        return [item for item in json_data if isinstance(item, dict) and item.get("type") == type_name]


# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # For Gunicorn deployment

# Define app layout
def setup_dash_app(viewer):
    # Filter files that match our criteria
    filtered_file_list = viewer.filter_and_load_files()
    
    # Use filtered files if available, otherwise use all files
    display_files = filtered_file_list if filtered_file_list else viewer.json_files
    
    # Create filter indicator message
    if filtered_file_list:
        filter_msg = f"Showing {len(filtered_file_list)} files containing '{viewer.content_filter}' in '{viewer.type_filter}' sections"
    else:
        filter_msg = f"No files found containing '{viewer.content_filter}' in '{viewer.type_filter}' sections. Showing all files."
    
    app.layout = html.Div([
        html.H1("Learning Content Viewer", style={'textAlign': 'center'}),
        
        html.Div([
            html.P(filter_msg, style={'marginBottom': '10px'})
        ]),
        
        html.Div([
            html.Label("Select file:"),
            dcc.Dropdown(
                id='file-dropdown',
                options=[{'label': f, 'value': f} for f in display_files],
                value=display_files[0] if display_files else None,
                style={'width': '80%'}
            )
        ]),
        
        html.Div([
            html.Label("Select content type:"),
            html.Div(id='type-buttons', style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '10px', 'marginTop': '10px'})
        ]),
        
        html.Div(id='content-display', style={'marginTop': '20px', 'padding': '15px', 'border': '1px solid #ddd'})
    ])
    
    # Setup callbacks
    @app.callback(
        Output('type-buttons', 'children'),
        Input('file-dropdown', 'value')
    )
    def update_type_buttons(selected_file):
        if not selected_file:
            return []
        
        json_data = viewer.load_json_file(selected_file)
        types = viewer.get_content_types(json_data)
        
        return [
            html.Button(
                type_name,
                id={'type': 'type-button', 'index': i},
                n_clicks=0,
                style={
                    'padding': '10px 15px',
                    'marginRight': '10px',
                    'marginBottom': '5px',
                    'borderRadius': '5px',
                    'border': '1px solid #ccc',
                    'cursor': 'pointer'
                }
            ) for i, type_name in enumerate(types)
        ]
    
    @app.callback(
        Output('content-display', 'children'),
        [
            Input('file-dropdown', 'value'),
            Input({'type': 'type-button', 'index': dash.dependencies.ALL}, 'n_clicks')
        ],
        [State({'type': 'type-button', 'index': dash.dependencies.ALL}, 'children')]
    )
    def update_content(selected_file, button_clicks, button_types):
        ctx = dash.callback_context
        
        if not selected_file:
            return html.P("Please select a file to view content")
        
        json_data = viewer.load_json_file(selected_file)
        
        # Determine which type to display
        selected_type = None
        
        if ctx.triggered and "type-button" in ctx.triggered[0]["prop_id"]:
            # A type button was clicked
            button_index = ctx.triggered_id['index']
            if button_index < len(button_types):
                selected_type = button_types[button_index]
        else:
            # Initial load or file dropdown change
            # First look for type containing our filter text
            matching_items = [
                item for item in json_data 
                if isinstance(item, dict) and 
                item.get("type") == viewer.type_filter and
                "summary" in item and
                viewer.content_filter in item.get("summary", "")
            ]
            
            if matching_items:
                selected_type = viewer.type_filter
            elif json_data and isinstance(json_data, list) and len(json_data) > 0:
                types = viewer.get_content_types(json_data)
                if types:
                    selected_type = types[0]
        
        if not selected_type:
            return html.P("No content found in the selected file")
        
        content_items = viewer.get_content_by_type(json_data, selected_type)
        
        if not content_items:
            return html.P(f"No content found for type: {selected_type}")
        
        # Extract the filename without the _learnings.json suffix
        repo_name = selected_file.replace('_learnings.json', '')
        
        # Prepare content
        content_elements = []
        
        # Add header
        content_elements.append(html.H2(f"{repo_name} - {selected_type.replace('_', ' ').title()}"))
        
        # Check if this type has our filter
        has_matching_content = any(
            viewer.content_filter in item.get("summary", "")
            for item in content_items
        )
        
        # Add note if this is our target type and has our filter
        if selected_type == viewer.type_filter and has_matching_content:
            content_elements.append(html.P(
                f"This section contains '{viewer.content_filter}'",
                style={'fontStyle': 'italic'}
            ))
        
        # Add each item's summary
        for item in content_items:
            summary = item.get("summary", "No summary available")
            
            # Highlight the filtered content if present
            if viewer.content_filter in summary and selected_type == viewer.type_filter:
                # Split by the filter term to highlight it
                parts = summary.split(viewer.content_filter)
                highlighted_summary = []
                
                for i, part in enumerate(parts):
                    highlighted_summary.append(html.Span(part))
                    if i < len(parts) - 1:  # Don't add after the last part
                        highlighted_summary.append(html.Strong(viewer.content_filter))
                        
                content_elements.append(html.P(highlighted_summary))
            else:
                content_elements.append(html.P(summary))
        
        return content_elements

# Main function to run app
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Learning Content Viewer')
    parser.add_argument('--dir', default="/home/cwenhao/workplace/BigWeaverContextLearningsLambdaWorkSpace/src/BigWeaverContextLearningsLambda/test/local/output/huggingface_sonnet3_7/repo_learning/learnings", 
                        help='Directory path containing JSON files')
    parser.add_argument('--filter', default="Testing Frameworks",
                        help='Content filter text')
    parser.add_argument('--type', default="tech_choices",
                        help='Type filter')
    parser.add_argument('--port', default=8050, type=int,
                        help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host to run the server on')
    
    args = parser.parse_args()
    
    viewer = LearningContentViewer(
        directory_path=args.dir,
        content_filter=args.filter,
        type_filter=args.type
    )
    
    setup_dash_app(viewer)
    
    # Run the app
    app.run(debug=True, host=args.host, port=args.port)

if __name__ == '__main__':
    main()