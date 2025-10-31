// Global variables
let items = [];
let categories = {};
let transactions = [];
let html5QrcodeScanner = null;
let scannerMode = null; // 'restock', 'usage', or null for find-only

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    setupEventListeners();
    updateStats();
    
    // Load items and then apply initial filter
    loadItems().then(() => {
        // Apply initial filter if specified (from URL-based QR codes)
        if (window.initialFilter) {
            applyInitialFilter();
        }
    });
    
    loadTransactions();
});

// Setup event listeners
function setupEventListeners() {
    // Search functionality
    document.getElementById('searchInput').addEventListener('input', filterItems);
    document.getElementById('categoryFilter').addEventListener('change', filterItems);
    document.getElementById('stockFilter').addEventListener('change', filterItems);
    document.getElementById('locationFilter').addEventListener('change', filterItems);
    
    // Tab change events
    const tabLinks = document.querySelectorAll('#mainTabs a[data-bs-toggle="tab"]');
    tabLinks.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            if (e.target.getAttribute('href') === '#transactions') {
                loadTransactions();
            } else if (e.target.getAttribute('href') === '#lowStock') {
                loadLowStockItems();
            }
        });
    });
}

// API functions
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showToast('An error occurred. Please try again.', 'error');
        throw error;
    }
}

// Load data functions
async function loadCategories() {
    try {
        categories = await apiCall('/api/categories');
        populateCategorySelects();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

async function loadItems() {
    try {
        items = await apiCall('/api/items');
        displayItems(items);
        updateStats();
    } catch (error) {
        console.error('Failed to load items:', error);
    }
}

async function loadTransactions() {
    try {
        transactions = await apiCall('/api/transactions');
        displayTransactions(transactions);
        updateStats();
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

async function loadLowStockItems() {
    try {
        const lowStockItems = await apiCall('/api/low-stock');
        displayLowStockItems(lowStockItems);
    } catch (error) {
        console.error('Failed to load low stock items:', error);
    }
}

// Display functions
function displayItems(itemsToDisplay) {
    const container = document.getElementById('itemsList');
    
    if (itemsToDisplay.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="text-center py-5">
                    <i class="bi bi-box-seam display-1 text-muted"></i>
                    <h4 class="text-muted mt-3">No items found</h4>
                    <p class="text-muted">Add your first item to get started!</p>
                </div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = itemsToDisplay.map(item => `
        <div class="col-md-6 col-lg-4 mb-3 fade-in">
            <div class="card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">${escapeHtml(item.name)}</h6>
                        <span class="stock-indicator ${getStockIndicatorClass(item)}"></span>
                    </div>
                    
                    <span class="badge category-badge mb-2">${escapeHtml(item.category_name)}</span>
                    
                    <div class="mb-2">
                        <small class="text-muted">Stock: </small>
                        <strong class="${getStockTextClass(item)}">${item.current_stock} ${item.unit}</strong>
                        <small class="text-muted">(min: ${item.min_stock})</small>
                    </div>
                    
                    ${item.location ? `<div class="mb-2"><small class="text-muted"><i class="bi bi-geo-alt"></i> ${escapeHtml(item.location)}</small></div>` : ''}
                    
                    ${item.barcodes && item.barcodes.length > 0 ? `
                        <div class="mb-2">
                            <small class="text-muted"><i class="bi bi-upc"></i> 
                                ${item.barcodes.length === 1 ? 
                                    escapeHtml(item.barcodes[0]) : 
                                    `${item.barcodes.length} barcodes`}
                            </small>
                            ${item.barcodes.length > 1 ? `
                                <button class="btn btn-sm btn-outline-info ms-1" onclick="showBarcodesModal('${item.id}', '${escapeHtml(item.name)}', ${JSON.stringify(item.barcodes).replace(/"/g, '&quot;')})">
                                    <i class="bi bi-eye"></i>
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
                    
                    <div class="d-flex gap-2 mt-3">
                        <button class="btn btn-sm btn-outline-success" onclick="showTransactionModal('${item.id}', '${escapeHtml(item.name)}', 'restock')">
                            <i class="bi bi-plus"></i> Restock
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="showTransactionModal('${item.id}', '${escapeHtml(item.name)}', 'usage')">
                            <i class="bi bi-dash"></i> Use
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="editItem('${item.id}')" title="Edit item details">
                            <i class="bi bi-pencil"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function displayTransactions(transactionsToDisplay) {
    const container = document.getElementById('transactionsList');
    
    if (transactionsToDisplay.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-clock-history display-4 text-muted"></i>
                <h5 class="text-muted mt-3">No transactions yet</h5>
                <p class="text-muted">Start tracking your inventory movements!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = transactionsToDisplay.slice(0, 20).map(transaction => `
        <div class="transaction-item transaction-${transaction.type} fade-in">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${escapeHtml(transaction.item_name || 'Unknown Item')}</strong>
                    <span class="badge bg-${transaction.type === 'restock' ? 'success' : 'warning'} ms-2">
                        ${transaction.type === 'restock' ? '+' : '-'}${transaction.quantity}
                    </span>
                </div>
                <small class="text-muted">${formatDateTime(transaction.timestamp)}</small>
            </div>
            ${transaction.notes ? `<div class="mt-1"><small class="text-muted">${escapeHtml(transaction.notes)}</small></div>` : ''}
        </div>
    `).join('');
}

function displayLowStockItems(lowStockItems) {
    const container = document.getElementById('lowStockList');
    
    if (lowStockItems.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="text-center py-4">
                    <i class="bi bi-check-circle display-4 text-success"></i>
                    <h5 class="text-success mt-3">All items are well stocked!</h5>
                    <p class="text-muted">No items are currently running low.</p>
                </div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = lowStockItems.map(item => `
        <div class="col-md-6 col-lg-4 mb-3 fade-in">
            <div class="card border-warning h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">${escapeHtml(item.name)}</h6>
                        <i class="bi bi-exclamation-triangle text-warning"></i>
                    </div>
                    
                    <span class="badge category-badge mb-2">${escapeHtml(item.category_name)}</span>
                    
                    <div class="mb-3">
                        <small class="text-muted">Current Stock: </small>
                        <strong class="text-warning">${item.current_stock} ${item.unit}</strong>
                        <br>
                        <small class="text-muted">Minimum Stock: ${item.min_stock} ${item.unit}</small>
                    </div>
                    
                    <button class="btn btn-warning btn-sm w-100" onclick="showTransactionModal('${item.id}', '${escapeHtml(item.name)}', 'restock')">
                        <i class="bi bi-plus-circle"></i> Restock Now
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Modal functions
function showAddItemModal() {
    const modal = new bootstrap.Modal(document.getElementById('addItemModal'));
    document.getElementById('addItemForm').reset();
    
    // Reset barcodes container to have only one field
    const container = document.getElementById('barcodesContainer');
    container.innerHTML = `
        <div class="input-group mb-2">
            <input type="text" class="form-control" name="barcodes[]" placeholder="Enter barcode">
            <button type="button" class="btn btn-outline-secondary" onclick="addBarcodeField()">
                <i class="bi bi-plus"></i>
            </button>
        </div>
    `;
    
    modal.show();
}

function showTransactionModal(itemId, itemName, type = 'restock') {
    document.getElementById('transactionItemId').value = itemId;
    document.getElementById('transactionItemName').value = itemName;
    document.querySelector('[name="type"]').value = type;
    document.getElementById('transactionForm').reset();
    document.getElementById('transactionItemId').value = itemId;
    document.getElementById('transactionItemName').value = itemName;
    document.querySelector('[name="type"]').value = type;
    
    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
    modal.show();
}

// Save functions
async function saveNewItem() {
    const form = document.getElementById('addItemForm');
    const formData = new FormData(form);
    
    // Collect all barcode inputs
    const barcodeInputs = form.querySelectorAll('input[name="barcodes[]"]');
    const barcodes = Array.from(barcodeInputs)
        .map(input => input.value.trim())
        .filter(barcode => barcode); // Remove empty values
    
    const itemData = {
        name: formData.get('name'),
        barcodes: barcodes,
        category: formData.get('category'),
        current_stock: parseInt(formData.get('current_stock')),
        min_stock: parseInt(formData.get('min_stock')),
        unit: formData.get('unit'),
        location: formData.get('location')
    };
    
    try {
        await apiCall('/api/items', 'POST', itemData);
        showToast('Item added successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('addItemModal')).hide();
        loadItems();
    } catch (error) {
        showToast('Failed to add item. Please try again.', 'error');
    }
}

async function saveTransaction() {
    const form = document.getElementById('transactionForm');
    const formData = new FormData(form);
    
    const transactionData = {
        item_id: formData.get('item_id'),
        type: formData.get('type'),
        quantity: parseInt(formData.get('quantity')),
        notes: formData.get('notes') || ''
    };
    
    try {
        await apiCall('/api/transactions', 'POST', transactionData);
        showToast('Transaction recorded successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('transactionModal')).hide();
        loadItems();
        loadTransactions();
    } catch (error) {
        showToast('Failed to record transaction. Please try again.', 'error');
    }
}

// Barcode scanner functions
function showScanner(mode = null) {
    scannerMode = mode;
    const overlay = document.getElementById('scannerOverlay');
    overlay.style.display = 'flex';
    
    // Update scanner title based on mode
    const scannerTitle = document.querySelector('#scannerOverlay h5');
    if (scannerTitle) {
        switch(mode) {
            case 'restock':
                scannerTitle.innerHTML = '<i class="bi bi-box-arrow-in-down text-success"></i> Scan to Restock';
                break;
            case 'usage':
                scannerTitle.innerHTML = '<i class="bi bi-box-arrow-up text-warning"></i> Scan to Consume';
                break;
            default:
                scannerTitle.innerHTML = '<i class="bi bi-search"></i> Scan to Find Item';
        }
    }
    
    html5QrcodeScanner = new Html5Qrcode("reader");
    
    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        rememberLastUsedCamera: true
    };
    
    html5QrcodeScanner.start(
        { facingMode: "environment" },
        config,
        onScanSuccess,
        onScanFailure
    ).catch(err => {
        console.error('Unable to start scanner:', err);
        showToast('Unable to access camera. Please check permissions.', 'error');
        hideScanner();
    });
}

function hideScanner() {
    if (html5QrcodeScanner) {
        html5QrcodeScanner.stop().then(() => {
            html5QrcodeScanner.clear();
            html5QrcodeScanner = null;
        }).catch(err => {
            console.error('Error stopping scanner:', err);
        });
    }
    
    scannerMode = null; // Reset scanner mode
    document.getElementById('scannerOverlay').style.display = 'none';
}

async function onScanSuccess(decodedText, decodedResult) {
    // Store the scanner mode before hiding the scanner
    const currentScannerMode = scannerMode;
    hideScanner();
    
    try {
        const item = await apiCall(`/api/items/barcode/${encodeURIComponent(decodedText)}`);
        
        // Handle different scanner modes
        if (currentScannerMode === 'restock') {
            showToast(`Found: ${item.name} - Opening restock dialog`, 'success');
            showTransactionModal(item.id, item.name, 'restock');
        } else if (currentScannerMode === 'usage') {
            showToast(`Found: ${item.name} - Opening consume dialog`, 'success');
            showTransactionModal(item.id, item.name, 'usage');
        } else {
            // Default behavior - find and highlight item
            showToast(`Found: ${item.name}`, 'success');
            
            // Switch to inventory tab and highlight the item
            const inventoryTab = new bootstrap.Tab(document.querySelector('a[href="#inventory"]'));
            inventoryTab.show();
            
            // Filter to show only this item temporarily
            const searchInput = document.getElementById('searchInput');
            searchInput.value = item.name;
            filterItems();
        }
        
    } catch (error) {
        // Item not found, ask if user wants to add it
        const modeText = currentScannerMode ? ` in ${currentScannerMode} mode` : '';
        if (confirm(`Barcode ${decodedText} not found${modeText}. Would you like to add a new item with this barcode?`)) {
            showAddItemModal();
            // Add the barcode to the first barcode field
            const firstBarcodeInput = document.querySelector('input[name="barcodes[]"]');
            if (firstBarcodeInput) {
                firstBarcodeInput.value = decodedText;
            }
        }
    }
}

// Apply initial filter from URL parameters
function applyInitialFilter() {
    if (!window.initialFilter) return;
    
    const { type, value } = window.initialFilter;
    
    if (type === 'location') {
        console.log('Applying initial location filter:', value); // Debug log
        
        // Set the location filter
        const locationFilter = document.getElementById('locationFilter');
        if (locationFilter) {
            locationFilter.value = value;
            console.log('Location filter set to:', locationFilter.value); // Debug log
            
            // Apply the filter
            filterItems();
            
            // Show a toast message
            showToast(`Showing items in ${value}`, 'info');
        } else {
            console.error('Location filter element not found'); // Debug log
        }
    }
}

// New function to add barcode input fields
function addBarcodeField() {
    const container = document.getElementById('barcodesContainer');
    const newField = document.createElement('div');
    newField.className = 'input-group mb-2';
    newField.innerHTML = `
        <input type="text" class="form-control" name="barcodes[]" placeholder="Enter barcode">
        <button type="button" class="btn btn-outline-danger" onclick="removeBarcodeField(this)">
            <i class="bi bi-dash"></i>
        </button>
    `;
    container.appendChild(newField);
}

// New function to remove barcode input fields
function removeBarcodeField(button) {
    const container = document.getElementById('barcodesContainer');
    if (container.children.length > 1) {
        button.closest('.input-group').remove();
    }
}

// New function to show barcodes modal
function showBarcodesModal(itemId, itemName, barcodes) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('barcodesModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'barcodesModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Item Barcodes</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h6 id="barcodesItemName" class="mb-0"></h6>
                            <button type="button" class="btn btn-sm btn-outline-primary" onclick="openEditFromBarcodes()">
                                <i class="bi bi-pencil"></i> Edit Item
                            </button>
                        </div>
                        <div id="barcodesList"></div>
                        <hr>
                        <div class="input-group">
                            <input type="text" class="form-control" id="newBarcodeInput" placeholder="Add new barcode">
                            <button type="button" class="btn btn-primary" onclick="addNewBarcode()">
                                <i class="bi bi-plus"></i> Add
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    document.getElementById('barcodesItemName').textContent = itemName;
    document.getElementById('newBarcodeInput').setAttribute('data-item-id', itemId);
    
    const barcodesList = document.getElementById('barcodesList');
    barcodesList.innerHTML = barcodes.map(barcode => `
        <div class="d-flex justify-content-between align-items-center border rounded p-2 mb-2">
            <span><i class="bi bi-upc"></i> ${escapeHtml(barcode)}</span>
            <button class="btn btn-sm btn-outline-danger" onclick="removeBarcode('${itemId}', '${escapeHtml(barcode)}')">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `).join('');
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Open edit modal from barcodes modal
function openEditFromBarcodes() {
    const itemId = document.getElementById('newBarcodeInput').getAttribute('data-item-id');
    bootstrap.Modal.getInstance(document.getElementById('barcodesModal')).hide();
    editItem(itemId);
}

// New function to add a barcode to an existing item
async function addNewBarcode() {
    const input = document.getElementById('newBarcodeInput');
    const itemId = input.getAttribute('data-item-id');
    const barcode = input.value.trim();
    
    if (!barcode) {
        showToast('Please enter a barcode', 'error');
        return;
    }
    
    try {
        await apiCall(`/api/items/${itemId}/barcodes`, 'POST', { barcode });
        showToast('Barcode added successfully!', 'success');
        input.value = '';
        loadItems();
        bootstrap.Modal.getInstance(document.getElementById('barcodesModal')).hide();
    } catch (error) {
        showToast('Failed to add barcode. It may already exist.', 'error');
    }
}

// New function to remove a barcode from an item
async function removeBarcode(itemId, barcode) {
    if (!confirm(`Remove barcode "${barcode}"?`)) {
        return;
    }
    
    try {
        await apiCall(`/api/items/${itemId}/barcodes/${encodeURIComponent(barcode)}`, 'DELETE');
        showToast('Barcode removed successfully!', 'success');
        loadItems();
        bootstrap.Modal.getInstance(document.getElementById('barcodesModal')).hide();
    } catch (error) {
        showToast('Failed to remove barcode.', 'error');
    }
}

function onScanFailure(error) {
    // Handle scan failure, usually better to ignore rather than log
}

// Location filtering functions
function filterItemsByLocation(location) {
    const filteredItems = items.filter(item => {
        if (!location) return true;
        return item.location && item.location.toLowerCase().includes(location.toLowerCase());
    });
    
    displayItems(filteredItems);
    
    // Update the location filter display
    const locationFilter = document.getElementById('locationFilter');
    if (locationFilter && location) {
        locationFilter.value = location;
        showToast(`Showing ${filteredItems.length} items in ${location}`, 'success');
    }
}

// Enhanced filtering function that includes location
function filterItems() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const stockFilter = document.getElementById('stockFilter').value;
    const locationFilter = document.getElementById('locationFilter') ? document.getElementById('locationFilter').value : '';
    
    const filteredItems = items.filter(item => {
        // Search filter
        const matchesSearch = !searchTerm || item.name.toLowerCase().includes(searchTerm);
        
        // Category filter
        const matchesCategory = !categoryFilter || item.category === categoryFilter;
        
        // Stock filter
        let matchesStock = true;
        if (stockFilter === 'good') {
            matchesStock = item.current_stock > item.min_stock;
        } else if (stockFilter === 'low') {
            matchesStock = item.current_stock <= item.min_stock && item.current_stock > 0;
        } else if (stockFilter === 'out') {
            matchesStock = item.current_stock === 0;
        }
        
        // Location filter
        const matchesLocation = !locationFilter || 
            (item.location && item.location.toLowerCase().includes(locationFilter.toLowerCase()));
        
        return matchesSearch && matchesCategory && matchesStock && matchesLocation;
    });
    
    displayItems(filteredItems);
}

// Clear all filters function
function clearAllFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('stockFilter').value = '';
    document.getElementById('locationFilter').value = '';
    filterItems();
    showToast('All filters cleared', 'info');
}

// Utility functions
function populateCategorySelects() {
    const selects = document.querySelectorAll('select[name="category"], #categoryFilter');
    
    selects.forEach(select => {
        if (select.id === 'categoryFilter') {
            select.innerHTML = '<option value="">All Categories</option>';
        } else {
            select.innerHTML = '';
        }
        
        Object.entries(categories).forEach(([key, category]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = category.name;
            select.appendChild(option);
        });
    });
}

function getStockIndicatorClass(item) {
    if (item.current_stock === 0) return 'stock-out';
    if (item.current_stock <= item.min_stock) return 'stock-low';
    return 'stock-good';
}

function getStockTextClass(item) {
    if (item.current_stock === 0) return 'text-danger';
    if (item.current_stock <= item.min_stock) return 'text-warning';
    return 'text-success';
}

function updateStats() {
    document.getElementById('totalItems').textContent = items.length;
    document.getElementById('lowStockItems').textContent = items.filter(item => 
        item.current_stock <= item.min_stock
    ).length;
    document.getElementById('totalCategories').textContent = Object.keys(categories).length;
    document.getElementById('totalTransactions').textContent = transactions.length;
}

function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 10000; max-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// Edit item function
async function editItem(itemId) {
    try {
        // Find the item in our current items array
        const item = items.find(i => i.id === itemId);
        if (!item) {
            showToast('Item not found', 'error');
            return;
        }
        
        // Populate the edit form
        document.getElementById('editItemId').value = item.id;
        document.querySelector('#editItemForm [name="name"]').value = item.name;
        document.querySelector('#editItemForm [name="category"]').value = item.category;
        document.querySelector('#editItemForm [name="current_stock"]').value = item.current_stock;
        document.querySelector('#editItemForm [name="min_stock"]').value = item.min_stock;
        document.querySelector('#editItemForm [name="unit"]').value = item.unit;
        document.querySelector('#editItemForm [name="location"]').value = item.location || '';
        
        // Populate categories in edit form
        const editCategorySelect = document.querySelector('#editItemForm [name="category"]');
        editCategorySelect.innerHTML = '';
        Object.entries(categories).forEach(([key, category]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = category.name;
            option.selected = key === item.category;
            editCategorySelect.appendChild(option);
        });
        
        // Populate barcodes
        const barcodesContainer = document.getElementById('editBarcodesContainer');
        barcodesContainer.innerHTML = '';
        
        if (item.barcodes && item.barcodes.length > 0) {
            item.barcodes.forEach(barcode => {
                addEditBarcodeField(barcode);
            });
        } else {
            addEditBarcodeField(); // Add one empty field
        }
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('editItemModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading item for edit:', error);
        showToast('Failed to load item details', 'error');
    }
}

// Add barcode field for edit form
function addEditBarcodeField(value = '') {
    const container = document.getElementById('editBarcodesContainer');
    const fieldDiv = document.createElement('div');
    fieldDiv.className = 'input-group mb-2';
    fieldDiv.innerHTML = `
        <input type="text" class="form-control" name="edit_barcodes[]" placeholder="Enter barcode" value="${escapeHtml(value)}">
        <button type="button" class="btn btn-outline-danger" onclick="removeEditBarcodeField(this)" ${container.children.length === 0 ? 'disabled' : ''}>
            <i class="bi bi-dash"></i>
        </button>
    `;
    container.appendChild(fieldDiv);
    
    // Enable/disable remove buttons based on field count
    updateEditBarcodeButtons();
}

// Remove barcode field from edit form
function removeEditBarcodeField(button) {
    const container = document.getElementById('editBarcodesContainer');
    if (container.children.length > 1) {
        button.closest('.input-group').remove();
        updateEditBarcodeButtons();
    }
}

// Update edit barcode buttons (ensure at least one field remains)
function updateEditBarcodeButtons() {
    const container = document.getElementById('editBarcodesContainer');
    const removeButtons = container.querySelectorAll('.btn-outline-danger');
    
    removeButtons.forEach((btn, index) => {
        btn.disabled = container.children.length === 1;
    });
}

// Save edited item
async function saveEditedItem() {
    const form = document.getElementById('editItemForm');
    const formData = new FormData(form);
    const itemId = formData.get('item_id');
    
    // Collect all barcode inputs
    const barcodeInputs = form.querySelectorAll('input[name="edit_barcodes[]"]');
    const barcodes = Array.from(barcodeInputs)
        .map(input => input.value.trim())
        .filter(barcode => barcode); // Remove empty values
    
    const itemData = {
        name: formData.get('name'),
        barcodes: barcodes,
        category: formData.get('category'),
        current_stock: parseInt(formData.get('current_stock')),
        min_stock: parseInt(formData.get('min_stock')),
        unit: formData.get('unit'),
        location: formData.get('location')
    };
    
    try {
        await apiCall(`/api/items/${itemId}`, 'PUT', itemData);
        showToast('Item updated successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('editItemModal')).hide();
        loadItems();
    } catch (error) {
        showToast('Failed to update item. Please try again.', 'error');
    }
}

// Confirm delete item
function confirmDeleteItem() {
    const itemName = document.querySelector('#editItemForm [name="name"]').value;
    
    if (confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) {
        deleteItem();
    }
}

// Delete item
async function deleteItem() {
    const itemId = document.getElementById('editItemId').value;
    
    try {
        await apiCall(`/api/items/${itemId}`, 'DELETE');
        showToast('Item deleted successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('editItemModal')).hide();
        loadItems();
    } catch (error) {
        showToast('Failed to delete item. Please try again.', 'error');
    }
}
