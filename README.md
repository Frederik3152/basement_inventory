# Basement Inventory Manager

A Flask-based web application for managing home and basement inventory with barcode scanning capabilities and PostgreSQL database storage.

## Features

- **Barcode Scanning**: Use device camera to scan and identify items
- **Multi-Barcode Support**: Store multiple barcodes per item  
- **Stock Management**: Track current stock levels with low-stock alerts
- **Transaction History**: Complete audit trail of restocks and usage
- **Category Organization**: Organize items with predefined categories
- **Location Tracking**: Track where items are stored (Box 1, Box 2, etc.)
- **REST API**: Full API access for programmatic integration
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Quick Start

### Prerequisites

- Python 3.7+
- PostgreSQL database
- Modern web browser with camera support

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Frederik3152/basement_inventory.git
   cd basement_inventory
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://username:password@host:port/database
   DATABASE_SCHEMA=pi_data
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser to `http://localhost:5000`

## Project Structure

```
basement_inventory/
├── app.py              # Main Flask application
├── database.py         # Database operations and models
├── requirements.txt    # Python dependencies
├── .env               # Environment configuration (create this)
├── templates/         # HTML templates
└── static/           # CSS, JavaScript, and other static files
```

## Database Schema

The application uses PostgreSQL with the following tables:

### Categories
```sql
CREATE TABLE pi_data.categories (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
```

### Items
```sql
CREATE TABLE pi_data.items (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    barcodes TEXT[],  -- Array of barcodes
    category_id VARCHAR(50) REFERENCES categories(id),
    current_stock INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    unit VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Transactions
```sql
CREATE TABLE pi_data.transactions (
    id VARCHAR(36) PRIMARY KEY,
    item_id VARCHAR(36) REFERENCES items(id) ON DELETE CASCADE,
    type VARCHAR(20) CHECK (type IN ('restock', 'usage')),
    quantity INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Items
- `GET /api/items` - Get all items
- `POST /api/items` - Create new item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item
- `GET /api/items/barcode/{barcode}` - Find item by barcode

### Barcodes
- `POST /api/items/{id}/barcodes` - Add barcode to item
- `DELETE /api/items/{id}/barcodes/{barcode}` - Remove barcode from item

### Categories & Transactions
- `GET /api/categories` - Get all categories
- `GET /api/transactions` - Get transaction history
- `POST /api/transactions` - Record transaction (restock/usage)
- `GET /api/low-stock` - Get items running low on stock

### Box Filters
- `GET /box/1` - View items in Box 1
- `GET /box/2` - View items in Box 2
- `GET /box/3` - View items in Box 3
- `GET /box/4` - View items in Box 4

## Usage Examples

### Adding a New Item
```javascript
POST /api/items
{
  "name": "Paper Towels",
  "category": "paper-products",
  "current_stock": 6,
  "min_stock": 2,
  "unit": "rolls",
  "location": "Box 1",
  "barcodes": ["123456789012"]
}
```

### Recording a Transaction
```javascript
POST /api/transactions
{
  "item_id": "item-uuid",
  "type": "usage",
  "quantity": 1,
  "notes": "Used one roll"
}
```

## Configuration

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with psycopg2
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Bootstrap 5
- **Barcode Scanning**: HTML5-QRCode library
- **Icons**: Bootstrap Icons

## Barcode Scanning

The application supports scanning various barcode formats:
- QR Codes
- UPC-A/UPC-E
- EAN-8/EAN-13
- Code 128
- Code 39
- And more...

**Usage**: Click the "Scan Barcode" button, allow camera access, and point your camera at the barcode. The item will be automatically identified or you can create a new item.

## Stock Management

- **Current Stock**: Track how many units you currently have
- **Minimum Stock**: Set alerts when stock runs low
- **Units**: Define units (pieces, rolls, bottles, etc.)
- **Location**: Track physical storage location
- **Low Stock Alerts**: Automatic notifications when items need restocking

## Transaction Types

- **Restock**: Add inventory (increases current stock)
- **Usage**: Remove inventory (decreases current stock)
- **Notes**: Add context to each transaction
- **History**: View complete transaction log

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### Database Initialization

The database tables and schema are automatically created when the application starts. The `Database` class in `database.py` handles:

- Schema creation
- Table initialization  
- Default category insertion
- Connection management

## Dependencies

The application requires the following Python packages:

```
Flask==2.3.3
Flask-CORS==4.0.0
python-dotenv==1.0.0
psycopg2-binary==2.9.7
```

## License

MIT License - Feel free to use and modify for personal or commercial projects.

---
