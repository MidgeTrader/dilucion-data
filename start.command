#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

# Start backend
cd "$DIR/backend"
source .venv/bin/activate 2>/dev/null
python3 main.py serve --port 8000 &
BACKEND_PID=$!

# Start frontend
cd "$DIR/frontend"
npx next dev -p 3000 &
FRONTEND_PID=$!

# Wait then open browser
sleep 5
open http://localhost:3000

# Wait for either to exit
wait $BACKEND_PID $FRONTEND_PID
