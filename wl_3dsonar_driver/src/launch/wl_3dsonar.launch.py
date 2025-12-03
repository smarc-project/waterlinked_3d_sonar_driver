from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='wl_3dsonar_driver',
            executable='wl_3dsonar_driver_node',
            name='wl_3dsonar_driver_node',
            output='screen',
            parameters=[
                {'multicast_or_unicast': 'multicast'}
            ]
            #parameters=[
             #   {'sonar_ip': '192.168.194.96'},  # Change to your sonar IP, '192.168.194.96' is the fallback ip.
              #  {'speed_of_sound': 1491}
            #]
        )
    ])
