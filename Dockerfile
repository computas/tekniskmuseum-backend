# Use Ubuntu as the base image
FROM ubuntu:22.04
# Set the working directory in the container

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip



# Install required dependencies and tools
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    software-properties-common \
    apt-transport-https \
    ca-certificates

# Add Microsoft's package repository for the ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list -o /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update

# Install the ODBC Driver 17 for SQL Server
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Clean up to reduce the image size
RUN rm -rf /var/lib/apt/lists/*


# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 



#COPY install-mysql-driver.sh .
#RUN chmod +x install-mysql-driver.sh
#RUN bash ./install-mysql-driver.sh

# Copy the rest of the application code to the container
COPY . /app
WORKDIR /app


# Expose the port that your app runs on
EXPOSE 8000

# Command to run Gunicorn with Gevent worker class for async handling
#CMD ["python3", "main.py"]
CMD ["gunicorn", "--bind=0.0.0.0", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w=1", "--chdir", "src/", "main:app"]

