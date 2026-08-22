FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    ROS_DISTRO=jazzy \
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    UV_PROJECT_ENVIRONMENT=/opt/arms-lab/.venv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    gnupg2 \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    locales \
    python3.12 \
    python3.12-venv \
    python3-pip \
    software-properties-common \
    && add-apt-repository universe \
    && locale-gen en_US.UTF-8 \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
       | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" \
       > /etc/apt/sources.list.d/ros2.list \
    && apt-get update && apt-get install -y --no-install-recommends \
       python3-colcon-common-extensions \
       ros-jazzy-rmw-cyclonedds-cpp \
       ros-jazzy-robot-state-publisher \
       ros-jazzy-ros-base \
       ros-jazzy-rosgraph-msgs \
       ros-jazzy-sensor-msgs \
       ros-jazzy-tf2-ros \
       ros-jazzy-trajectory-msgs \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /opt/arms-lab
COPY pyproject.toml README.md ./
RUN uv venv --python /usr/bin/python3.12 --system-site-packages "$UV_PROJECT_ENVIRONMENT" \
    && uv sync --no-dev --no-install-project

COPY . .
RUN uv sync --no-dev

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /opt/arms-lab/run.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "arms-lab"]
