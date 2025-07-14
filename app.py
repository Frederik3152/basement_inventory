from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import uuid
import json
from database import Database

app = Flask(__name__)
CORS(app)

# Initialize database
try:
    db = Database()
    print("✅ Database connected successfully!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("Please check your DATABASE_URL in the .env file")
    exit(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items"""
    try:
        items = db.get_items()
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'category', 'current_stock', 'min_stock', 'unit']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Process barcodes - ensure it's always a list
        barcodes = data.get('barcodes', [])
        if isinstance(barcodes, str):
            barcodes = [barcodes] if barcodes else []
        elif not isinstance(barcodes, list):
            barcodes = []
        
        # Remove empty barcodes and duplicates
        barcodes = list(set([bc.strip() for bc in barcodes if bc and bc.strip()]))
        
        item_data = {
            'name': data['name'],
            'barcodes': barcodes,
            'category': data['category'],
            'current_stock': int(data['current_stock']),
            'min_stock': int(data['min_stock']),
            'unit': data['unit'],
            'location': data.get('location', '')
        }
        
        item_id = db.create_item(item_data)
        item = db.get_item_by_id(item_id)
        
        return jsonify(item), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing item"""
    try:
        data = request.json
        
        # Get current item
        item = db.get_item_by_id(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Handle barcodes update
        barcodes = data.get('barcodes', item['barcodes'])
        if isinstance(barcodes, str):
            barcodes = [barcodes] if barcodes else []
        elif not isinstance(barcodes, list):
            barcodes = []
        
        # Remove empty barcodes and duplicates
        barcodes = list(set([bc.strip() for bc in barcodes if bc and bc.strip()]))
        
        item_data = {
            'name': data.get('name', item['name']),
            'barcodes': barcodes,
            'category': data.get('category', item['category']),
            'current_stock': int(data.get('current_stock', item['current_stock'])),
            'min_stock': int(data.get('min_stock', item['min_stock'])),
            'unit': data.get('unit', item['unit']),
            'location': data.get('location', item['location'])
        }
        
        success = db.update_item(item_id, item_data)
        if success:
            updated_item = db.get_item_by_id(item_id)
            return jsonify(updated_item)
        else:
            return jsonify({'error': 'Failed to update item'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item"""
    try:
        success = db.delete_item(item_id)
        if success:
            return jsonify({'message': 'Item deleted successfully'})
        else:
            return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/barcode/<barcode>', methods=['GET'])
def get_item_by_barcode(barcode):
    """Get item by barcode"""
    try:
        item = db.get_item_by_barcode(barcode)
        if item:
            return jsonify(item)
        else:
            return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>/barcodes', methods=['POST'])
def add_barcode_to_item(item_id):
    """Add a barcode to an existing item"""
    try:
        data = request.json
        if 'barcode' not in data or not data['barcode'].strip():
            return jsonify({'error': 'Barcode is required'}), 400
        
        barcode = data['barcode'].strip()
        
        # Check if item exists
        item = db.get_item_by_id(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        # Check if barcode already exists
        existing_item = db.get_item_by_barcode(barcode)
        if existing_item:
            if existing_item['id'] == item_id:
                return jsonify({'error': 'Barcode already exists for this item'}), 400
            else:
                return jsonify({'error': f'Barcode already exists for item: {existing_item["name"]}'}), 400
        
        success = db.add_barcode_to_item(item_id, barcode)
        if success:
            updated_item = db.get_item_by_id(item_id)
            return jsonify(updated_item)
        else:
            return jsonify({'error': 'Failed to add barcode'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<item_id>/barcodes/<barcode>', methods=['DELETE'])
def remove_barcode_from_item(item_id, barcode):
    """Remove a barcode from an item"""
    try:
        # Check if item exists
        item = db.get_item_by_id(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        if not item['barcodes'] or barcode not in item['barcodes']:
            return jsonify({'error': 'Barcode not found for this item'}), 404
        
        success = db.remove_barcode_from_item(item_id, barcode)
        if success:
            return jsonify({'message': 'Barcode removed successfully'})
        else:
            return jsonify({'error': 'Failed to remove barcode'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    try:
        categories = db.get_categories()
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    """Record a transaction (restock or usage)"""
    try:
        data = request.json
        
        required_fields = ['item_id', 'type', 'quantity', 'notes']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if item exists
        item = db.get_item_by_id(data['item_id'])
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        if data['type'] not in ['restock', 'usage']:
            return jsonify({'error': 'Invalid transaction type'}), 400
        
        transaction_data = {
            'item_id': data['item_id'],
            'type': data['type'],
            'quantity': int(data['quantity']),
            'notes': data['notes']
        }
        
        transaction_id = db.create_transaction(transaction_data)
        
        # Return the transaction with item name
        transactions = db.get_transactions()
        transaction = next((t for t in transactions if t['id'] == transaction_id), None)
        
        return jsonify(transaction), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions"""
    try:
        transactions = db.get_transactions()
        return jsonify(transactions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/low-stock', methods=['GET'])
def get_low_stock_items():
    """Get items that are running low on stock"""
    try:
        low_stock_items = db.get_low_stock_items()
        return jsonify(low_stock_items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
