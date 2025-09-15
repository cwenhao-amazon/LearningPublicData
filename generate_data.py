import os
import json
import glob
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class PlotlyLearningContentViewer:
    def __init__(self, directory_path, content_filter="Testing Frameworks", type_filter="tech_choices"):
        self.directory_path = directory_path
        self.content_filter = content_filter
        self.type_filter = type_filter
        self.json_files = self.get_json_files()
        self.current_json_data = None
        self.filtered_files = self.filter_and_load_files()
        
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
                
        return filtered_files if filtered_files else self.json_files
    
    def load_json_file(self, file_name):
        """Load all data from a selected JSON file."""
        file_path = os.path.join(self.directory_path, file_name)
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return [{"type": "error", "summary": f"Error loading file: {str(e)}", "data": None}]
    
    def get_unique_types(self, json_data):
        """Get unique types from JSON data."""
        if not json_data:
            return []
        return sorted(set(item.get("type", "") for item in json_data if isinstance(item, dict) and item.get("type")))
    
    def get_content_by_type(self, json_data, type_name):
        """Get content of the specified type."""
        if not json_data:
            return "No data loaded"
            
        content_items = [item for item in json_data if isinstance(item, dict) and item.get("type") == type_name]
        
        if not content_items:
            return f"No content found for type: {type_name}"
        
        # Format the content
        formatted_content = ""
        has_matching_content = any(
            self.content_filter in item.get("summary", "")
            for item in content_items
        )
        
        for item in content_items:
            summary = item.get("summary", "No summary available")
            
            # Highlight the filtered content if present
            if self.content_filter in summary and type_name == self.type_filter:
                # Create HTML for highlighting
                highlighted_summary = summary.replace(
                    self.content_filter, 
                    f"<b>{self.content_filter}</b>"
                )
                formatted_content += f"{highlighted_summary}<br><br>"
            else:
                formatted_content += f"{summary}<br><br>"
                
        return formatted_content
    
    def create_interactive_viewer(self):
        """Create an interactive HTML viewer."""
        # Load data for the first file
        first_file = self.filtered_files[0] if self.filtered_files else None
        initial_data = self.load_json_file(first_file) if first_file else []
        initial_types = self.get_unique_types(initial_data)
        
        # Create figure with dropdown for file selection
        fig = make_subplots(rows=2, cols=1, row_heights=[0.15, 0.85], 
                           vertical_spacing=0.05)
        
        # Filter message
        filter_message = f"Showing files containing '{self.content_filter}' in '{self.type_filter}' sections"
        if len(self.filtered_files) < len(self.json_files):
            filter_message += f" ({len(self.filtered_files)}/{len(self.json_files)} files)"
        
        # Add filter information
        fig.add_annotation(
            text=filter_message,
            xref="paper", yref="paper",
            x=0.5, y=0.99,
            showarrow=False,
            font=dict(size=14)
        )
        
        # Add empty content div that will be updated
        fig.add_trace(
            go.Scatter(
                x=[0], y=[0],
                mode="text",
                text=[""],
                hoverinfo="none",
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Create dropdown menus for file and type selection
        file_buttons = []
        for file_name in self.filtered_files:
            # Clean name for display
            display_name = file_name.replace('_learnings.json', '')
            
            file_buttons.append(
                dict(
                    label=display_name,
                    method="update",
                    args=[
                        {},  # No data update needed here
                        {
                            "title": f"Repository: {display_name}"
                        }
                    ],
                    # We'll use custom JavaScript to handle loading data
                )
            )
        
        # Set up the layout
        fig.update_layout(
            title="Learning Content Viewer",
            height=800,
            margin=dict(l=40, r=40, t=120, b=40),
            updatemenus=[
                # File selection dropdown
                dict(
                    buttons=file_buttons,
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.1,
                    xanchor="left",
                    y=1.05,
                    yanchor="top",
                    bgcolor="lightgrey",
                    type="dropdown",
                    name="file_selector"
                ),
            ],
            # Add a div where we'll render content
            annotations=[
                dict(
                    text="Select Content Type:",
                    x=0,
                    y=0.9,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    align="left"
                ),
                dict(
                    text="Select Repository:",
                    x=0,
                    y=1.05,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    align="left"
                )
            ]
        )
        
        # Create a hidden div to store data for JavaScript
        file_data = {}
        for file_name in self.filtered_files:
            data = self.load_json_file(file_name)
            types = self.get_unique_types(data)
            
            type_content = {}
            for type_name in types:
                type_content[type_name] = self.get_content_by_type(data, type_name)
                
            file_data[file_name] = {
                "types": types,
                "content": type_content
            }
        
        # Remove axes
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        
        # Generate HTML
        html_content = fig.to_html(
            include_plotlyjs=True,
            full_html=True,
            include_mathjax=False
        )
        
        # Add JavaScript to handle updating content
        js_code = f"""
        <script>
            // Store all data
            const fileData = {json.dumps(file_data)};
            const filteredFiles = {json.dumps(self.filtered_files)};
            
            // Function to update content based on selections
            function updateContent(fileName, typeName) {{
                const contentDiv = document.getElementById('content-display');
                if (!contentDiv) {{
                    console.error('Content div not found');
                    return;
                }}
                
                if (fileData[fileName] && fileData[fileName].content[typeName]) {{
                    contentDiv.innerHTML = fileData[fileName].content[typeName];
                }} else {{
                    contentDiv.innerHTML = "No content available";
                }}
                
                // Update type buttons
                updateTypeButtons(fileName);
            }}
            
            // Function to update type buttons based on selected file
            function updateTypeButtons(fileName) {{
                const buttonContainer = document.getElementById('type-buttons');
                if (!buttonContainer) {{
                    console.error('Button container not found');
                    return;
                }}
                
                // Clear existing buttons
                buttonContainer.innerHTML = '';
                
                if (fileData[fileName] && fileData[fileName].types) {{
                    fileData[fileName].types.forEach(typeName => {{
                        const btn = document.createElement('button');
                        btn.textContent = typeName;
                        btn.style.margin = '5px';
                        btn.style.padding = '8px 12px';
                        btn.style.cursor = 'pointer';
                        btn.onclick = function() {{ 
                            updateContent(fileName, typeName);
                            
                            // Highlight active button
                            document.querySelectorAll('#type-buttons button').forEach(b => {{
                                b.style.backgroundColor = '';
                                b.style.fontWeight = 'normal';
                            }});
                            btn.style.backgroundColor = '#e0e0e0';
                            btn.style.fontWeight = 'bold';
                        }};
                        buttonContainer.appendChild(btn);
                    }});
                    
                    // Select first type by default
                    if (fileData[fileName].types.length > 0) {{
                        updateContent(fileName, fileData[fileName].types[0]);
                        buttonContainer.firstChild.style.backgroundColor = '#e0e0e0';
                        buttonContainer.firstChild.style.fontWeight = 'bold';
                    }}
                }}
            }}
            
            // Initialize after page loads
            document.addEventListener('DOMContentLoaded', function() {{
                // Add content display div
                const contentDiv = document.createElement('div');
                contentDiv.id = 'content-display';
                contentDiv.style.backgroundColor = 'white';
                contentDiv.style.padding = '20px';
                contentDiv.style.margin = '20px';
                contentDiv.style.border = '1px solid #ddd';
                contentDiv.style.borderRadius = '5px';
                contentDiv.style.height = 'calc(100% - 180px)';
                contentDiv.style.overflowY = 'auto';
                
                // Add button container
                const buttonContainer = document.createElement('div');
                buttonContainer.id = 'type-buttons';
                buttonContainer.style.margin = '10px 20px';
                
                // Insert them into the document
                const plotlyDiv = document.querySelector('.plotly-graph-div');
                plotlyDiv.parentNode.insertBefore(buttonContainer, plotlyDiv.nextSibling);
                plotlyDiv.parentNode.insertBefore(contentDiv, plotlyDiv.nextSibling);
                
                // Handle file dropdown clicks
                document.querySelectorAll('g.updatemenu-item-text').forEach((item, index) => {{
                    item.addEventListener('click', function() {{
                        if (index < filteredFiles.length) {{
                            updateTypeButtons(filteredFiles[index]);
                        }}
                    }});
                }});
                
                // Initialize with the first file
                if (filteredFiles.length > 0) {{
                    updateTypeButtons(filteredFiles[0]);
                }}
            }});
        </script>
        <style>
            #content-display h1 {{ font-size: 24px; margin-top: 0; }}
            #content-display h2 {{ font-size: 20px; }}
            #content-display h3 {{ font-size: 18px; }}
            #content-display p {{ margin-bottom: 16px; }}
            #content-display b {{ background-color: #ffffcc; font-weight: bold; }}
            #type-buttons button:hover {{ background-color: #f0f0f0; }}
        </style>
        """
        
        # Add the JavaScript to the HTML
        html_content = html_content.replace('</body>', f'{js_code}</body>')
        
        return html_content
        
    def save_viewer(self, output_path='learning_content_viewer.html'):
        """Save the interactive viewer to an HTML file."""
        html_content = self.create_interactive_viewer()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Interactive viewer saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving interactive viewer: {e}")
            return False

# Usage example
directory_path = "/home/cwenhao/workplace/BigWeaverContextLearningsLambdaWorkSpace/src/BigWeaverContextLearningsLambda/test/local/output/huggingface_sonnet3_7/repo_learning/learnings"
viewer = PlotlyLearningContentViewer(
    directory_path,
    #content_filter="Testing Frameworks",
    #type_filter="tech_choices"
)
viewer.save_viewer("index.html")