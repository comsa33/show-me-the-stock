#\!/bin/bash
export MONGODB_URI="mongodb://admin:durwl4wlK@ruoserver.iptime.org:30017"
cd /home/ruo/my_project/show-me-the-stock/web-version/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
EOF < /dev/null