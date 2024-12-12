# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements.txt first (optimizing layer cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

ENV PORT 8080
# Expose port
EXPOSE 8080


# Start application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app.main:app"]
