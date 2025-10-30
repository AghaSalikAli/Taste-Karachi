# Taste Karachi

This MLOps project predicts a restaurant's rating on a scale of 5 based on multiple features to help
owners improve.

Commands to run:
docker build -t taste-karachi .
docker run -p 8000:8000 --name taste-karachi-api taste-karachi
