#!/bin/bash
# Arranca el dashboard Next.js
cd "$(dirname "$0")/frontend"
echo "→ http://localhost:3000/ticker/SPHL"
npm run dev
