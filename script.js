class LearningContentViewer {
    constructor(dataDirectory, contentFilter = "Testing Frameworks", typeFilter = "tech_choices") {
        this.dataDirectory = dataDirectory;
        this.contentFilter = contentFilter;
        this.typeFilter = typeFilter;
        this.jsonFiles = [];
        this.currentJsonData = null;
        
        this.fileSelect = document.getElementById('file-select');
        this.typeButtonsContainer = document.getElementById('type-buttons');
        this.contentOutput = document.getElementById('content-output');
        this.filterInfo = document.getElementById('filter-info');
        
        this.init();
    }
    
    async init() {
        await this.fetchJsonFiles();
        this.setupEventListeners();
    }
    
    async fetchJsonFiles() {
        try {
            // Fetch the list of JSON files from a manifest or directory listing
            const response = await fetch(`${this.dataDirectory}/file_manifest.json`);
            const files = await response.json();
            
            this.jsonFiles = files.filter(file => file.endsWith('_learnings.json'));
            
            // Filter files based on content and type
            const filteredFiles = [];
            for (const fileName of this.jsonFiles) {
                const fileData = await this.loadJsonFile(fileName);
                if (this.fileContainsFilteredContent(fileData)) {
                    filteredFiles.push(fileName);
                }
            }
            
            // Update filter info
            this.updateFilterInfo(filteredFiles.length > 0 ? filteredFiles.length : 0);
            
            // Use filtered files or all files
            const displayFiles = filteredFiles.length > 0 ? filteredFiles : this.jsonFiles;
            
            // Populate the file dropdown
            this.fileSelect.innerHTML = '';
            displayFiles.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                this.fileSelect.appendChild(option);
            });
            
            // Load the first file if available
            if (displayFiles.length > 0) {
                this.fileSelect.value = displayFiles[0];
                await this.handleFileSelection(displayFiles[0]);
            }
        } catch (error) {
            console.error("Error fetching file list:", error);
            this.contentOutput.innerHTML = `<p>Error loading files: ${error.message}</p>`;
        }
    }
    
    fileContainsFilteredContent(data) {
        return data.some(item => 
            item && 
            typeof item === 'object' &&
            item.type === this.typeFilter && 
            item.summary && 
            typeof item.summary === 'string' && 
            item.summary.includes(this.contentFilter)
        );
    }
    
    updateFilterInfo(count) {
        let message;
        if (count > 0) {
            message = `Showing ${count} files containing '<strong>${this.contentFilter}</strong>' in '<strong>${this.typeFilter}</strong>' sections`;
        } else {
            message = `No files found containing '<strong>${this.contentFilter}</strong>' in '<strong>${this.typeFilter}</strong>' sections. Showing all files.`;
        }
        this.filterInfo.innerHTML = message;
    }
    
    async loadJsonFile(fileName) {
        try {
            const response = await fetch(`${this.dataDirectory}/${fileName}`);
            return await response.json();
        } catch (error) {
            console.error(`Error loading ${fileName}:`, error);
            return [{ type: "error", summary: `Error loading file: ${error.message}`, data: null }];
        }
    }
    
    setupEventListeners() {
        this.fileSelect.addEventListener('change', async (event) => {
            await this.handleFileSelection(event.target.value);
        });
    }
    
    async handleFileSelection(fileName) {
        this.currentJsonData = await this.loadJsonFile(fileName);
        this.updateTypeButtons();
        this.displaySelectedContent();
    }
    
    updateTypeButtons() {
        if (!this.currentJsonData) return;
        
        // Clear existing buttons
        this.typeButtonsContainer.innerHTML = '';
        
        // Get unique types
        const types = [...new Set(
            this.currentJsonData
                .filter(item => item && typeof item === 'object' && item.type)
                .map(item => item.type)
        )].sort();
        
        // Create buttons
        types.forEach(type => {
            const button = document.createElement('button');
            button.textContent = type;
            button.className = 'type-button';
            button.addEventListener('click', () => {
                // Remove active class from all buttons
                document.querySelectorAll('.type-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                // Add active class to clicked button
                button.classList.add('active');
                this.displayContentByType(type);
            });
            this.typeButtonsContainer.appendChild(button);
        });
    }
    
    displayContentByType(typeName) {
        if (!this.currentJsonData) {
            this.contentOutput.innerHTML = "<p>No data loaded</p>";
            return;
        }
        
        const contentItems = this.currentJsonData.filter(
            item => item && typeof item === 'object' && item.type === typeName
        );
        
        if (contentItems.length === 0) {
            this.contentOutput.innerHTML = `<p>No content found for type: ${typeName}</p>`;
            return;
        }
        
        // Extract repository name
        const repoName = this.fileSelect.value.replace('_learnings.json', '');
        
        // Check if any item contains our filter
        const hasMatchingContent = contentItems.some(
            item => item.summary && item.summary.includes(this.contentFilter)
        );
        
        // Create content
        let contentHtml = `<h2>${repoName} - ${typeName.replace('_', ' ').charAt(0).toUpperCase() + typeName.replace('_', ' ').slice(1)}</h2>`;
        
        // Add note about filter if applicable
        if (typeName === this.typeFilter && hasMatchingContent) {
            contentHtml += `<em>This section contains '${this.contentFilter}'</em>`;
        }
        
        // Add each item's summary
        contentItems.forEach(item => {
            if (!item.summary) return;
            
            let summary = item.summary;
            
            // Highlight filtered content if present
            if (this.contentFilter && typeName === this.typeFilter && summary.includes(this.contentFilter)) {
                summary = summary.replace(
                    new RegExp(this.contentFilter, 'g'),
                    `<span class="highlight">${this.contentFilter}</span>`
                );
            }
            
            // Convert markdown to HTML
            contentHtml += `<div>${marked.parse(summary)}</div>`;
        });
        
        this.contentOutput.innerHTML = contentHtml;
    }
    
    displaySelectedContent() {
        if (!this.currentJsonData) {
            this.contentOutput.innerHTML = "<p>Please select a file to view content</p>";
            return;
        }
        
        // First look for the type containing our filter text
        const matchingItems = this.currentJsonData.filter(
            item => item && 
                   typeof item === 'object' && 
                   item.type === this.typeFilter && 
                   item.summary && 
                   item.summary.includes(this.contentFilter)
        );
        
        if (matchingItems.length > 0) {
            // Show the matching type first
            this.displayContentByType(this.typeFilter);
            
            // Also set the corresponding button to active
            document.querySelectorAll('.type-button').forEach(btn => {
                if (btn.textContent === this.typeFilter) {
                    btn.classList.add('active');
                }
            });
        } else if (this.currentJsonData && this.currentJsonData.length > 0) {
            // If no match, show the first available type
            const firstItem = this.currentJsonData[0];
            if (firstItem && typeof firstItem === 'object' && firstItem.type) {
                this.displayContentByType(firstItem.type);
                
                // Set the first button to active
                const firstButton = document.querySelector('.type-button');
                if (firstButton) {
                    firstButton.classList.add('active');
                }
            }
        } else {
            this.contentOutput.innerHTML = "<p>No content found in the selected file</p>";
        }
    }
}

// Initialize the viewer when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // The dataDirectory should point to where your JSON files are located
    const viewer = new LearningContentViewer('/LearningPublicData/data');
});