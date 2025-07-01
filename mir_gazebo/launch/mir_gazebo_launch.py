# Copyright (c) 2018-2022, Martin Günther (DFKI GmbH) and contributors
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: relffok, oscar-lima

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetLaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource, FrontendLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, TextSubstitution, PythonExpression
from launch_ros.actions import Node

def _create_jsp_and_relay_nodes(context, *_):
    ns = context.launch_configurations.get('namespace', '')
    prefix = f'/{ns}' if ns else ''

    source_list = [
        f'{prefix}/mir_joint_states',
    ]

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        namespace=ns,
        output='screen',
        parameters=[{
            'use_sim_time': context.launch_configurations.get('use_sim_time', 'true') == 'true',
            'source_list': source_list,
            'rate': 60.0,
        }]
    )

    relay_joint_states_node = Node(
        package='topic_tools',
        executable='relay',
        name='joint_states_relay',      # no more “todo”
        namespace=ns,
        arguments=['joint_states', 'dynamic_joint_states'],
        output='screen',
    )

    return [joint_state_publisher_node, relay_joint_states_node]

def _create_rviz_node(context, *_):
    ns = context.launch_configurations.get('namespace', '')
    fixed_frame = f'{ns}/odom' if ns else 'odom'

    rviz_cfg = context.launch_configurations.get('rviz_config_file')
    use_sim  = context.launch_configurations.get('use_sim_time', 'true') == 'true'

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        namespace=ns,                     # RViz node itself can sit in the ns
        output={'both': 'log'},
        arguments=['-d', rviz_cfg, '-f', fixed_frame],
        parameters=[{'use_sim_time': use_sim}],
    )
    return [rviz_node]

def generate_launch_description():

    mir_description_dir = get_package_share_directory('mir_description')
    mir_gazebo_dir = get_package_share_directory('mir_gazebo')

    rviz_config_file = LaunchConfiguration('rviz_config_file')

    ld = LaunchDescription()

    declare_namespace_arg = DeclareLaunchArgument(
        'namespace', default_value='', description='Namespace to push all topics into.'
    )

    declare_mir_type_arg = DeclareLaunchArgument(
        'mir_type', default_value='mir_100', description='Either mir_100 or mir_250 are supported.'
    )

    declare_robot_x_arg = DeclareLaunchArgument(
        'robot_x', default_value='0.0', description='Spawning position of robot (x)'
    )

    declare_robot_y_arg = DeclareLaunchArgument(
        'robot_y', default_value='0.0', description='Spawning position of robot (y)'
    )

    declare_robot_yaw_arg = DeclareLaunchArgument(
        'robot_yaw', default_value='0.0', description='Spawning position of robot (yaw)'
    )

    declare_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true', description='Use simulation (Gazebo) clock if true'
    )

    declare_world_arg = DeclareLaunchArgument(
        'world', default_value='empty', description='Choose simulation world. Available worlds: empty, maze'
    )

    declare_verbose_arg = DeclareLaunchArgument(
        'verbose', default_value='false', description='Set to true to enable verbose mode for Gazebo.'
    )

    declare_teleop_arg = DeclareLaunchArgument(
        'teleop_enabled', default_value='true', description='Set to true to enable teleop to manually move MiR around.'
    )

    declare_rviz_arg = DeclareLaunchArgument(
        'rviz_enabled', default_value='true', description='Set to true to launch rviz.'
    )

    declare_rviz_config_arg = DeclareLaunchArgument(
        'rviz_config_file',
        default_value=os.path.join(mir_gazebo_dir, 'rviz', 'mir_visualization.rviz'),
        description='Define rviz config file to be used.',
    )

    declare_gui_arg = DeclareLaunchArgument('gui', default_value='true', description='Set to "false" to run headless.')

    world_file = PathJoinSubstitution([
        mir_gazebo_dir,
        'worlds',
        PythonExpression(['\'', LaunchConfiguration('world'), TextSubstitution(text='.world'), '\''])
    ])

    launch_gazebo_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]
        ),
        launch_arguments={'gz_args': ['-r -v4 ', world_file], 'on_exit_shutdown': 'true'}.items(),
    )

    launch_mir_description = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource(os.path.join(mir_description_dir, 'launch', 'robot_state_publisher.launch')),
        launch_arguments={'mir_type':LaunchConfiguration('mir_type'), 'tf_prefix':LaunchConfiguration('namespace')}.items(),
    )

    launch_mir_robot_scan_merger = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(mir_gazebo_dir, 'launch', 'includes', 'mir_robot_scan_merger_launch.py')),
        launch_arguments={'namespace': LaunchConfiguration('namespace'),
                          'use_sim_time': 'true'}.items(),
    )

    def process_namespace(context):
        robot_name = "mir_robot"
        try:
            namespace = context.launch_configurations['namespace']
            robot_name = namespace + '/' + robot_name
        except KeyError:
            pass
        return [SetLaunchConfiguration('robot_name', robot_name)]

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', LaunchConfiguration('robot_name'),
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.0',
            '-R', '0.0', '-P', '0.0', '-Y', '0.0',
        ],
        namespace=LaunchConfiguration('namespace'),
        output='screen',
    )

    gz_bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='mir_gz_bridge',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        parameters=[{
            'config_file': PathJoinSubstitution([
                mir_gazebo_dir, 'config', 'ros_gz_bridge_config.yaml'
            ]),
            'expand_gz_topic_names': True
        }]
    )

    launch_rviz = OpaqueFunction(
        function=_create_rviz_node,
        condition=IfCondition(LaunchConfiguration('rviz_enabled')),
    )

    launch_teleop = Node(
        condition=IfCondition(LaunchConfiguration("teleop_enabled")),
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        namespace=LaunchConfiguration('namespace'),
        output='screen',
        prefix='xterm -e',
    )

    ld.add_action(OpaqueFunction(function=process_namespace))
    ld.add_action(declare_namespace_arg)
    ld.add_action(declare_mir_type_arg)
    ld.add_action(declare_robot_x_arg)
    ld.add_action(declare_robot_y_arg)
    ld.add_action(declare_robot_yaw_arg)
    ld.add_action(declare_sim_time_arg)
    ld.add_action(declare_world_arg)
    ld.add_action(declare_verbose_arg)
    ld.add_action(declare_teleop_arg)
    ld.add_action(declare_rviz_arg)
    ld.add_action(declare_rviz_config_arg)
    ld.add_action(declare_gui_arg)

    ld.add_action(launch_gazebo_world)
    ld.add_action(launch_mir_description)
    ld.add_action(OpaqueFunction(function=_create_jsp_and_relay_nodes))
    ld.add_action(launch_mir_robot_scan_merger)
    ld.add_action(spawn_robot)
    ld.add_action(gz_bridge_node)
    ld.add_action(launch_rviz)
    ld.add_action(launch_teleop)

    return ld
