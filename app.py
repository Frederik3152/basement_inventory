from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import uuid
import json

app = Flask(__name__)
CORS(app)

# In-memory storage
items = {}
categories = {
    "paper-products": {"name": "Paper Products", "items": []},
    "canned-goods": {"name": "Canned Goods", "items": []},
    "cleaning-supplies": {"name": "Cleaning Supplies", "items": []},
    "personal-care": {"name": "Personal Care", "items": []},
    "beverages": {"name": "Beverages", "items": []},
    "snacks": {"name": "Snacks", "items": []},
    "other": {"name": "Other", "items": []}
}
transactions = []

# Sample data
sample_items = [
    {
        "id": str(uuid.uuid4()),
        "name": "Toilet Paper",
        "barcodes": ["123456789012", "987654321098"],  # Multiple barcodes for same item
        "category": "paper-products",
        "current_stock": 24,
        "min_stock": 6,
        "unit": "rolls",
        "location": "Shelf A",
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Paper Towels",
        "barcodes": ["123456789013"],
        "category": "paper-products",
        "current_stock": 12,
        "min_stock": 3,
        "unit": "rolls",
        "location": "Shelf A",
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Canned Tomatoes",
        "barcodes": ["123456789014", "456789012345"],  # Different brands/sizes
        "category": "canned-goods",
        "current_stock": 8,
        "min_stock": 2,
        "unit": "cans",
        "location": "Shelf B",
        "last_updated": datetime.now().isoformat()
    }
]

# Initialize sample data
for item in sample_items:
    items[item["id"]] = item
    categories[item["category"]]["items"].append(item["id"])

# Backward compatibility: convert old barcode field to barcodes array
def ensure_barcodes_format():
    """Ensure all items have barcodes as array format"""
    for item in items.values():
        if 'barcode' in item and 'barcodes' not in item:
            # Convert old single barcode to array
            item['barcodes'] = [item['barcode']] if item['barcode'] else []
            del item['barcode']
        elif 'barcodes' not in item:
            item['barcodes'] = []

ensure_barcodes_format()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items"""
    items_with_categories = []
    for item in items.values():
        item_copy = item.copy()
        item_copy['category_name'] = categories[item['category']]['name']
        items_with_categories.append(item_copy)
    return jsonify(items_with_categories)

@app.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'category', 'current_stock', 'min_stock', 'unit']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if category exists
    if data['category'] not in categories:
        return jsonify({'error': 'Invalid category'}), 400
    
    # Process barcodes - ensure it's always a list
    barcodes = data.get('barcodes', [])
    if isinstance(barcodes, str):
        barcodes = [barcodes] if barcodes else []
    elif not isinstance(barcodes, list):
        barcodes = []
    
    # Remove empty barcodes and duplicates
    barcodes = list(set([bc.strip() for bc in barcodes if bc and bc.strip()]))
    
    item_id = str(uuid.uuid4())
    item = {
        'id': item_id,
        'name': data['name'],
        'barcodes': barcodes,
        'category': data['category'],
        'current_stock': int(data['current_stock']),
        'min_stock': int(data['min_stock']),
        'unit': data['unit'],
        'location': data.get('location', ''),
        'last_updated': datetime.now().isoformat()
    }
    
    items[item_id] = item
    categories[data['category']]['items'].append(item_id)
    
    return jsonify(item), 201

@app.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing item"""
    if item_id not in items:
        return jsonify({'error': 'Item not found'}), 404
    
    data = request.json
    item = items[item_id]
    
    # Update fields if provided
    updatable_fields = ['name', 'category', 'current_stock', 'min_stock', 'unit', 'location']
    old_category = item['category']
    
    for field in updatable_fields:
        if field in data:
            if field in ['current_stock', 'min_stock']:
                item[field] = int(data[field])
            else:
                item[field] = data[field]
    
    # Handle barcodes update
    if 'barcodes' in data:
        barcodes = data['barcodes']
        if isinstance(barcodes, str):
            barcodes = [barcodes] if barcodes else []
        elif not isinstance(barcodes, list):
            barcodes = []
        
        # Remove empty barcodes and duplicates
        barcodes = list(set([bc.strip() for bc in barcodes if bc and bc.strip()]))
        item['barcodes'] = barcodes
    
    # Update category list if category changed
    if 'category' in data and data['category'] != old_category:
        categories[old_category]['items'].remove(item_id)
        categories[data['category']]['items'].append(item_id)
    
    item['last_updated'] = datetime.now().isoformat()
    
    return jsonify(item)

@app.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item"""
    if item_id not in items:
        return jsonify({'error': 'Item not found'}), 404
    
    item = items[item_id]
    categories[item['category']]['items'].remove(item_id)
    del items[item_id]
    
    return jsonify({'message': 'Item deleted successfully'})

@app.route('/api/items/barcode/<barcode>', methods=['GET'])
def get_item_by_barcode(barcode):
    """Get item by barcode"""
    for item in items.values():
        if barcode in item.get('barcodes', []):
            item_copy = item.copy()
            item_copy['category_name'] = categories[item['category']]['name']
            return jsonify(item_copy)
    
    return jsonify({'error': 'Item not found'}), 404

@app.route('/api/items/<item_id>/barcodes', methods=['POST'])
def add_barcode_to_item(item_id):
    """Add a barcode to an existing item"""
    if item_id not in items:
        return jsonify({'error': 'Item not found'}), 404
    
    data = request.json
    if 'barcode' not in data or not data['barcode'].strip():
        return jsonify({'error': 'Barcode is required'}), 400
    
    barcode = data['barcode'].strip()
    item = items[item_id]
    
    # Check if barcode already exists for any item
    for existing_item in items.values():
        if barcode in existing_item.get('barcodes', []):
            if existing_item['id'] == item_id:
                return jsonify({'error': 'Barcode already exists for this item'}), 400
            else:
                return jsonify({'error': f'Barcode already exists for item: {existing_item["name"]}'}), 400
    
    # Add barcode to item
    if 'barcodes' not in item:
        item['barcodes'] = []
    
    item['barcodes'].append(barcode)
    item['last_updated'] = datetime.now().isoformat()
    
    return jsonify(item)

@app.route('/api/items/<item_id>/barcodes/<barcode>', methods=['DELETE'])
def remove_barcode_from_item(item_id, barcode):
    """Remove a barcode from an item"""
    if item_id not in items:
        return jsonify({'error': 'Item not found'}), 404
    
    item = items[item_id]
    
    if 'barcodes' not in item or barcode not in item['barcodes']:
        return jsonify({'error': 'Barcode not found for this item'}), 404
    
    item['barcodes'].remove(barcode)
    item['last_updated'] = datetime.now().isoformat()
    
    return jsonify({'message': 'Barcode removed successfully'})

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    return jsonify(categories)

@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    """Record a transaction (restock or usage)"""
    data = request.json
    
    required_fields = ['item_id', 'type', 'quantity', 'notes']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['item_id'] not in items:
        return jsonify({'error': 'Item not found'}), 404
    
    if data['type'] not in ['restock', 'usage']:
        return jsonify({'error': 'Invalid transaction type'}), 400
    
    transaction = {
        'id': str(uuid.uuid4()),
        'item_id': data['item_id'],
        'type': data['type'],
        'quantity': int(data['quantity']),
        'notes': data['notes'],
        'timestamp': datetime.now().isoformat()
    }
    
    # Update item stock
    item = items[data['item_id']]
    if data['type'] == 'restock':
        item['current_stock'] += int(data['quantity'])
    else:  # usage
        item['current_stock'] = max(0, item['current_stock'] - int(data['quantity']))
    
    item['last_updated'] = datetime.now().isoformat()
    transactions.append(transaction)
    
    return jsonify(transaction), 201

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions"""
    # Add item names to transactions
    enriched_transactions = []
    for transaction in transactions:
        transaction_copy = transaction.copy()
        if transaction['item_id'] in items:
            transaction_copy['item_name'] = items[transaction['item_id']]['name']
        enriched_transactions.append(transaction_copy)
    
    # Sort by timestamp (newest first)
    enriched_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(enriched_transactions)

@app.route('/api/low-stock', methods=['GET'])
def get_low_stock_items():
    """Get items that are running low on stock"""
    low_stock_items = []
    for item in items.values():
        if item['current_stock'] <= item['min_stock']:
            item_copy = item.copy()
            item_copy['category_name'] = categories[item['category']]['name']
            low_stock_items.append(item_copy)
    
    return jsonify(low_stock_items)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
