# Document Summarizer

A full-stack web application that allows users to upload PDF and TXT documents and get AI-powered summaries. Features include user authentication (sign up, login, and Google OAuth) and a modern, responsive UI.

## Features

- 🔐 User Authentication
  - Email/Password sign up and login
  - Google OAuth integration
  - JWT-based session management

- 📄 Document Processing
  - Upload PDF files
  - Upload TXT files
  - Extract text from documents
  - AI-powered summarization

- 🎨 Modern UI
  - Responsive design
  - Clean and intuitive interface
  - Real-time document management

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM for database
- **SQLite** - Database (can be easily changed to PostgreSQL)
- **PyPDF2** - PDF text extraction
- **OpenAI API** - AI summarization (with fallback)
- **JWT** - Authentication tokens
- **bcrypt** - Password hashing

### Frontend
- **React** - UI framework
- **Vite** - Build tool
- **React Router** - Navigation
- **Axios** - API requests
- **Google OAuth** - Google authentication

## Quick Start

For a quick start, you can use the provided startup script:

```bash
./start.sh
```

This will automatically:
- Set up the backend virtual environment
- Install all dependencies
- Start both backend and frontend servers

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a `.env` file in the backend directory):
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./documents.db
OPENAI_API_KEY=your-openai-api-key-optional
GOOGLE_CLIENT_ID=your-google-client-id-optional
```

5. Run the backend server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the frontend directory:
```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-client-id-optional
```

4. Run the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google+ API
4. Go to "Credentials" and create OAuth 2.0 Client ID
5. Add authorized redirect URIs:
   - `http://localhost:3000` (for development)
6. Copy the Client ID and add it to your `.env` files

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Sign up for a new account or use Google OAuth
4. Upload a PDF or TXT file
5. Click "Generate Summary" to get an AI-powered summary

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /token` - Login and get access token
- `POST /google-auth` - Google OAuth authentication
- `GET /me` - Get current user information

### Documents
- `POST /upload` - Upload a document (PDF or TXT)
- `GET /documents` - Get all user documents
- `POST /summarize/{document_id}` - Generate summary for a document

## Notes

- The OpenAI API key is optional. If not provided, the app will use a simple extractive summarization method.
- For production, change the `SECRET_KEY` to a secure random string.
- Consider using PostgreSQL instead of SQLite for production.
- The current implementation stores only the first 5000 characters of documents. For production, consider storing full documents in a file storage service.

## License

MIT

