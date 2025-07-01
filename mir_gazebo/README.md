# mir_gazebo

# run instructions

The following instructions were tested under ROS2 jazzy and Gazebo harmonic.

Run without a namespace:

```bash
ros2 launch mir_gazebo mir_gazebo_launch.py world:=maze
```

Run with a namespace:

```bash
ros2 launch mir_gazebo mir_gazebo_launch.py namespace:=robot_ns world:=maze
```

If no world arg is provided, the robot will spawn in an empty world.

This will launch the simulation in Gazebo harmonic, rviz2 and a separate terminal (xterm)
to teleoperate the base with the keyboard. The Gazebo - ROS2 bridge is also launched and selected topics
are exposed to ROS2.
