#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /opt/fr3_wave/setup.bash

exec "$@"
