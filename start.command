#!/bin/bash

# Dilucion Data — Launch Script
# Abre backend (FastAPI) + frontend (Next.js) en Terminal

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "╔══════════════════════════════════════╗"
echo "║      Dilucion Data — Arranque        ║"
echo "╚══════════════════════════════════════╝"
echo ""

cleanup() {
  echo ""
  echo "⏹  Parando servicios..."
  for PORT in 8000 3000; do
    PID=$(lsof -ti:$PORT -sTCP:LISTEN 2>/dev/null)
    [ -n "$PID" ] && kill -9 "$PID" 2>/dev/null
  done
  echo "   ✅ Servicios detenidos."
  echo "[$(date)] 🛑 App cerrada" >> "$DIR/server.log"
}
trap cleanup EXIT INT TERM

PYTHON="$DIR/backend/.venv/bin/python3"
NEXT="$DIR/frontend/node_modules/.bin/next"
LOG="$DIR/server.log"

# Kill existing processes
echo "[1/2] Preparando puertos..."
for PORT in 8000 3000; do
  PID=$(lsof -ti:$PORT -sTCP:LISTEN 2>/dev/null)
  [ -n "$PID" ] && kill -9 "$PID" 2>/dev/null && echo "   Puerto $PORT liberado"
done

# Start backend
echo "[2/2] Iniciando servicios..."
cd "$DIR/backend"
nohup "$PYTHON" main.py serve --port 8000 >> "$LOG" 2>&1 &
echo "   ⚙️  Backend (PID $!)"

# Start frontend
cd "$DIR/frontend"
nohup "$NEXT" dev -p 3000 >> "$LOG" 2>&1 &
echo "   ⚙️  Frontend (PID $!)"

# Health check
echo ""
echo "⏳ Verificando..."
BACKEND_OK=0; FRONTEND_OK=0
for i in $(seq 1 15); do
  [ $BACKEND_OK -eq 0 ] && lsof -ti:8000 -sTCP:LISTEN >/dev/null 2>&1 && BACKEND_OK=1 && echo "   ✅ Backend OK (${i}s)"
  [ $FRONTEND_OK -eq 0 ] && lsof -ti:3000 -sTCP:LISTEN >/dev/null 2>&1 && FRONTEND_OK=1 && echo "   ✅ Frontend OK (${i}s)"
  [ $BACKEND_OK -eq 1 ] && [ $FRONTEND_OK -eq 1 ] && break
  sleep 2
done

echo ""
if [ $BACKEND_OK -eq 1 ] && [ $FRONTEND_OK -eq 1 ]; then
  echo "✅ Todo listo — http://localhost:3000"
  echo ""
  echo "   NO cierres esta terminal."
  echo "   Ctrl+C para detener."
  echo "[$(date)] ✅ Arrancado OK" >> "$LOG"
  open http://localhost:3000 2>/dev/null || true
else
  echo "⚠️  Fallo: backend=$BACKEND_OK frontend=$FRONTEND_OK"
  echo "   Revisa: $LOG"
  echo "[$(date)] ⚠️ Fallo backend=$BACKEND_OK frontend=$FRONTEND_OK" >> "$LOG"
fi

# Keep alive until Ctrl+C
wait
