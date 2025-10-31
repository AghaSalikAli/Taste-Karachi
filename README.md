# Taste Karachi

This MLOps project predicts a restaurant's rating on a scale of 5 based on multiple features to help
owners improve.

## 🚀 Quick Start with Docker Compose (Recommended)

The easiest way to run both the API and web interface:

```powershell
docker-compose up --build
```

Then access:
- **Streamlit Web Interface**: http://localhost:8501 (User-friendly UI)
- **FastAPI Backend**: http://localhost:8000 (REST API)
- **API Documentation**: http://localhost:8000/docs

For detailed Docker Compose instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md)

## 🐳 Manual Docker Commands (Alternative)

### Build and run FastAPI only:

```powershell
docker build -t taste-karachi .

docker run -p 8000:8000 --name taste-karachi-api taste-karachi
```

Once the container is up and running, in a new terminal run:

```powershell
python src/test.py
```

## 💻 Local Development

### Start FastAPI:
```powershell
python src/api.py
```

### Start Streamlit:
```powershell
streamlit run src/streamlit_app.py
```

## 📊 Features

- **Machine Learning Model**: Predicts restaurant ratings based on 30+ features
- **REST API**: FastAPI backend with automatic documentation
- **Web Interface**: Streamlit frontend for easy interaction
- **Containerized**: Docker and Docker Compose support
- **MLOps Pipeline**: MLflow integration for model tracking

