# Dockerfile
# Use a slim Python image for smaller size
FROM python:3.10-slim-buster

# Set working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application using Uvicorn
# The --host 0.0.0.0 makes the server accessible from outside the container
# The --reload flag (optional) is useful for development but should be removed in production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
