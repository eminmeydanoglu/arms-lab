FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=jazzy \
    UV_PROJECT_ENVIRONMENT=/opt/arms-lab/.venv

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg2 locales software-properties-common \
    python3.12 python3.12-venv python3-pip \
    && locale-gen en_US.UTF-8 \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
       -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" \
       > /etc/apt/sources.list.d/ros2.list \
    && apt-get update && apt-get install -y --no-install-recommends \
       ros-jazzy-ros-base \
       ros-jazzy-sensor-msgs \
       ros-jazzy-trajectory-msgs \
       ros-jazzy-rosgraph-msgs \
       ros-jazzy-tf2-ros \
       ros-jazzy-robot-state-publisher \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /opt/arms-lab
COPY pyproject.toml ./
RUN uv sync --no-dev
COPY . .
RUN uv sync

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /opt/arms-lab/run.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "arms-lab"]
