# Use the official Python image from the Docker Hub
FROM mcr.microsoft.com/devcontainers/python:3.9

# Fix Yarn repository issue by removing it temporarily
RUN rm -f /etc/apt/sources.list.d/yarn.list || true

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg default-jdk && \
    apt-get clean

# Alternative: Install Temurin JDK (commented out - using default-jdk instead)
# RUN wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /usr/share/keyrings/adoptium-archive-keyring.gpg && \
#     echo "deb [signed-by=/usr/share/keyrings/adoptium-archive-keyring.gpg] https://packages.adoptium.net/artifactory/deb $(grep VERSION_CODENAME /etc/os-release | cut -d= -f2) main" | tee /etc/apt/sources.list.d/adoptium.list && \
#     apt-get update && \
#     apt-get install -y temurin-11-jdk

# Set JAVA_HOME dynamically
RUN JAVA_HOME_DETECTED=$(dirname $(dirname $(readlink -f $(which java)))) && \
    echo "export JAVA_HOME=${JAVA_HOME_DETECTED}" >> /etc/bash.bashrc && \
    echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /etc/bash.bashrc

# Set environment variables for Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-arm64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install Python dependencies
RUN pip install --no-cache-dir \
    jupyter \
    pyspark>=3.3.0 \
    pandas>=2.0.0 \
    python-dotenv>=1.0.0 \
    tqdm>=1.0.0

# Try to install Nekt SDK (optional - will not fail build if unavailable)
RUN pip install --no-cache-dir git+https://github.com/nektcom/nekt-sdk-py.git#egg=nekt-sdk || \
    echo "Warning: nekt-sdk installation failed. You may need to install it manually with credentials."

# Set PySpark environment variables
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Expose port 8888 for Jupyter Notebook
EXPOSE 8888

# Set the working directory
WORKDIR /workspace