from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource, AnyLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, TextSubstitution, LaunchConfiguration
from launch.actions import GroupAction, OpaqueFunction
from launch_ros.actions import PushRosNamespace, SetRemap, SetParameter


def generate_launch_description():
    return LaunchDescription([
        # Handle parameters.
        DeclareLaunchArgument(
            "id", default_value=TextSubstitution(text="0")
        ),
        DeclareLaunchArgument(
            "namespace", default_value=["agent", LaunchConfiguration("id")]
        ),
        DeclareLaunchArgument(
            "initial_pos_x", default_value='0.0'
        ),
        DeclareLaunchArgument(
            "initial_pos_y", default_value='0.0'
        ),
        DeclareLaunchArgument(
            "initial_pos_z", default_value='0.0'
        ),
        DeclareLaunchArgument(
            'map', default_value='cumberland'
        ),
        DeclareLaunchArgument(
            'map_file', default_value=[FindPackageShare("simulation_base"), "/models/maps/", LaunchConfiguration("map"), "/", LaunchConfiguration("map"), ".yaml"]
        ),
        DeclareLaunchArgument(
            'model_name', default_value='waffle'
        ),
        DeclareLaunchArgument(
            'urdf_path', default_value=[FindPackageShare('simulation_base'), '/models/robots/', LaunchConfiguration("model_name"), '.model']
        ),
        DeclareLaunchArgument(
            'use_rviz', default_value='false'
        ),
        DeclareLaunchArgument(
            'simulator_agent_integration_launch_file',
            default_value=[FindPackageShare("simulation_base"), "/launch/simulator/gazebo/agent.launch.yaml"]
        ),


        # Start the navigation stack.
        GroupAction(
            actions=[
                # Manually remap the scan topic.
                SetRemap(src='/scan', dst=['/agent', LaunchConfiguration("id"), '/scan']),

                # Run the navigation stack.
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([
                        PathJoinSubstitution([
                            FindPackageShare('simulation_base'),
                            'launch',
                            'agent',
                            'robot_navigation2.launch.py'
                        ])
                    ]),
                    launch_arguments={
                        'namespace': LaunchConfiguration("namespace"),
                        'use_namespace': 'True',
                        'use_composition': 'False',
                        'use_sim_time': 'True',
                        'map': LaunchConfiguration("map_file"),
                        'params_file': PathJoinSubstitution([
                            FindPackageShare('simulation_base'),
                            'config',
                            'nav2_params.yaml'
                        ]),
                        'pose_x': LaunchConfiguration("initial_pos_x"),
                        'pose_y': LaunchConfiguration("initial_pos_y"),
                        'log_level': 'warn',
                    }.items(),
                ),
            ]
        ),

        # Start RViz if use_rviz=true.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare('nav2_bringup'),
                    'launch',
                    'rviz_launch.py'
                ])
            ]),
            launch_arguments={
                'namespace': LaunchConfiguration("namespace"),
                'use_namespace': 'True',
                'rviz_config': PathJoinSubstitution([
                    FindPackageShare('nav2_bringup'),
                    'rviz',
                    'nav2_namespaced_view.rviz'
                ]),
            }.items(),
            condition = IfCondition(LaunchConfiguration("use_rviz")),
        ),

        # Instantiate the robot in the simulator.
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(
                LaunchConfiguration("simulator_agent_integration_launch_file")
            ),
            launch_arguments={
                "id": LaunchConfiguration("id"),
                "namespace": LaunchConfiguration("namespace"),
                "urdf_path": LaunchConfiguration("urdf_path"),
                "initial_pos_x": LaunchConfiguration("initial_pos_x"),
                "initial_pos_y": LaunchConfiguration("initial_pos_y"),
                "initial_pos_z": LaunchConfiguration("initial_pos_z")
            }.items(),
        ),
    ])

def createRsp(context: LaunchContext, urdf_path_subst):
    ''' Create the robot state publisher. '''
    
    urdf_path = str(context.perform_substitution(urdf_path_subst))
    robotDesc = getUrdfData(urdf_path)

    return [Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robotDesc
        }],
    )]

def getUrdfData(filepath):
    ''' Gets URDF data from filepath and returns as string. '''

    robot_desc = ""
    with open(filepath, 'r') as infp:
        robot_desc = infp.read()
    return robot_desc
