# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

# Install uv, the Python package installer
RUN pip install uv

# Copy the dependency files
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv pip install -r uv.lock --no-deps --system

# Install NLTK data for French
RUN python -m nltk.downloader punkt_tab

# Copy the rest of the application code
COPY . .

# Command to run the application
# We can override this in docker-compose.yml for more specific tasks
CMD ["uv", "run", "python", "run_graph.py"]
