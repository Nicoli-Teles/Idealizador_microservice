#!/bin/bash
cd /home/site/wwwroot
echo "🚀 Iniciando aplicação FastAPI no Azure..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
