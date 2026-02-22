*[中文文档](README.md) | [English Documentation](README_en.md)*

# Akari Task Scheduler

A local task scheduling application with web interface for defining, testing, and monitoring scheduled tasks.

## Features

- **Task Scheduling**: Support for both cron expressions and interval-based scheduling
- **Task Execution**: Execute any command-line program with arguments
- **Logging**: Capture and view stdout, stderr, exit codes, and execution details
- **Web Interface**: Modern Vue.js frontend with dark/light theme support
- **Internationalization**: English and Chinese language support
- **REST API**: Fully documented API for integration with other clients
- **Local Database**: SQLite database for data persistence
- **No Authentication**: Simple local use without authentication overhead

## Project Structure

```
akari/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Configuration and events
│   │   ├── db/       # Database connection
│   │   ├── models/   # Database models
│   │   └── scheduler/# Task scheduling logic
│   ├── requirements.txt
│   └── main.py       # Application entry point
└── frontend/         # Vue.js frontend
    ├── src/
    │   ├── components/
    │   ├── views/    # Page components
    │   ├── stores/   # Pinia stores
    │   ├── locales/  # i18n translations
    │   └── styles/   # Global styles
    ├── package.json
    └── vite.config.js
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- SQLite3 (included with Python)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd akari/backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/MacOS:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the backend server:
   ```bash
   python main.py
   ```
   The server will start at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/api/docs`
   - Alternative Docs: `http://localhost:8000/api/redoc`

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd akari/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will start at `http://localhost:3000`

4. Access the application at `http://localhost:3000`

## Usage

### Creating a Task

1. Click "New Task" in the task list page
2. Fill in task details:
   - **Name**: Descriptive name for the task
   - **Command**: Full path to executable or command in PATH
   - **Arguments**: Optional command-line arguments
   - **Schedule Type**: Choose between Cron or Interval
   - **Schedule Details**: Cron expression or interval in seconds
   - **Timeout**: Maximum execution time
   - **Max Concurrent**: Limit simultaneous executions
   - **Enabled**: Enable/disable the task

### Example Tasks

1. **Python script every 5 minutes**:
   - Command: `python`
   - Arguments: `C:\scripts\backup.py`
   - Schedule Type: Cron
   - Cron Expression: `*/5 * * * *`

2. **Shell script every 30 seconds**:
   - Command: `bash`
   - Arguments: `/home/user/scripts/monitor.sh`
   - Schedule Type: Interval
   - Interval: `30`

3. **One-time test execution**:
   - Create task with any schedule
   - Click "Test Execution" in task edit page

### Viewing Logs

- Navigate to "Logs" page to see execution history
- Filter logs by task, status, or search text
- View detailed logs including stdout/stderr
- Clear old logs or delete specific entries

## API Reference

The backend provides a RESTful API at `http://localhost:8000`

### Key Endpoints

- `GET /tasks` - List tasks with pagination
- `POST /tasks` - Create a new task
- `GET /tasks/{id}` - Get task details
- `PUT /tasks/{id}` - Update a task
- `DELETE /tasks/{id}` - Delete a task
- `POST /tasks/{id}/execute` - Execute task manually
- `GET /tasks/{id}/logs` - Get task execution logs
- `GET /logs` - Get all execution logs
- `DELETE /logs` - Clear logs with filters

See the interactive documentation at `/docs` for full API details.

## Configuration

### Backend Configuration

Edit `akari/backend/app/core/config.py` or create a `.env` file:

```env
DB_URL=sqlite:///akari.db
DEBUG=true
LOG_LEVEL=INFO
SCHEDULER_MAX_WORKERS=10
```

### Frontend Configuration

Edit `akari/frontend/vite.config.js` to change proxy settings or ports.

## Development

### Adding New Features

1. **New API endpoints**:
   - Add route in `app/api/`
   - Update model if needed
   - Test with Swagger UI

2. **Frontend pages**:
   - Create Vue component in `src/views/`
   - Add route in `src/router/index.ts`
   - Add translations in `src/locales/`

3. **Database changes**:
   - Update models in `app/models/`
   - Use aerich for migrations (TODO: add migration setup)

### Testing

Run backend tests:
```bash
cd backend
pytest
```

Run frontend tests:
```bash
cd frontend
npm test
```

## License

MIT License - see LICENSE file (to be added)