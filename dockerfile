# Use a base image with Java pre-installed or install Java 11 explicitly
FROM debian:bullseye-slim
FROM openjdk:11

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install pyspark

# Update package repository and remove any existing Java installations
RUN apt-get update && \
    apt-get remove -y openjdk-* && \
    apt-get autoremove -y && \
    apt-get clean

# Install OpenJDK 11
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get clean

# Set JAVA_HOME and update PATH
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Verify Java installation
RUN java -version

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app

# Set default command (adjust according to your app)
CMD ["bash"]
