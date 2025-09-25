"""
mir robot scan merger launch file based on ira_laser_tools:
      subscribe to multiple LaserScan topics and merge them into a single one.

i.e.: subscribe to /b_scan and /f_scan topics, merge them into a single /scan topic or with namespace:
      subscribe to /robot_ns/b_scan and /robot_ns/f_scan topics, merge them into a single /robot_ns/scan topic

Make sure to install via source the right version of ira_laser_tools:
      github.com/relffok/ira_laser_tools.git ros2-devel branch
      tested against commit: a6bfd0e1114746b70e7314366e808e709b61bb93

NOTE: there is a workaround in this launch file. laserscan_multi_merger (external) node ignores
      the node namespace when it parses the laserscan_topics and destination_frame strings,
      so a namespaced launch causes topics like /robot_ns/robot_ns/b_scan and TF lookup errors.
      This launch-file workaround keeps the node in the global namespace and
      pre-pends the desired robot prefix (robot_ns/…) directly to each topic/frame parameter,
      ensuring the node subscribes and publishes exactly once under /robot_ns/* without code changes to ira_laser_tools.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def make_laser_merger(context):
    # Resolve launch args to plain strings
    ns = LaunchConfiguration('namespace').perform(context)      # '' or 'robot_ns'
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Helper: add namespace only when the user supplied one (no leading '/')
    def ns_join(name: str) -> str:
        return f'{ns}/{name}' if ns else name

    # Parameters that must already contain the prefix
    laserscan_topics      = f'{ns_join("b_scan")} {ns_join("f_scan")}'
    destination_frame     = ns_join('virtual_laser_link')
    scan_dest_topic       = ns_join('scan')
    cloud_dest_topic      = ns_join('scan_cloud')

    return [Node(
        package='ira_laser_tools',
        executable='laserscan_multi_merger',
        name='mir_laser_scan_merger',     # node lives in the root namespace
        # namespace is intentionally left empty -> prevents “ns/ns/topic” doubling
        parameters=[{
            'laserscan_topics':        laserscan_topics,
            'destination_frame':       destination_frame,
            'scan_destination_topic':  scan_dest_topic,
            'cloud_destination_topic': cloud_dest_topic,
            'min_height':             -0.25,
            'max_completion_time':     0.05,
            'max_merge_time_diff':     0.005,
            'use_sim_time':            use_sim_time,
            'best_effort':             False,
        }],
        output='screen',
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation (Gazebo) clock if true',
        ),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Optional namespace for all LaserScan I/O',
        ),
        OpaqueFunction(function=make_laser_merger),
    ])
