# Shared FR3 development and headless acceptance environment.
# AI model weights are deliberately supplied outside this image.
FROM ros:jazzy-ros-base-noble

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pytest \
    ros-jazzy-mujoco-ros2-control \
    ros-jazzy-joint-trajectory-controller \
    ros-jazzy-joint-state-broadcaster \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-control-msgs \
    ros-jazzy-trajectory-msgs \
    ros-jazzy-sensor-msgs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY src/ src/
COPY assets/models/franka_fr3_v2/ assets/models/franka_fr3_v2/
COPY tests/ tests/

RUN source /opt/ros/jazzy/setup.bash \
    && colcon build

ENV FR3_MUJOCO_SCENE=/workspace/assets/models/franka_fr3_v2/scene.xml
CMD ["bash"]
