#!/bin/bash
# Start both backend and frontend concurrently

echo "🚀 Starting AI Agent Development Environment..."

# Kill any existing processes on these ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start backend in background
echo "📡 Starting backend server..."
cd backend && python working_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background  
echo "🎨 Starting frontend server..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo "✅ Both servers started!"
echo "📡 Backend: http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    # Kill any remaining processes on these ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on interrupt
trap cleanup INT TERM

# Wait for user interrupt
wait