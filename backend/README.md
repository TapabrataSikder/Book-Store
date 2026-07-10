# Purnasree Backend — Local Run Instructions

This guide covers starting the backend and frontend locally so you can test the UI and API together.

## 1. Prerequisites
- Python 3.10+ installed
- Node.js and npm or yarn installed
- Docker Desktop running (recommended for MongoDB) or a local MongoDB installation

## 2. Start MongoDB
Choose one option:

### Option A — Docker (recommended)
```bash
docker run -d --name purnasree-mongo -p 27017:27017 mongo:6.0
```

Verify it is running:
```bash
docker ps --filter name=purnasree-mongo
```

### Option B — Local `mongod`
```powershell
mkdir C:\data\db
mongod --dbpath C:\data\db --bind_ip 127.0.0.1
```

### Option C — Windows service
```powershell
net start MongoDB
```

## 3. Start the backend
From the project root:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
```

If you are already inside the `backend` folder, this also works:
```bash
python -m uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

### Backend health checks
```bash
curl http://127.0.0.1:8000/api/store-info
curl http://127.0.0.1:8000/api/products
```

## 4. Start the frontend UI
Open a second terminal and run:

```bash
cd frontend
npm install
```

If you use Yarn instead of npm:
```bash
yarn install
```

Set the frontend to use your local backend by creating or editing `frontend/.env.local`:
```env
REACT_APP_BACKEND_URL=http://127.0.0.1:8000
```

Then start the UI:
```bash
npm start
```

Or with Yarn:
```bash
yarn start
```

The app should open in your browser at:
```text
http://localhost:3000
```

## 5. Verify the full flow
- Backend API: http://127.0.0.1:8000/api/store-info
- Frontend UI: http://localhost:3000
- If the UI loads and the API responds, the local setup is working.

## 6. Stop services
- Backend: press `Ctrl+C` in the backend terminal
- Frontend: press `Ctrl+C` in the frontend terminal
- MongoDB container:
```bash
docker stop purnasree-mongo
docker rm purnasree-mongo
```

## 7. Notes
- The repository includes `backend/.env` with example environment values.
- Update secrets before deploying to production.
- If `uvicorn` is not found, use `python -m uvicorn ...` as shown above.