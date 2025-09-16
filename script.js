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
        this.statusMessage = document.getElementById('status-message');
        this.loadingIndicator = document.getElementById('loading-indicator');
        
        // List of JSON files to load - replace these with your actual file names
        this.availableFiles = [
            "Unity-MLAgents-LoadFromHub-Assets_learnings.json",  // Replace with your actual filename
            // Add more files as needed
        ];
        
        this.init();
    }
    
    async init() {
        try {
            // First try to load actual files
            await this.tryLoadingFiles();
        } catch (error) {
            console.error("Error during initialization:", error);
            this.showStatusMessage("Could not load data files. Using sample data instead.", "error");
            this.useSampleData();
        }
    }
    
    showStatusMessage(message, type = "info") {
        this.statusMessage.className = `status-message ${type}`;
        this.statusMessage.textContent = message;
        this.statusMessage.style.display = "block";
    }
    
    hideStatusMessage() {
        this.statusMessage.style.display = "none";
    }
    
    showLoading() {
        this.loadingIndicator.style.display = "block";
    }
    
    hideLoading() {
        this.loadingIndicator.style.display = "none";
    }
    
    async tryLoadingFiles() {
        this.showLoading();
        this.showStatusMessage("Attempting to load JSON files...");
        
        try {
            // Try loading each file in the list
            const loadedFiles = [];
            const filteredFiles = [];
            
            for (const fileName of this.availableFiles) {
                try {
                    console.log(`Trying to load: ${this.dataDirectory}/${fileName}`);
                    const data = await this.loadJsonFile(fileName);
                    loadedFiles.push(fileName);
                    
                    if (this.fileContainsFilteredContent(data)) {
                        filteredFiles.push(fileName);
                    }
                } catch (fileError) {
                    console.warn(`Failed to load ${fileName}:`, fileError);
                    // Continue with other files
                }
            }
            
            this.jsonFiles = loadedFiles;
            
            if (loadedFiles.length === 0) {
                throw new Error("No files could be loaded");
            }
            
            // Update filter info
            this.updateFilterInfo(filteredFiles.length);
            
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
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load the first file if available
            if (displayFiles.length > 0) {
                this.fileSelect.value = displayFiles[0];
                await this.handleFileSelection(displayFiles[0]);
                this.showStatusMessage(`Loaded ${loadedFiles.length} files successfully`);
                setTimeout(() => this.hideStatusMessage(), 3000);
            }
            
            this.hideLoading();
        } catch (error) {
            this.hideLoading();
            console.error("Failed to load files:", error);
            throw error; // Rethrow for the caller to handle
        }
    }
    
    useSampleData() {
        this.jsonFiles = Object.keys(SAMPLE_DATA);
        
        // Update filter info
        this.updateFilterInfo(this.jsonFiles.length);
        
        // Populate the file dropdown
        this.fileSelect.innerHTML = '';
        this.jsonFiles.forEach(file => {
            const option = document.createElement('option');
            option.value = file;
            option.textContent = file;
            this.fileSelect.appendChild(option);
        });
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load the first file
        if (this.jsonFiles.length > 0) {
            const firstFile = this.jsonFiles[0];
            this.fileSelect.value = firstFile;
            this.currentJsonData = SAMPLE_DATA[firstFile];
            this.updateTypeButtons();
            this.displaySelectedContent();
        }
    }
    
    fileContainsFilteredContent(data) {
        if (!Array.isArray(data)) return false;
        
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
            // Try fetch with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${this.dataDirectory}/${fileName}`, { 
                signal: controller.signal,
                headers: { 'Accept': 'application/json' }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            
            // Check Content-Type to avoid trying to parse HTML as JSON
            const contentType = response.headers.get('content-type');
            if (contentType && !contentType.includes('application/json')) {
                console.warn(`File ${fileName} has wrong content type: ${contentType}`);
                throw new Error('Not a JSON file');
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error loading ${fileName}:`, error);
            throw error;
        }
    }
    
    setupEventListeners() {
        this.fileSelect.addEventListener('change', async (event) => {
            this.showLoading();
            try {
                await this.handleFileSelection(event.target.value);
            } catch (error) {
                this.showStatusMessage(`Failed to load file: ${error.message}`, "error");
            } finally {
                this.hideLoading();
            }
        });
    }
    
    async handleFileSelection(fileName) {
        try {
            // Check if this is sample data
            if (SAMPLE_DATA[fileName]) {
                this.currentJsonData = SAMPLE_DATA[fileName];
            } else {
                // Try to load from server
                this.currentJsonData = await this.loadJsonFile(fileName);
            }
            
            this.updateTypeButtons();
            this.displaySelectedContent();
        } catch (error) {
            console.error(`Failed to handle selection of ${fileName}:`, error);
            this.showStatusMessage(`Error: ${error.message}`, "error");
        }
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
        
        if (types.length === 0) {
            this.typeButtonsContainer.innerHTML = '<p>No content types found</p>';
            return;
        }
        
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
        let contentHtml = `<h2>${repoName} - ${typeName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h2>`;
        
        // Add note about filter if applicable
        if (typeName === this.typeFilter && hasMatchingContent) {
            contentHtml += `<p><em>This section contains '${this.contentFilter}'</em></p>`;
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
    // Replace with the actual path to your JSON files
    const viewer = new LearningContentViewer('./data');
});