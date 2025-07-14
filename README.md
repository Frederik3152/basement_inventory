# Basement Inventory Manager

A modern, intuitive inventory management application designed to help you track items in your basement storage. Features include barcode scanning via phone camera, category management, stock tracking, and transaction history.

## Features

- **📱 Barcode Scanning**: Use your phone camera to quickly identify and manage items
- **🏷️ Multiple Barcodes**: Support multiple barcodes per item (different brands, sizes, etc.)
- **📊 Real-time Dashboard**: View key metrics and stock levels at a glance
- **🏷️ Category Management**: Organize items into logical categories
- **📈 Stock Tracking**: Monitor current stock levels and get low-stock alerts
- **📝 Transaction History**: Track all replenishments and usage
- **🎨 Modern UI**: Clean, responsive design that works on all devices
- **⚡ Fast & Lightweight**: In-memory storage for quick responses

## Technology Stack

- **Backend**: Python Flask with REST API
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap 5)
- **Barcode Scanning**: HTML5-QRCode library
- **Storage**: In-memory (database integration planned)

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Open in Browser**
   - Navigate to `http://localhost:5000`
   - Start adding your basement items!

## Usage

### Adding Items
1. Click "Add Item" button
2. Fill in item details (name, category, stock levels, etc.)
3. Add one or more barcodes for the item:
   - Click the "+" button to add additional barcode fields
   - Use multiple barcodes for items that come in different brands/sizes
   - Remove barcode fields with the "-" button

### Editing Items
1. Click the edit button (pencil icon) on any item card
2. Modify any item details including:
   - Name, category, stock levels, unit, location
   - Add or remove barcodes
   - Update stock quantities
3. Use the "Delete Item" button to permanently remove items
4. All changes are saved immediately

### Barcode Scanning
1. Click "Scan Barcode" button
2. Allow camera access when prompted
3. Point camera at barcode
4. If item exists, it will be highlighted
5. If new barcode, option to create new item

### Managing Multiple Barcodes
- **View Barcodes**: Items with multiple barcodes show a count and "eye" icon
- **Add Barcodes**: Click the eye icon to view/manage all barcodes for an item
- **Remove Barcodes**: Use the trash icon next to individual barcodes
- **Scan Any Barcode**: Any barcode associated with an item will find it
- **Edit from Barcodes**: Click "Edit Item" button in the barcodes modal for full editing

### Managing Stock
- **Restock**: Record when you add items to storage
- **Usage**: Record when you use/consume items
- **Low Stock Alerts**: Automatic notifications when items run low

### Categories
Pre-configured categories include:
- Paper Products
- Canned Goods
- Cleaning Supplies
- Personal Care
- Beverages
- Snacks
- Other

## API Endpoints

### Items
- `GET /api/items` - Get all items
- `POST /api/items` - Create new item (with barcodes array)
- `PUT /api/items/<id>` - Update item (with barcodes array)
- `DELETE /api/items/<id>` - Delete item
- `GET /api/items/barcode/<barcode>` - Find item by any of its barcodes
- `POST /api/items/<id>/barcodes` - Add a barcode to an existing item
- `DELETE /api/items/<id>/barcodes/<barcode>` - Remove a barcode from an item

### Categories
- `GET /api/categories` - Get all categories

### Transactions
- `GET /api/transactions` - Get transaction history
- `POST /api/transactions` - Record new transaction

### Utilities
- `GET /api/low-stock` - Get items running low on stock

## Development

The application uses a modular structure:

```
├── app.py              # Flask backend with API routes
├── templates/
│   └── index.html      # Main HTML template
├── static/
│   └── js/
│       └── app.js      # Frontend JavaScript
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Key Components

1. **Backend (app.py)**
   - Flask REST API
   - In-memory data storage
   - CORS enabled for development

2. **Frontend (index.html + app.js)**
   - Responsive Bootstrap UI
   - Real-time updates
   - Barcode scanning integration

## Sample Data

The application comes with sample items to get you started:
- Toilet Paper (24 rolls) - with 2 barcodes for different brands
- Paper Towels (12 rolls) - with 1 barcode
- Canned Tomatoes (8 cans) - with 2 barcodes for different brands/sizes

## Future Enhancements

- Database integration (SQLite/PostgreSQL)
- User authentication
- Export/import functionality
- Mobile app
- Advanced reporting
- Inventory value tracking
- Expiration date monitoring

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - feel free to use and modify for your own needs.
