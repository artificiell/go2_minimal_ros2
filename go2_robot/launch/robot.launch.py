import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import FrontendLaunchDescriptionSource, PythonLaunchDescriptionSource

def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    with_joystick = LaunchConfiguration('joystick', default='true')
    with_teleop = LaunchConfiguration('teleop', default='true')

    robot_token = os.getenv('ROBOT_TOKEN', '') # how does this work for multiple robots?
    robot_ip = os.getenv('ROBOT_IP', '')
    print("Robot IP:", robot_ip)

    conn_type = os.getenv('CONN_TYPE', 'webrtc')
    conn_mode = "single" if len(robot_ip_lst) == 1 and conn_type != "cyclonedds" else "multi"

    # RViz config
    rviz_config = "single_robot_conf.rviz"
    if conn_type == 'cyclonedds':
        rviz_config = "cyclonedds_config.rviz"

    # Load robot description
    urdf = os.path.join(
        get_package_share_directory('go2_robot'),
        'urdf',
        'go2.urdf')
    with open(urdf, 'r') as infp:
        robot_desc = infp.read()

    # Read config parameters
    joy_params = os.path.join(
        get_package_share_directory('go2_robot'),
        'config',
        'joystick.yaml'
    )
    default_config_topics = os.path.join(
        get_package_share_directory('go2_robot'),
        'config',
        'twist_mux.yaml'
    )

    # Lanch nodes
    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time,
                         'robot_description': robot_desc}],
            arguments=[urdf]
        ),
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            remappings=[
                ('cloud_in', 'point_cloud2'),
                ('scan', 'scan'),
            ],
            parameters=[{
                'target_frame': 'base_link',
                'max_height': 0.5
            }],
            output='screen',
        ),
        Node(
            package='go2_robot',
            executable='go2_driver_node',
            parameters=[{'robot_ip': robot_ip, 'token': robot_token, "conn_type": conn_type}],
        ),
        Node(
            package='joy',
            executable='joy_node',
            condition=IfCondition(with_joystick),
            parameters=[joy_params]
        ),
        Node(
            package='teleop_twist_joy',
            executable='teleop_node',
            name='teleop_node',
            condition=IfCondition(with_joystick),
            parameters=[default_config_topics],
        ),
        Node(
            package='twist_mux',
            executable='twist_mux',
            output='screen',
            condition=IfCondition(with_teleop),
            parameters=[
                {'use_sim_time': use_sim_time},
                default_config_topics
            ],
        ),
    ])
