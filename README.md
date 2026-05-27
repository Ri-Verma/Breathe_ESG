# Breadth ESG - Environmental, Social & Governance Dashboard

A comprehensive Django REST API and React dashboard for managing and analyzing ESG (Environmental, Social & Governance) metrics.

## Project Overview

The Breadth ESG platform allows organizations to:
- Upload and manage ESG data from various sources (CSV, Excel, JSON)
- Categorize metrics into Environmental, Social, and Governance categories
- Visualize ESG metrics through an interactive dashboard
- Track ESG performance over time

## Project Structure

```
breadth-esg/
├── backend/                    # Django REST API
│   ├── core/                   # Settings and routing
│   │   ├── settings.py         # Django settings
│   │   ├── urls.py             # URL configuration
│   │   └── wsgi.py             # WSGI application
│   ├── ingestion/              # Data ingestion app
│   │   ├── models.py           # Database models
│   │   ├── views.py            # API views
│   │   ├── serializers.py      # DRF serializers
│   │   ├── urls.py             # API URLs
│   │   └── parsers.py          # Data parsing logic
│   ├── manage.py               # Django management
│   └── requirements.txt         # Python dependencies
│
├── frontend/                   # React Vite Application
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── FileUpload.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── MetricsDisplay.jsx
│   │   ├── App.jsx             # Main App component
│   │   ├── main.jsx            # Entry point
│   │   └── index.css           # Global styles
│   ├── index.html              # HTML template
│   ├── package.json            # Node dependencies
│   └── vite.config.js          # Vite configuration
│
├── docs/                       # Documentation
│   ├── MODEL.md                # Data model documentation
│   ├── DECISIONS.md            # Architecture decisions
│   ├── TRADEOFFS.md            # Design tradeoffs
│   └── SOURCES.md              # Data sources
│
├── data_samples/               # Sample data files
│   ├── sap_export.csv          # ERP export sample
│   ├── utility_bill.csv        # Utility consumption data
│   └── travel_api_response.json # Travel emissions API
│
├── Dockerfile                  # Container configuration
└── README.md                   # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)
- PostgreSQL (optional, defaults to SQLite)

### Backend Setup

1. **Create a virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Start development server:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

### API Endpoints

- `GET /api/files/` - List uploaded files
- `POST /api/files/upload/` - Upload new file
- `GET /api/metrics/` - List all metrics
- `GET /api/metrics/?category=environmental` - Filter metrics by category

## Docker Deployment

Build and run the Docker container:

```bash
docker build -t breadth-esg .
docker run -p 8000:8000 breadth-esg
```

## Features

### Backend (Django REST API)

- **File Upload & Processing**: Support for CSV, Excel, and JSON formats
- **Data Models**: Structured models for files and metrics
- **REST API**: Full REST API with filtering and search
- **CORS Support**: Enable cross-origin requests from frontend
- **Data Validation**: Built-in data parsing and validation

### Frontend (React + Vite)

- **File Upload Component**: Drag-and-drop file upload interface
- **Interactive Dashboard**: Summary statistics and metrics overview
- **Metrics Display**: Categorized view of ESG metrics
- **Responsive Design**: Mobile-friendly interface
- **Real-time Updates**: Automatic data refresh after uploads

## Data Models

### DataFile Model
- `name`: File name
- `file_type`: Type of file (csv, xlsx, json)
- `uploaded_at`: Upload timestamp
- `file_path`: Storage location

### ESGMetric Model
- `category`: Category (environmental, social, governance)
- `metric_name`: Name of the metric
- `value`: Metric value
- `unit`: Measurement unit
- `date`: Date of the metric
- `source_file`: Reference to uploaded file

## Development

### Running Tests

```bash
# Backend tests
python manage.py test

# Frontend tests
npm test
```

### Building for Production

**Backend:**
```bash
pip install gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**Frontend:**
```bash
npm run build
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue on the repository.
