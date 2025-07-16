# ROS2 driver for the Water Linked 3D Sonar Driver

This section describes the ROS2 package for the Water Linked Sonar 3D-15.

## Build Instructions
From the root of this repository, get the original WL API as a submodule
```bash
git submodule update --remote --init wl_3dsonar_driver/wl_api/
```
Then follow the instructions [here](https://github.com/waterlinked/Sonar-3D-15-api-example/blob/main/README.md) to install it.

And build the ROS pkg as usual
```bash
colcon build --packages-select wl_3dsonar_driver
```

## Run Instructions

```bash
ros2 run wl_3dsonar_driver wl_3dsonar_driver_node
```
