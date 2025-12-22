// Projects Management JavaScript

let projects = [];
let currentProjectId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
    setupEventListeners();
    setDefaultDates();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('input', filterProjects);
    document.getElementById('statusFilter').addEventListener('change', filterProjects);
    document.getElementById('typeFilter').addEventListener('change', filterProjects);
}

// Set default dates for new project form
function setDefaultDates() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('projectStartDate').value = today;
    
    // Default ready date to 7 days from now
    const ready = new Date();
    ready.setDate(ready.getDate() + 7);
    document.getElementById('projectReadyDate').value = ready.toISOString().split('T')[0];
    
    // Default expiry to 30 days from now
    const expiry = new Date();
    expiry.setDate(expiry.getDate() + 30);
    document.getElementById('projectExpiryDate').value = expiry.toISOString().split('T')[0];
    
    // Uncheck no expiry checkbox
    document.getElementById('projectNoExpiry').checked = false;
    document.getElementById('projectExpiryDate').disabled = false;
}

// Load all projects
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        if (!response.ok) throw new Error('Failed to load projects');
        
        projects = await response.json();
        updateStats();
        renderProjects(projects);
    } catch (error) {
        console.error('Error loading projects:', error);
        showToast('Error loading projects', 'danger');
    }
}

// Update dashboard stats
function updateStats() {
    const total = projects.length;
    const active = projects.filter(p => p.status === 'active').length;
    
    // Calculate ready projects (ready_date has passed, still active, not expired)
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const ready = projects.filter(p => {
        if (p.status !== 'active' || !p.ready_date) return false;
        const readyDate = new Date(p.ready_date);
        readyDate.setHours(0, 0, 0, 0);
        
        // Ready if ready_date has passed
        if (readyDate > today) return false;
        
        // Not ready if already expired
        if (p.expiry_date) {
            const expiryDate = new Date(p.expiry_date);
            expiryDate.setHours(0, 0, 0, 0);
            if (expiryDate < today) return false;
        }
        
        return true;
    }).length;
    
    // Calculate expiring soon (within 7 days)
    const sevenDaysFromNow = new Date();
    sevenDaysFromNow.setDate(today.getDate() + 7);
    
    const expiring = projects.filter(p => {
        if (p.status !== 'active' || !p.expiry_date) return false;
        const expiryDate = new Date(p.expiry_date);
        return expiryDate > today && expiryDate <= sevenDaysFromNow;
    }).length;
    
    // Calculate expired
    const expired = projects.filter(p => {
        if (p.status !== 'active' || !p.expiry_date) return false;
        const expiryDate = new Date(p.expiry_date);
        return expiryDate < today;
    }).length;
    
    document.getElementById('totalProjects').textContent = total;
    document.getElementById('activeProjects').textContent = active;
    document.getElementById('readyProjects').textContent = ready;
    document.getElementById('expiringProjects').textContent = expiring;
    document.getElementById('expiredProjects').textContent = expired;
}

// Render projects list
function renderProjects(projectsToRender) {
    const container = document.getElementById('projectsList');
    const emptyState = document.getElementById('emptyState');
    
    if (projectsToRender.length === 0) {
        container.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    container.innerHTML = projectsToRender.map(project => {
        const daysRemaining = calculateDaysRemaining(project.expiry_date);
        const cardClass = getProjectCardClass(project, daysRemaining);
        const statusBadge = getStatusBadge(project.status);
        const isReady = isProjectReady(project);
        const readyBadge = isReady ? '<span class="status-badge status-ready ms-1"><i class="bi bi-check-circle"></i> Ready</span>' : '';
        
        return `
            <div class="col-md-6 col-lg-4 mb-3 fade-in">
                <div class="card project-card ${cardClass}" onclick="showProjectDetails('${project.id}')">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">${escapeHtml(project.name)}</h6>
                            <div class="d-flex flex-wrap gap-1">
                                ${statusBadge}
                                ${readyBadge}
                            </div>
                        </div>
                        <p class="text-muted mb-2">
                            <span class="type-badge">${escapeHtml(project.type)}</span>
                        </p>
                        ${project.location ? `
                            <p class="mb-2">
                                <i class="bi bi-geo-alt"></i> 
                                <small>${escapeHtml(project.location)}</small>
                            </p>
                        ` : ''}
                        <div class="mb-2">
                            <small class="text-muted">Started: ${formatDate(project.start_date)}</small><br>
                            ${project.ready_date ? `<small class="text-muted">Ready: ${formatDate(project.ready_date)}</small><br>` : ''}
                            <small class="text-muted">Expires: ${project.expiry_date ? formatDate(project.expiry_date) : 'No expiry'}</small>
                        </div>
                        <div class="days-remaining ${getDaysRemainingClass(project, daysRemaining)}">
                            ${getDaysRemainingText(project, daysRemaining)}
                        </div>
                        ${project.notes ? `
                            <p class="card-text mt-2">
                                <small class="text-muted">${escapeHtml(project.notes.substring(0, 100))}${project.notes.length > 100 ? '...' : ''}</small>
                            </p>
                        ` : ''}
                    </div>
                    <div class="card-footer bg-transparent border-0">
                        <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); editProject('${project.id}')">
                            <i class="bi bi-pencil"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation(); deleteProject('${project.id}')">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Calculate days remaining
function calculateDaysRemaining(expiryDate) {
    if (!expiryDate) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const expiry = new Date(expiryDate);
    expiry.setHours(0, 0, 0, 0);
    return daysBetween(today, expiry);
}

// Check if project is ready
function isProjectReady(project) {
    if (project.status !== 'active' || !project.ready_date) return false;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const readyDate = new Date(project.ready_date);
    readyDate.setHours(0, 0, 0, 0);
    
    // Ready if ready_date has passed
    if (readyDate > today) return false;
    
    // Not ready if already expired
    if (project.expiry_date) {
        const expiryDate = new Date(project.expiry_date);
        expiryDate.setHours(0, 0, 0, 0);
        if (expiryDate < today) return false;
    }
    
    return true;
}

// Get project card class based on status and days remaining
function getProjectCardClass(project, daysRemaining) {
    if (project.status !== 'active') {
        return project.status;
    }
    if (daysRemaining === null) {
        return 'active';
    }
    if (daysRemaining < 0) {
        return 'expired';
    }
    if (daysRemaining <= 7) {
        return 'expiring-soon';
    }
    return 'active';
}

// Get days remaining class for styling
function getDaysRemainingClass(project, daysRemaining) {
    if (project.status !== 'active') {
        return '';
    }
    if (daysRemaining === null) {
        return 'safe';
    }
    if (daysRemaining < 0) {
        return 'expired';
    }
    if (daysRemaining <= 7) {
        return 'expiring';
    }
    return 'safe';
}

// Get days remaining text
function getDaysRemainingText(project, daysRemaining) {
    if (project.status !== 'active') {
        return '';
    }
    if (daysRemaining === null) {
        return 'No expiry date';
    }
    if (daysRemaining < 0) {
        return `Expired ${Math.abs(daysRemaining)} day${Math.abs(daysRemaining) !== 1 ? 's' : ''} ago`;
    }
    if (daysRemaining === 0) {
        return 'Expires today!';
    }
    if (daysRemaining === 1) {
        return 'Expires tomorrow!';
    }
    return `${daysRemaining} days remaining`;
}

// Get status badge HTML
function getStatusBadge(status) {
    const badges = {
        'active': '<span class="status-badge status-active">Active</span>',
        'completed': '<span class="status-badge status-completed">Completed</span>',
        'expired': '<span class="status-badge status-expired">Expired</span>',
        'discarded': '<span class="status-badge status-discarded">Discarded</span>'
    };
    return badges[status] || '';
}

// Filter projects based on search and filters
function filterProjects() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const typeFilter = document.getElementById('typeFilter').value;
    
    const filtered = projects.filter(project => {
        const matchesSearch = project.name.toLowerCase().includes(searchTerm) ||
                            (project.notes && project.notes.toLowerCase().includes(searchTerm)) ||
                            (project.location && project.location.toLowerCase().includes(searchTerm));
        const matchesStatus = !statusFilter || project.status === statusFilter;
        const matchesType = !typeFilter || project.type === typeFilter;
        
        return matchesSearch && matchesStatus && matchesType;
    });
    
    renderProjects(filtered);
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('typeFilter').value = '';
    renderProjects(projects);
}

// Show add project modal
function showAddProjectModal() {
    currentProjectId = null;
    document.getElementById('projectModalTitle').textContent = 'Add Project';
    document.getElementById('projectForm').reset();
    setDefaultDates();
    document.getElementById('projectStatus').value = 'active';
    showModal('projectModal');
}

// Show edit project modal
function editProject(projectId) {
    const project = projects.find(p => p.id === projectId);
    if (!project) return;
    
    currentProjectId = projectId;
    document.getElementById('projectModalTitle').textContent = 'Edit Project';
    document.getElementById('projectName').value = project.name;
    document.getElementById('projectType').value = project.type;
    document.getElementById('projectStatus').value = project.status;
    document.getElementById('projectStartDate').value = project.start_date;
    document.getElementById('projectReadyDate').value = project.ready_date || '';
    document.getElementById('projectExpiryDate').value = project.expiry_date || '';
    
    // Handle no expiry checkbox
    const hasExpiry = project.expiry_date !== null && project.expiry_date !== '';
    document.getElementById('projectNoExpiry').checked = !hasExpiry;
    document.getElementById('projectExpiryDate').disabled = !hasExpiry;
    
    document.getElementById('projectLocation').value = project.location || '';
    document.getElementById('projectNotes').value = project.notes || '';
    
    showModal('projectModal');
}

// Save project (create or update)
async function saveProject() {
    const name = document.getElementById('projectName').value.trim();
    const type = document.getElementById('projectType').value;
    const status = document.getElementById('projectStatus').value;
    const startDate = document.getElementById('projectStartDate').value;
    const readyDate = document.getElementById('projectReadyDate').value;
    const noExpiry = document.getElementById('projectNoExpiry').checked;
    const expiryDate = noExpiry ? null : document.getElementById('projectExpiryDate').value;
    const location = document.getElementById('projectLocation').value.trim();
    const notes = document.getElementById('projectNotes').value.trim();
    
    if (!name || !type || !status || !startDate) {
        showToast('Please fill in all required fields', 'warning');
        return;
    }
    
    // Validate dates
    if (readyDate && new Date(readyDate) < new Date(startDate)) {
        showToast('Ready date must be after start date', 'warning');
        return;
    }
    
    if (expiryDate) {
        if (new Date(expiryDate) < new Date(startDate)) {
            showToast('Expiry date must be after start date', 'warning');
            return;
        }
        if (readyDate && new Date(expiryDate) < new Date(readyDate)) {
            showToast('Expiry date must be after ready date', 'warning');
            return;
        }
    }
    
    const projectData = {
        name,
        type,
        status,
        start_date: startDate,
        ready_date: readyDate || null,
        expiry_date: expiryDate,
        location,
        notes
    };
    
    try {
        let response;
        if (currentProjectId) {
            // Update existing project
            response = await fetch(`/api/projects/${currentProjectId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
        } else {
            // Create new project
            response = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
        }
        
        if (!response.ok) throw new Error('Failed to save project');
        
        hideModal('projectModal');
        
        showToast(currentProjectId ? 'Project updated successfully' : 'Project added successfully', 'success');
        loadProjects();
    } catch (error) {
        console.error('Error saving project:', error);
        showToast('Error saving project', 'danger');
    }
}

// Delete project
async function deleteProject(projectId) {
    if (!confirm('Are you sure you want to delete this project?')) return;
    
    try {
        const response = await fetch(`/api/projects/${projectId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete project');
        
        showToast('Project deleted successfully', 'success');
        loadProjects();
    } catch (error) {
        console.error('Error deleting project:', error);
        showToast('Error deleting project', 'danger');
    }
}

// Show project details modal
function showProjectDetails(projectId) {
    const project = projects.find(p => p.id === projectId);
    if (!project) return;
    
    currentProjectId = projectId;
    
    document.getElementById('detailsProjectName').textContent = project.name;
    document.getElementById('detailsProjectType').textContent = project.type;
    document.getElementById('detailsProjectStatus').innerHTML = getStatusBadge(project.status);
    document.getElementById('detailsStartDate').textContent = formatDate(project.start_date);
    document.getElementById('detailsReadyDate').textContent = project.ready_date ? formatDate(project.ready_date) : 'Not set';
    document.getElementById('detailsExpiryDate').textContent = project.expiry_date ? formatDate(project.expiry_date) : 'No expiry';
    document.getElementById('detailsLocation').textContent = project.location || 'Not specified';
    document.getElementById('detailsNotes').textContent = project.notes || 'No notes';
    
    const daysRemaining = calculateDaysRemaining(project.expiry_date);
    const daysRemainingElement = document.getElementById('detailsDaysRemaining');
    daysRemainingElement.textContent = getDaysRemainingText(project, daysRemaining);
    daysRemainingElement.className = `ms-2 days-remaining ${getDaysRemainingClass(project, daysRemaining)}`;
    
    showModal('projectDetailsModal');
}

// Edit project from details modal
function editProjectFromDetails() {
    hideModal('projectDetailsModal');
    editProject(currentProjectId);
}

// Delete project from details modal
async function deleteProjectFromDetails() {
    hideModal('projectDetailsModal');
    await deleteProject(currentProjectId);
}

// Toggle expiry date field
function toggleExpiryDate() {
    const checkbox = document.getElementById('projectNoExpiry');
    const expiryField = document.getElementById('projectExpiryDate');
    
    if (checkbox.checked) {
        expiryField.value = '';
        expiryField.disabled = true;
    } else {
        expiryField.disabled = false;
        // Set default to 30 days from now if empty
        if (!expiryField.value) {
            const expiry = new Date();
            expiry.setDate(expiry.getDate() + 30);
            expiryField.value = expiry.toISOString().split('T')[0];
        }
    }
}
