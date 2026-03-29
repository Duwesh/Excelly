# Excel Analysis Agent Frontend

This is the Next.js frontend for the Excel Analysis Agent. It provides a beautiful, modern chat interface to interact with your data.

## Getting Started

### Prerequisites
- Node.js 18.17 or later

### Installation

1. Install dependencies:
```bash
npm install
```

2. Make sure your environment variables are set. See the `.env.example` in the repository root. By default, the frontend expects the backend API to be running at `http://localhost:8000`.

### Running the Development Server

1. **Start the backend server first** (from the repository root):
```bash
# Terminal 1: Sandbox Server
python run_sandbox_server.py

# Terminal 2: FastAPI Backend
fastapi dev main.py
```

2. **Start the Next.js frontend** (from this `web` directory):
```bash
# Terminal 3: Frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Tech Stack
- [Next.js](https://nextjs.org/) (App Router)
- [Tailwind CSS v4](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Lucide Icons](https://lucide.dev/)
