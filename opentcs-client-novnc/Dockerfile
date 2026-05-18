FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for VNC, Openbox, Java, and wget
RUN apt-get update && apt-get install -y \
    tigervnc-standalone-server \
    tigervnc-common \
    novnc \
    websockify \
    openbox \
    wget \
    unzip \
    openjdk-17-jre \
    xterm \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Setup user
RUN useradd -m -s /bin/bash opentcs
USER opentcs
WORKDIR /home/opentcs

# Download OpenTCS 7.2.1
RUN wget -q https://github.com/openTCS/opentcs/releases/download/v7.2.1/openTCS-7.2.1-bin.zip -O /tmp/opentcs.zip && \
    unzip -q /tmp/opentcs.zip -d /home/opentcs/ && \
    rm /tmp/opentcs.zip && \
    mv /home/opentcs/openTCS-7.2.1** /home/opentcs/opentcs

# Fix line endings and permissions for start scripts
RUN cd /home/opentcs/opentcs && \
    chmod +x */*.sh

# Create VNC directory
RUN mkdir -p /home/opentcs/.vnc

# Set VNC password (opentcs)
RUN echo "opentcs" | vncpasswd -f > /home/opentcs/.vnc/passwd && \
    chmod 600 /home/opentcs/.vnc/passwd

# Setup Openbox autostart
RUN mkdir -p /home/opentcs/.config/openbox
RUN echo "xterm -e 'echo Welcome to OpenTCS Client VNC; bash' &" > /home/opentcs/.config/openbox/autostart

# Startup script
COPY --chown=opentcs:opentcs start.sh /home/opentcs/start.sh
RUN chmod +x /home/opentcs/start.sh

# Expose noVNC port
EXPOSE 8080

CMD ["/home/opentcs/start.sh"]
