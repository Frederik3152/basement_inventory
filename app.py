from flask import Flask, request, jsonify, render_template, redirect
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

@app.route('/box/<int:box_number>')
def box_filter(box_number):
    """Direct link to inventory filtered by specific box"""
    if box_number not in [1, 2, 3, 4]:
        return redirect('/')
    return render_template('index.html', initial_filter={'type': 'location', 'value': f'Box {box_number}'})

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

# ==================== PROJECT ROUTES ====================

@app.route('/projects')
def projects_page():
    """Projects tracking page"""
    return render_template('projects.html')

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        projects = db.get_projects()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'type', 'start_date', 'expiry_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        project_data = {
            'name': data['name'],
            'type': data['type'],
            'start_date': data['start_date'],
            'expiry_date': data['expiry_date'],
            'status': data.get('status', 'active'),
            'location': data.get('location', ''),
            'notes': data.get('notes', '')
        }
        
        project_id = db.create_project(project_data)
        project = db.get_project_by_id(project_id)
        
        return jsonify(project), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a single project by ID"""
    try:
        project = db.get_project_by_id(project_id)
        if project:
            return jsonify(project)
        else:
            return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project"""
    try:
        data = request.json
        
        # Get current project
        project = db.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        project_data = {
            'name': data.get('name', project['name']),
            'type': data.get('type', project['type']),
            'start_date': data.get('start_date', project['start_date']),
            'expiry_date': data.get('expiry_date', project['expiry_date']),
            'status': data.get('status', project['status']),
            'location': data.get('location', project['location']),
            'notes': data.get('notes', project['notes'])
        }
        
        success = db.update_project(project_id, project_data)
        if success:
            updated_project = db.get_project_by_id(project_id)
            return jsonify(updated_project)
        else:
            return jsonify({'error': 'Failed to update project'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        success = db.delete_project(project_id)
        if success:
            return jsonify({'message': 'Project deleted successfully'})
        else:
            return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/expiring', methods=['GET'])
def get_expiring_projects():
    """Get projects expiring soon"""
    try:
        days = request.args.get('days', 7, type=int)
        expiring_projects = db.get_expiring_projects(days)
        return jsonify(expiring_projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/expired', methods=['GET'])
def get_expired_projects():
    """Get expired projects"""
    try:
        expired_projects = db.get_expired_projects()
        return jsonify(expired_projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
