"""
Embodied AI Development Tools

This module provides a set of tools for embodied AI application development.
These tools can be registered with agents to enhance their capabilities.
"""

from typing import Dict, Any, List, Optional, Callable, Union
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from loguru import logger
from pathlib import Path
import base64
from io import BytesIO

# Base tool definition
class EmbodiedTool:
    """Base class for embodied AI development tools."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: The name of the tool
            description: A description of what the tool does
        """
        self.name = name
        self.description = description
    
    def __call__(self, *args, **kwargs):
        """Execute the tool functionality."""
        raise NotImplementedError("Tool functionality must be implemented in subclasses")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tool to a dictionary for registration with AG2."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters()
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the parameters for the tool."""
        raise NotImplementedError("Parameters must be defined in subclasses")

# Sensor simulation tools
class SensorSimulationTool(EmbodiedTool):
    """Tool for simulating sensor data for embodied AI development."""
    
    def __init__(self):
        """Initialize the sensor simulation tool."""
        super().__init__(
            name="simulate_sensor_data",
            description="Simulate sensor data for embodied AI testing and development."
        )
    
    def __call__(
        self,
        sensor_type: str,
        parameters: Dict[str, Any],
        noise_level: float = 0.1,
        return_visualization: bool = False
    ) -> Dict[str, Any]:
        """
        Simulate sensor data based on the specified parameters.
        
        Args:
            sensor_type: Type of sensor to simulate (camera, lidar, imu, etc.)
            parameters: Parameters for the sensor simulation
            noise_level: Level of noise to add to the simulation (0.0 to 1.0)
            return_visualization: Whether to return a visualization of the data
            
        Returns:
            Dict containing the simulated sensor data and metadata
        """
        try:
            # Validate inputs
            if noise_level < 0.0 or noise_level > 1.0:
                raise ValueError("Noise level must be between 0.0 and 1.0")
            
            # Simulate different sensor types
            if sensor_type.lower() == "camera":
                data = self._simulate_camera(parameters, noise_level)
            elif sensor_type.lower() == "lidar":
                data = self._simulate_lidar(parameters, noise_level)
            elif sensor_type.lower() == "imu":
                data = self._simulate_imu(parameters, noise_level)
            elif sensor_type.lower() == "force":
                data = self._simulate_force_sensor(parameters, noise_level)
            else:
                raise ValueError(f"Unsupported sensor type: {sensor_type}")
            
            # Generate visualization if requested
            visualization = None
            if return_visualization:
                visualization = self._visualize_sensor_data(sensor_type, data)
            
            # Prepare result
            result = {
                "sensor_type": sensor_type,
                "data": data,
                "metadata": {
                    "timestamp": "2023-01-01T00:00:00Z",  # Placeholder timestamp
                    "parameters": parameters,
                    "noise_level": noise_level
                }
            }
            
            if visualization:
                result["visualization"] = visualization
            
            return result
            
        except Exception as e:
            logger.error(f"Error simulating sensor data: {e}")
            return {"error": str(e)}
    
    def _simulate_camera(self, parameters: Dict[str, Any], noise_level: float) -> Dict[str, Any]:
        """Simulate camera sensor data."""
        # Extract parameters with defaults
        width = parameters.get("width", 640)
        height = parameters.get("height", 480)
        depth = parameters.get("depth", False)
        
        # Generate simulated RGB image
        rgb_data = np.random.rand(height, width, 3)
        # Add some structure to make it look more realistic
        x, y = np.meshgrid(np.linspace(0, 1, width), np.linspace(0, 1, height))
        pattern = np.sin(x * 10) * np.cos(y * 10)
        for i in range(3):
            rgb_data[:, :, i] = (rgb_data[:, :, i] * 0.3) + (pattern * 0.7)
        
        # Add noise
        rgb_data += np.random.normal(0, noise_level, rgb_data.shape)
        rgb_data = np.clip(rgb_data, 0, 1)
        
        # Convert to 8-bit format
        rgb_data = (rgb_data * 255).astype(np.uint8)
        
        result = {
            "rgb": rgb_data.tolist()  # Convert to list for JSON serialization
        }
        
        # Generate depth data if requested
        if depth:
            depth_data = np.zeros((height, width))
            # Create a simple depth pattern
            for i in range(height):
                for j in range(width):
                    depth_data[i, j] = ((i / height) ** 2 + (j / width) ** 2) * 10
            
            # Add noise
            depth_data += np.random.normal(0, noise_level, depth_data.shape)
            depth_data = np.clip(depth_data, 0, 10)
            
            result["depth"] = depth_data.tolist()
        
        return result
    
    def _simulate_lidar(self, parameters: Dict[str, Any], noise_level: float) -> Dict[str, Any]:
        """Simulate LIDAR sensor data."""
        # Extract parameters with defaults
        num_points = parameters.get("num_points", 1000)
        max_range = parameters.get("max_range", 100.0)
        angular_resolution = parameters.get("angular_resolution", 1.0)
        
        # Generate simulated point cloud
        angles = np.linspace(0, 2 * np.pi, int(360 / angular_resolution))
        distances = np.random.rand(len(angles)) * max_range
        
        # Add some structure to make it look more realistic
        for i in range(len(angles)):
            # Simulate walls or objects
            if 0.5 < angles[i] < 1.5 or 3.5 < angles[i] < 4.5:
                distances[i] = max_range * 0.3
            elif 2.0 < angles[i] < 2.5:
                distances[i] = max_range * 0.5
        
        # Add noise
        distances += np.random.normal(0, noise_level * max_range * 0.1, distances.shape)
        distances = np.clip(distances, 0, max_range)
        
        # Convert to Cartesian coordinates
        x = distances * np.cos(angles)
        y = distances * np.sin(angles)
        z = np.zeros_like(x)
        
        # Combine into point cloud
        points = np.column_stack((x, y, z))
        
        # Randomly sample if more points were requested
        if num_points > len(points):
            # Duplicate points and add noise
            indices = np.random.choice(len(points), num_points - len(points))
            extra_points = points[indices] + np.random.normal(0, noise_level, (len(indices), 3))
            points = np.vstack((points, extra_points))
        elif num_points < len(points):
            # Randomly sample points
            indices = np.random.choice(len(points), num_points, replace=False)
            points = points[indices]
        
        return {
            "points": points.tolist(),
            "intensities": np.random.rand(len(points)).tolist()
        }
    
    def _simulate_imu(self, parameters: Dict[str, Any], noise_level: float) -> Dict[str, Any]:
        """Simulate IMU sensor data."""
        # Extract parameters with defaults
        frequency = parameters.get("frequency", 100)
        duration = parameters.get("duration", 1.0)
        
        # Calculate number of samples
        num_samples = int(frequency * duration)
        
        # Generate time array
        time = np.linspace(0, duration, num_samples)
        
        # Generate simulated accelerometer data
        accel_x = np.sin(2 * np.pi * time) * 0.5
        accel_y = np.cos(2 * np.pi * time) * 0.3
        accel_z = np.ones_like(time) * 9.81  # Gravity
        
        # Add noise
        accel_x += np.random.normal(0, noise_level, accel_x.shape)
        accel_y += np.random.normal(0, noise_level, accel_y.shape)
        accel_z += np.random.normal(0, noise_level, accel_z.shape)
        
        # Generate simulated gyroscope data
        gyro_x = np.cos(2 * np.pi * time) * 0.2
        gyro_y = np.sin(2 * np.pi * time) * 0.1
        gyro_z = np.sin(4 * np.pi * time) * 0.05
        
        # Add noise
        gyro_x += np.random.normal(0, noise_level, gyro_x.shape)
        gyro_y += np.random.normal(0, noise_level, gyro_y.shape)
        gyro_z += np.random.normal(0, noise_level, gyro_z.shape)
        
        return {
            "time": time.tolist(),
            "accelerometer": {
                "x": accel_x.tolist(),
                "y": accel_y.tolist(),
                "z": accel_z.tolist()
            },
            "gyroscope": {
                "x": gyro_x.tolist(),
                "y": gyro_y.tolist(),
                "z": gyro_z.tolist()
            }
        }
    
    def _simulate_force_sensor(self, parameters: Dict[str, Any], noise_level: float) -> Dict[str, Any]:
        """Simulate force/torque sensor data."""
        # Extract parameters with defaults
        frequency = parameters.get("frequency", 100)
        duration = parameters.get("duration", 1.0)
        
        # Calculate number of samples
        num_samples = int(frequency * duration)
        
        # Generate time array
        time = np.linspace(0, duration, num_samples)
        
        # Generate simulated force data
        force_x = np.sin(2 * np.pi * time) * 5.0
        force_y = np.cos(2 * np.pi * time) * 3.0
        force_z = np.ones_like(time) * 10.0 + np.sin(4 * np.pi * time) * 2.0
        
        # Add noise
        force_x += np.random.normal(0, noise_level * 5.0, force_x.shape)
        force_y += np.random.normal(0, noise_level * 3.0, force_y.shape)
        force_z += np.random.normal(0, noise_level * 2.0, force_z.shape)
        
        # Generate simulated torque data
        torque_x = np.cos(2 * np.pi * time) * 0.5
        torque_y = np.sin(2 * np.pi * time) * 0.3
        torque_z = np.sin(4 * np.pi * time) * 0.2
        
        # Add noise
        torque_x += np.random.normal(0, noise_level * 0.5, torque_x.shape)
        torque_y += np.random.normal(0, noise_level * 0.3, torque_y.shape)
        torque_z += np.random.normal(0, noise_level * 0.2, torque_z.shape)
        
        return {
            "time": time.tolist(),
            "force": {
                "x": force_x.tolist(),
                "y": force_y.tolist(),
                "z": force_z.tolist()
            },
            "torque": {
                "x": torque_x.tolist(),
                "y": torque_y.tolist(),
                "z": torque_z.tolist()
            }
        }
    
    def _visualize_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> str:
        """
        Generate a visualization of the sensor data.
        
        Args:
            sensor_type: Type of sensor data
            data: Sensor data to visualize
            
        Returns:
            Base64-encoded PNG image of the visualization
        """
        plt.figure(figsize=(10, 6))
        
        if sensor_type.lower() == "camera":
            if "rgb" in data:
                plt.imshow(np.array(data["rgb"]).astype(np.uint8))
                plt.title("Simulated Camera Image")
                plt.axis("off")
            elif "depth" in data:
                plt.imshow(np.array(data["depth"]), cmap="viridis")
                plt.colorbar(label="Depth (m)")
                plt.title("Simulated Depth Image")
                plt.axis("off")
        
        elif sensor_type.lower() == "lidar":
            points = np.array(data["points"])
            plt.scatter(points[:, 0], points[:, 1], s=1, c=data["intensities"], cmap="viridis")
            plt.colorbar(label="Intensity")
            plt.title("Simulated LIDAR Point Cloud (Top View)")
            plt.xlabel("X (m)")
            plt.ylabel("Y (m)")
            plt.axis("equal")
        
        elif sensor_type.lower() == "imu":
            time = np.array(data["time"])
            
            plt.subplot(2, 1, 1)
            plt.plot(time, data["accelerometer"]["x"], label="X")
            plt.plot(time, data["accelerometer"]["y"], label="Y")
            plt.plot(time, data["accelerometer"]["z"], label="Z")
            plt.title("Simulated Accelerometer Data")
            plt.xlabel("Time (s)")
            plt.ylabel("Acceleration (m/s²)")
            plt.legend()
            plt.grid(True)
            
            plt.subplot(2, 1, 2)
            plt.plot(time, data["gyroscope"]["x"], label="X")
            plt.plot(time, data["gyroscope"]["y"], label="Y")
            plt.plot(time, data["gyroscope"]["z"], label="Z")
            plt.title("Simulated Gyroscope Data")
            plt.xlabel("Time (s)")
            plt.ylabel("Angular Velocity (rad/s)")
            plt.legend()
            plt.grid(True)
            
            plt.tight_layout()
        
        elif sensor_type.lower() == "force":
            time = np.array(data["time"])
            
            plt.subplot(2, 1, 1)
            plt.plot(time, data["force"]["x"], label="X")
            plt.plot(time, data["force"]["y"], label="Y")
            plt.plot(time, data["force"]["z"], label="Z")
            plt.title("Simulated Force Data")
            plt.xlabel("Time (s)")
            plt.ylabel("Force (N)")
            plt.legend()
            plt.grid(True)
            
            plt.subplot(2, 1, 2)
            plt.plot(time, data["torque"]["x"], label="X")
            plt.plot(time, data["torque"]["y"], label="Y")
            plt.plot(time, data["torque"]["z"], label="Z")
            plt.title("Simulated Torque Data")
            plt.xlabel("Time (s)")
            plt.ylabel("Torque (Nm)")
            plt.legend()
            plt.grid(True)
            
            plt.tight_layout()
        
        # Save the figure to a BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        
        # Encode the image as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        
        return img_str
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the parameters for the tool."""
        return {
            "type": "object",
            "properties": {
                "sensor_type": {
                    "type": "string",
                    "description": "Type of sensor to simulate (camera, lidar, imu, force)",
                    "enum": ["camera", "lidar", "imu", "force"]
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the sensor simulation"
                },
                "noise_level": {
                    "type": "number",
                    "description": "Level of noise to add to the simulation (0.0 to 1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.1
                },
                "return_visualization": {
                    "type": "boolean",
                    "description": "Whether to return a visualization of the data",
                    "default": False
                }
            },
            "required": ["sensor_type", "parameters"]
        }

# Motion planning tools
class MotionPlanningTool(EmbodiedTool):
    """Tool for planning motion trajectories for embodied AI applications."""
    
    def __init__(self):
        """Initialize the motion planning tool."""
        super().__init__(
            name="plan_motion_trajectory",
            description="Plan a motion trajectory for an embodied AI system."
        )
    
    def __call__(
        self,
        start_state: Dict[str, Any],
        goal_state: Dict[str, Any],
        robot_type: str,
        obstacles: List[Dict[str, Any]] = None,
        planning_time: float = 1.0,
        smoothing: bool = True
    ) -> Dict[str, Any]:
        """
        Plan a motion trajectory from start to goal state.
        
        Args:
            start_state: Starting state of the robot
            goal_state: Goal state of the robot
            robot_type: Type of robot (arm, mobile, humanoid)
            obstacles: List of obstacles in the environment
            planning_time: Maximum planning time in seconds
            smoothing: Whether to smooth the trajectory
            
        Returns:
            Dict containing the planned trajectory and metadata
        """
        try:
            # Validate inputs
            self._validate_states(start_state, goal_state, robot_type)
            
            # Default empty obstacles list
            if obstacles is None:
                obstacles = []
            
            # Plan trajectory based on robot type
            if robot_type.lower() == "arm":
                trajectory = self._plan_arm_trajectory(start_state, goal_state, obstacles, planning_time, smoothing)
            elif robot_type.lower() == "mobile":
                trajectory = self._plan_mobile_trajectory(start_state, goal_state, obstacles, planning_time, smoothing)
            elif robot_type.lower() == "humanoid":
                trajectory = self._plan_humanoid_trajectory(start_state, goal_state, obstacles, planning_time, smoothing)
            else:
                raise ValueError(f"Unsupported robot type: {robot_type}")
            
            # Generate visualization
            visualization = self._visualize_trajectory(robot_type, trajectory, obstacles)
            
            # Prepare result
            result = {
                "trajectory": trajectory,
                "metadata": {
                    "robot_type": robot_type,
                    "planning_time": planning_time,
                    "smoothing": smoothing,
                    "num_waypoints": len(trajectory["waypoints"]),
                    "path_length": trajectory["path_length"],
                    "execution_time": trajectory["execution_time"]
                },
                "visualization": visualization
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error planning motion trajectory: {e}")
            return {"error": str(e)}
    
    def _validate_states(self, start_state: Dict[str, Any], goal_state: Dict[str, Any], robot_type: str):
        """Validate start and goal states for the given robot type."""
        if robot_type.lower() == "arm":
            required_keys = ["joint_positions"]
            for key in required_keys:
                if key not in start_state or key not in goal_state:
                    raise ValueError(f"Missing required key '{key}' in start or goal state for arm robot")
                
                if len(start_state[key]) != len(goal_state[key]):
                    raise ValueError(f"Dimension mismatch in '{key}' between start and goal states")
        
        elif robot_type.lower() == "mobile":
            required_keys = ["position", "orientation"]
            for key in required_keys:
                if key not in start_state or key not in goal_state:
                    raise ValueError(f"Missing required key '{key}' in start or goal state for mobile robot")
                
                if key == "position" and (len(start_state[key]) != 2 or len(goal_state[key]) != 2):
                    raise ValueError("Position must be a 2D coordinate [x, y] for mobile robot")
        
        elif robot_type.lower() == "humanoid":
            required_keys = ["position", "orientation", "joint_positions"]
            for key in required_keys:
                if key not in start_state or key not in goal_state:
                    raise ValueError(f"Missing required key '{key}' in start or goal state for humanoid robot")
                
                if key == "position" and (len(start_state[key]) != 3 or len(goal_state[key]) != 3):
                    raise ValueError("Position must be a 3D coordinate [x, y, z] for humanoid robot")
                
                if key == "joint_positions" and len(start_state[key]) != len(goal_state[key]):
                    raise ValueError("Dimension mismatch in joint positions between start and goal states")
    
    def _plan_arm_trajectory(
        self,
        start_state: Dict[str, Any],
        goal_state: Dict[str, Any],
        obstacles: List[Dict[str, Any]],
        planning_time: float,
        smoothing: bool
    ) -> Dict[str, Any]:
        """Plan a trajectory for a robotic arm."""
        # Extract joint positions
        start_joints = np.array(start_state["joint_positions"])
        goal_joints = np.array(goal_state["joint_positions"])
        num_joints = len(start_joints)
        
        # Simulate planning with a simple linear interpolation
        num_waypoints = 20
        waypoints = []
        
        for i in range(num_waypoints):
            t = i / (num_waypoints - 1)
            # Linear interpolation
            joint_positions = (1 - t) * start_joints + t * goal_joints
            
            # Add some randomness to simulate obstacle avoidance
            if 0.2 < t < 0.8 and obstacles:
                # Add a small detour
                detour = np.sin(t * np.pi) * 0.2 * np.random.rand(num_joints)
                joint_positions += detour
            
            waypoints.append({
                "joint_positions": joint_positions.tolist(),
                "time": t * 5.0  # Assume 5 seconds for execution
            })
        
        # Apply smoothing if requested
        if smoothing:
            # Simple moving average smoothing
            window_size = 3
            for j in range(num_joints):
                for i in range(window_size, num_waypoints - window_size):
                    smoothed_value = 0
                    for k in range(-window_size, window_size + 1):
                        smoothed_value += waypoints[i + k]["joint_positions"][j]
                    waypoints[i]["joint_positions"][j] = smoothed_value / (2 * window_size + 1)
        
        # Calculate path length (joint space)
        path_length = 0
        for i in range(1, len(waypoints)):
            prev_joints = np.array(waypoints[i-1]["joint_positions"])
            curr_joints = np.array(waypoints[i]["joint_positions"])
            path_length += np.linalg.norm(curr_joints - prev_joints)
        
        return {
            "waypoints": waypoints,
            "path_length": path_length,
            "execution_time": waypoints[-1]["time"]
        }
    
    def _plan_mobile_trajectory(
        self,
        start_state: Dict[str, Any],
        goal_state: Dict[str, Any],
        obstacles: List[Dict[str, Any]],
        planning_time: float,
        smoothing: bool
    ) -> Dict[str, Any]:
        """Plan a trajectory for a mobile robot."""
        # Extract positions and orientations
        start_pos = np.array(start_state["position"])
        goal_pos = np.array(goal_state["position"])
        start_orient = start_state["orientation"]
        goal_orient = goal_state["orientation"]
        
        # Convert obstacles to numpy arrays for easier processing
        obstacle_positions = []
        obstacle_radii = []
        for obs in obstacles:
            if "position" in obs and "radius" in obs:
                obstacle_positions.append(np.array(obs["position"]))
                obstacle_radii.append(obs["radius"])
        
        # Simulate planning with potential field approach
        num_waypoints = 30
        waypoints = []
        
        # Initial path is a straight line
        for i in range(num_waypoints):
            t = i / (num_waypoints - 1)
            # Linear interpolation for position
            position = (1 - t) * start_pos + t * goal_pos
            
            # Apply obstacle avoidance if there are obstacles
            if obstacle_positions:
                # Simple potential field approach
                repulsive_force = np.zeros(2)
                for j, obs_pos in enumerate(obstacle_positions):
                    # Vector from obstacle to robot
                    vec_to_robot = position - obs_pos[:2]
                    distance = np.linalg.norm(vec_to_robot)
                    
                    # Apply repulsive force if close to obstacle
                    if distance < obstacle_radii[j] * 2:
                        # Normalize and scale inversely with distance
                        if distance > 0:  # Avoid division by zero
                            force = vec_to_robot / distance * (1.0 / max(distance - obstacle_radii[j], 0.1))
                            repulsive_force += force
                
                # Apply repulsive force to position
                position += repulsive_force * 0.1
            
            # Linear interpolation for orientation
            orientation = start_orient + t * (goal_orient - start_orient)
            
            # Calculate velocity based on position change
            velocity = np.zeros(2)
            if i > 0:
                prev_pos = np.array(waypoints[i-1]["position"])
                velocity = (position - prev_pos) / 0.1  # Assume 0.1s between waypoints
            
            waypoints.append({
                "position": position.tolist(),
                "orientation": orientation,
                "velocity": velocity.tolist(),
                "time": t * 10.0  # Assume 10 seconds for execution
            })
        
        # Apply smoothing if requested
        if smoothing:
            # Simple moving average smoothing for position
            window_size = 2
            for i in range(window_size, num_waypoints - window_size):
                smoothed_pos = np.zeros(2)
                for k in range(-window_size, window_size + 1):
                    smoothed_pos += np.array(waypoints[i + k]["position"])
                waypoints[i]["position"] = smoothed_pos.tolist() / (2 * window_size + 1)
            
            # Recalculate velocities after smoothing
            for i in range(1, num_waypoints):
                prev_pos = np.array(waypoints[i-1]["position"])
                curr_pos = np.array(waypoints[i]["position"])
                waypoints[i]["velocity"] = ((curr_pos - prev_pos) / 0.1).tolist()
        
        # Calculate path length
        path_length = 0
        for i in range(1, len(waypoints)):
            prev_pos = np.array(waypoints[i-1]["position"])
            curr_pos = np.array(waypoints[i]["position"])
            path_length += np.linalg.norm(curr_pos - prev_pos)
        
        return {
            "waypoints": waypoints,
            "path_length": path_length,
            "execution_time": waypoints[-1]["time"]
        }
    
    def _plan_humanoid_trajectory(
        self,
        start_state: Dict[str, Any],
        goal_state: Dict[str, Any],
        obstacles: List[Dict[str, Any]],
        planning_time: float,
        smoothing: bool
    ) -> Dict[str, Any]:
        """Plan a trajectory for a humanoid robot."""
        # Extract positions, orientations, and joint positions
        start_pos = np.array(start_state["position"])
        goal_pos = np.array(goal_state["position"])
        start_orient = start_state["orientation"]
        goal_orient = goal_state["orientation"]
        start_joints = np.array(start_state["joint_positions"])
        goal_joints = np.array(goal_state["joint_positions"])
        
        # Simulate planning with a combination of mobile base planning and whole-body motion
        num_waypoints = 40
        waypoints = []
        
        for i in range(num_waypoints):
            t = i / (num_waypoints - 1)
            
            # Linear interpolation for position
            position = (1 - t) * start_pos + t * goal_pos
            
            # Add some randomness to simulate footstep planning
            if t > 0 and t < 1:
                # Add a small oscillation in the vertical direction for walking
                position[2] += 0.02 * np.sin(t * np.pi * 10)
                
                # Add a small oscillation in the lateral direction for balance
                position[1] += 0.01 * np.sin(t * np.pi * 5)
            
            # Linear interpolation for orientation
            orientation = start_orient + t * (goal_orient - start_orient)
            
            # Linear interpolation for joint positions
            joint_positions = (1 - t) * start_joints + t * goal_joints
            
            # Add some randomness to simulate natural motion
            if 0.1 < t < 0.9:
                # Add small oscillations to joints for walking motion
                joint_oscillations = 0.05 * np.sin(t * np.pi * 10 + np.arange(len(joint_positions)) * 0.5)
                joint_positions += joint_oscillations
            
            waypoints.append({
                "position": position.tolist(),
                "orientation": orientation,
                "joint_positions": joint_positions.tolist(),
                "time": t * 15.0  # Assume 15 seconds for execution
            })
        
        # Apply smoothing if requested
        if smoothing:
            # Simple moving average smoothing
            window_size = 3
            for i in range(window_size, num_waypoints - window_size):
                # Smooth position
                smoothed_pos = np.zeros(3)
                for k in range(-window_size, window_size + 1):
                    smoothed_pos += np.array(waypoints[i + k]["position"])
                waypoints[i]["position"] = smoothed_pos.tolist() / (2 * window_size + 1)
                
                # Smooth joint positions
                for j in range(len(start_joints)):
                    smoothed_joint = 0
                    for k in range(-window_size, window_size + 1):
                        smoothed_joint += waypoints[i + k]["joint_positions"][j]
                    waypoints[i]["joint_positions"][j] = smoothed_joint / (2 * window_size + 1)
        
        # Calculate path length (Cartesian space)
        path_length = 0
        for i in range(1, len(waypoints)):
            prev_pos = np.array(waypoints[i-1]["position"])
            curr_pos = np.array(waypoints[i]["position"])
            path_length += np.linalg.norm(curr_pos - prev_pos)
        
        return {
            "waypoints": waypoints,
            "path_length": path_length,
            "execution_time": waypoints[-1]["time"]
        }
    
    def _visualize_trajectory(
        self,
        robot_type: str,
        trajectory: Dict[str, Any],
        obstacles: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a visualization of the planned trajectory.
        
        Args:
            robot_type: Type of robot
            trajectory: Planned trajectory
            obstacles: List of obstacles
            
        Returns:
            Base64-encoded PNG image of the visualization
        """
        plt.figure(figsize=(10, 8))
        
        waypoints = trajectory["waypoints"]
        
        if robot_type.lower() in ["mobile", "humanoid"]:
            # Extract positions for plotting
            positions = np.array([wp["position"] for wp in waypoints])
            
            # Plot trajectory
            if robot_type.lower() == "mobile":
                plt.plot(positions[:, 0], positions[:, 1], 'b-', linewidth=2, label="Trajectory")
                plt.scatter(positions[0, 0], positions[0, 1], color='g', s=100, marker='o', label="Start")
                plt.scatter(positions[-1, 0], positions[-1, 1], color='r', s=100, marker='x', label="Goal")
                
                # Plot obstacles
                for obs in obstacles:
                    if "position" in obs and "radius" in obs:
                        circle = plt.Circle((obs["position"][0], obs["position"][1]), 
                                           obs["radius"], color='gray', alpha=0.5)
                        plt.gca().add_patch(circle)
                
                plt.title(f"Mobile Robot Trajectory ({len(waypoints)} waypoints)")
                plt.xlabel("X (m)")
                plt.ylabel("Y (m)")
                plt.axis("equal")
                plt.grid(True)
                plt.legend()
                
            elif robot_type.lower() == "humanoid":
                # 3D plot for humanoid
                ax = plt.figure().add_subplot(111, projection='3d')
                ax.plot(positions[:, 0], positions[:, 1], positions[:, 2], 'b-', linewidth=2, label="Trajectory")
                ax.scatter(positions[0, 0], positions[0, 1], positions[0, 2], color='g', s=100, marker='o', label="Start")
                ax.scatter(positions[-1, 0], positions[-1, 1], positions[-1, 2], color='r', s=100, marker='x', label="Goal")
                
                # Plot obstacles
                for obs in obstacles:
                    if "position" in obs and "radius" in obs:
                        # Create a wireframe sphere
                        u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
                        x = obs["position"][0] + obs["radius"] * np.cos(u) * np.sin(v)
                        y = obs["position"][1] + obs["radius"] * np.sin(u) * np.sin(v)
                        z = obs["position"][2] + obs["radius"] * np.cos(v)
                        ax.plot_wireframe(x, y, z, color="gray", alpha=0.3)
                
                ax.set_title(f"Humanoid Robot Trajectory ({len(waypoints)} waypoints)")
                ax.set_xlabel("X (m)")
                ax.set_ylabel("Y (m)")
                ax.set_zlabel("Z (m)")
                ax.legend()
                
        elif robot_type.lower() == "arm":
            # For arm, plot joint positions over time
            joint_positions = np.array([wp["joint_positions"] for wp in waypoints])
            times = np.array([wp["time"] for wp in waypoints])
            
            for i in range(joint_positions.shape[1]):
                plt.plot(times, joint_positions[:, i], label=f"Joint {i+1}")
            
            plt.title(f"Arm Joint Trajectories ({len(waypoints)} waypoints)")
            plt.xlabel("Time (s)")
            plt.ylabel("Joint Position (rad)")
            plt.grid(True)
            plt.legend()
        
        # Save the figure to a BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        
        # Encode the image as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        
        return img_str
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the parameters for the tool."""
        return {
            "type": "object",
            "properties": {
                "start_state": {
                    "type": "object",
                    "description": "Starting state of the robot"
                },
                "goal_state": {
                    "type": "object",
                    "description": "Goal state of the robot"
                },
                "robot_type": {
                    "type": "string",
                    "description": "Type of robot (arm, mobile, humanoid)",
                    "enum": ["arm", "mobile", "humanoid"]
                },
                "obstacles": {
                    "type": "array",
                    "description": "List of obstacles in the environment",
                    "items": {
                        "type": "object"
                    }
                },
                "planning_time": {
                    "type": "number",
                    "description": "Maximum planning time in seconds",
                    "default": 1.0
                },
                "smoothing": {
                    "type": "boolean",
                    "description": "Whether to smooth the trajectory",
                    "default": True
                }
            },
            "required": ["start_state", "goal_state", "robot_type"]
        }

# Environment interaction tools
class EnvironmentInteractionTool(EmbodiedTool):
    """Tool for interacting with simulated environments for embodied AI applications."""
    
    def __init__(self):
        """Initialize the environment interaction tool."""
        super().__init__(
            name="interact_with_environment",
            description="Interact with a simulated environment for embodied AI applications."
        )
        
        # Initialize environment state
        self._reset_environment()
    
    def __call__(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        environment_type: str = "simple",
        render: bool = True
    ) -> Dict[str, Any]:
        """
        Interact with the simulated environment.
        
        Args:
            action_type: Type of action to perform (move, grasp, release, sense)
            parameters: Parameters for the action
            environment_type: Type of environment to simulate
            render: Whether to render the environment state
            
        Returns:
            Dict containing the result of the interaction and updated environment state
        """
        try:
            # Validate inputs
            self._validate_action(action_type, parameters, environment_type)
            
            # Execute action based on type
            if action_type.lower() == "move":
                result = self._execute_move_action(parameters, environment_type)
            elif action_type.lower() == "grasp":
                result = self._execute_grasp_action(parameters, environment_type)
            elif action_type.lower() == "release":
                result = self._execute_release_action(parameters, environment_type)
            elif action_type.lower() == "sense":
                result = self._execute_sense_action(parameters, environment_type)
            elif action_type.lower() == "reset":
                result = self._reset_environment(parameters.get("scenario", "default"))
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
            
            # Generate visualization if requested
            visualization = None
            if render:
                visualization = self._render_environment(environment_type)
            
            # Prepare result
            response = {
                "success": result["success"],
                "message": result["message"],
                "environment_state": self._get_environment_state(),
                "observation": result.get("observation", None)
            }
            
            if visualization:
                response["visualization"] = visualization
                
            return response
            
        except Exception as e:
            logger.error(f"Error interacting with environment: {e}")
            return {
                "success": False,
                "message": str(e),
                "environment_state": self._get_environment_state()
            }
    
    def _validate_action(self, action_type: str, parameters: Dict[str, Any], environment_type: str):
        """Validate action parameters for the given environment type."""
        valid_action_types = ["move", "grasp", "release", "sense", "reset"]
        if action_type.lower() not in valid_action_types:
            raise ValueError(f"Invalid action type: {action_type}. Must be one of {valid_action_types}")
        
        valid_environment_types = ["simple", "tabletop", "room", "outdoor"]
        if environment_type.lower() not in valid_environment_types:
            raise ValueError(f"Invalid environment type: {environment_type}. Must be one of {valid_environment_types}")
        
        # Validate parameters based on action type
        if action_type.lower() == "move":
            if "position" not in parameters and "joint_positions" not in parameters:
                raise ValueError("Move action requires either 'position' or 'joint_positions' parameter")
                
        elif action_type.lower() == "grasp":
            if "object_id" not in parameters:
                raise ValueError("Grasp action requires 'object_id' parameter")
                
        elif action_type.lower() == "sense":
            if "sensor_type" not in parameters:
                raise ValueError("Sense action requires 'sensor_type' parameter")
    
    def _reset_environment(self, scenario: str = "default") -> Dict[str, Any]:
        """Reset the environment to a default or specified state."""
        # Initialize environment with default objects and robot state
        self.env_state = {
            "robot": {
                "position": [0.0, 0.0, 0.0],
                "orientation": 0.0,
                "gripper_state": "open",
                "holding_object": None,
                "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            },
            "objects": {
                "cube_1": {
                    "position": [0.5, 0.2, 0.0],
                    "dimensions": [0.1, 0.1, 0.1],
                    "color": "red",
                    "mass": 0.5,
                    "graspable": True
                },
                "cube_2": {
                    "position": [0.3, -0.4, 0.0],
                    "dimensions": [0.1, 0.1, 0.1],
                    "color": "blue",
                    "mass": 0.5,
                    "graspable": True
                },
                "cylinder_1": {
                    "position": [-0.2, 0.3, 0.0],
                    "dimensions": [0.1, 0.2],  # radius, height
                    "color": "green",
                    "mass": 0.7,
                    "graspable": True
                }
            },
            "obstacles": {
                "wall_1": {
                    "position": [0.0, 0.8, 0.0],
                    "dimensions": [1.5, 0.1, 0.3],
                    "color": "gray"
                },
                "wall_2": {
                    "position": [0.0, -0.8, 0.0],
                    "dimensions": [1.5, 0.1, 0.3],
                    "color": "gray"
                }
            },
            "targets": {
                "target_1": {
                    "position": [-0.5, -0.5, 0.0],
                    "dimensions": [0.15, 0.15, 0.01],
                    "color": "yellow"
                }
            }
        }
        
        # Customize environment based on scenario
        if scenario == "tabletop":
            # Add more objects for a tabletop manipulation scenario
            self.env_state["objects"]["plate_1"] = {
                "position": [0.0, 0.0, 0.0],
                "dimensions": [0.2, 0.2, 0.02],
                "color": "white",
                "mass": 0.3,
                "graspable": True
            }
            self.env_state["objects"]["cup_1"] = {
                "position": [0.2, 0.0, 0.0],
                "dimensions": [0.05, 0.1],  # radius, height
                "color": "blue",
                "mass": 0.2,
                "graspable": True
            }
            
        elif scenario == "room":
            # Add furniture and room structure
            self.env_state["obstacles"]["table"] = {
                "position": [0.0, 0.0, 0.0],
                "dimensions": [1.0, 0.6, 0.1],
                "color": "brown"
            }
            self.env_state["obstacles"]["chair"] = {
                "position": [0.0, -0.8, 0.0],
                "dimensions": [0.4, 0.4, 0.8],
                "color": "brown"
            }
            # Adjust robot position
            self.env_state["robot"]["position"] = [1.0, 0.0, 0.0]
            
        elif scenario == "outdoor":
            # Create an outdoor environment with terrain
            self.env_state["terrain"] = {
                "type": "uneven",
                "size": [10.0, 10.0],
                "height_field": "random"
            }
            self.env_state["obstacles"]["tree_1"] = {
                "position": [1.5, 1.5, 0.0],
                "dimensions": [0.3, 2.0],  # radius, height
                "color": "green"
            }
            self.env_state["obstacles"]["rock_1"] = {
                "position": [-1.0, 2.0, 0.0],
                "dimensions": [0.5, 0.3, 0.4],
                "color": "gray"
            }
            # Adjust robot position
            self.env_state["robot"]["position"] = [0.0, 0.0, 0.0]
        
        return {
            "success": True,
            "message": f"Environment reset to {scenario} scenario"
        }
    
    def _execute_move_action(self, parameters: Dict[str, Any], environment_type: str) -> Dict[str, Any]:
        """Execute a move action in the environment."""
        # Check if position or joint positions are provided
        if "position" in parameters:
            target_position = parameters["position"]
            
            # Check for collisions with obstacles
            for obstacle_id, obstacle in self.env_state["obstacles"].items():
                # Simple collision check (distance-based)
                obstacle_pos = np.array(obstacle["position"])
                target_pos = np.array(target_position)
                
                # Calculate distance (ignoring height for simplicity)
                distance_2d = np.linalg.norm(obstacle_pos[:2] - target_pos[:2])
                
                # Check if too close to obstacle
                if distance_2d < 0.3:  # Simple threshold
                    return {
                        "success": False,
                        "message": f"Move failed: Collision detected with obstacle {obstacle_id}"
                    }
            
            # Update robot position
            self.env_state["robot"]["position"] = target_position
            
            # Update orientation if provided
            if "orientation" in parameters:
                self.env_state["robot"]["orientation"] = parameters["orientation"]
                
            return {
                "success": True,
                "message": f"Robot moved to position {target_position}"
            }
            
        elif "joint_positions" in parameters:
            # Update robot joint positions
            self.env_state["robot"]["joint_positions"] = parameters["joint_positions"]
            
            return {
                "success": True,
                "message": f"Robot joints moved to {parameters['joint_positions']}"
            }
        
        return {
            "success": False,
            "message": "Move action requires either position or joint_positions"
        }
    
    def _execute_grasp_action(self, parameters: Dict[str, Any], environment_type: str) -> Dict[str, Any]:
        """Execute a grasp action in the environment."""
        object_id = parameters["object_id"]
        
        # Check if object exists
        if object_id not in self.env_state["objects"]:
            return {
                "success": False,
                "message": f"Grasp failed: Object {object_id} not found"
            }
        
        # Check if object is graspable
        if not self.env_state["objects"][object_id].get("graspable", False):
            return {
                "success": False,
                "message": f"Grasp failed: Object {object_id} is not graspable"
            }
        
        # Check if robot is already holding an object
        if self.env_state["robot"]["holding_object"] is not None:
            return {
                "success": False,
                "message": f"Grasp failed: Robot is already holding {self.env_state['robot']['holding_object']}"
            }
        
        # Check if robot is close enough to the object
        robot_pos = np.array(self.env_state["robot"]["position"])
        object_pos = np.array(self.env_state["objects"][object_id]["position"])
        distance = np.linalg.norm(robot_pos - object_pos)
        
        if distance > 0.5:  # Simple threshold
            return {
                "success": False,
                "message": f"Grasp failed: Object {object_id} is too far (distance: {distance:.2f}m)"
            }
        
        # Execute grasp
        self.env_state["robot"]["gripper_state"] = "closed"
        self.env_state["robot"]["holding_object"] = object_id
        
        # Update object position to be at robot's position
        self.env_state["objects"][object_id]["position"] = self.env_state["robot"]["position"]
        
        return {
            "success": True,
            "message": f"Successfully grasped object {object_id}"
        }
    
    def _execute_release_action(self, parameters: Dict[str, Any], environment_type: str) -> Dict[str, Any]:
        """Execute a release action in the environment."""
        # Check if robot is holding an object
        if self.env_state["robot"]["holding_object"] is None:
            return {
                "success": False,
                "message": "Release failed: Robot is not holding any object"
            }
        
        # Get the object being held
        object_id = self.env_state["robot"]["holding_object"]
        
        # Release the object
        self.env_state["robot"]["gripper_state"] = "open"
        self.env_state["robot"]["holding_object"] = None
        
        # If release position is specified, use it; otherwise use robot's current position
        if "position" in parameters:
            self.env_state["objects"][object_id]["position"] = parameters["position"]
        else:
            # Place slightly in front of the robot
            robot_pos = np.array(self.env_state["robot"]["position"])
            robot_orient = self.env_state["robot"]["orientation"]
            
            # Calculate position in front of robot based on orientation
            offset_x = 0.2 * np.cos(robot_orient)
            offset_y = 0.2 * np.sin(robot_orient)
            release_pos = robot_pos.copy()
            release_pos[0] += offset_x
            release_pos[1] += offset_y
            
            self.env_state["objects"][object_id]["position"] = release_pos.tolist()
        
        return {
            "success": True,
            "message": f"Successfully released object {object_id}"
        }
    
    def _execute_sense_action(self, parameters: Dict[str, Any], environment_type: str) -> Dict[str, Any]:
        """Execute a sense action in the environment."""
        sensor_type = parameters["sensor_type"]
        
        if sensor_type.lower() == "camera":
            # Simulate camera observation
            observation = self._simulate_camera_observation(parameters.get("resolution", [640, 480]))
            return {
                "success": True,
                "message": "Camera observation captured",
                "observation": observation
            }
            
        elif sensor_type.lower() == "lidar":
            # Simulate lidar observation
            observation = self._simulate_lidar_observation(parameters.get("num_rays", 360))
            return {
                "success": True,
                "message": "Lidar scan completed",
                "observation": observation
            }
            
        elif sensor_type.lower() == "touch":
            # Simulate touch sensor
            observation = self._simulate_touch_observation()
            return {
                "success": True,
                "message": "Touch sensing completed",
                "observation": observation
            }
            
        else:
            return {
                "success": False,
                "message": f"Unsupported sensor type: {sensor_type}"
            }
    
    def _simulate_camera_observation(self, resolution: List[int]) -> Dict[str, Any]:
        """Simulate a camera observation."""
        # For simplicity, return a list of visible objects with their properties
        robot_pos = np.array(self.env_state["robot"]["position"])
        
        visible_objects = {}
        for obj_id, obj in self.env_state["objects"].items():
            obj_pos = np.array(obj["position"])
            distance = np.linalg.norm(robot_pos - obj_pos)
            
            # Check if object is within field of view (simple distance check)
            if distance < 2.0:  # Assume 2m visibility range
                visible_objects[obj_id] = {
                    "position": obj["position"],
                    "color": obj["color"],
                    "distance": float(distance),
                    "dimensions": obj["dimensions"]
                }
        
        return {
            "visible_objects": visible_objects,
            "resolution": resolution
        }
    
    def _simulate_lidar_observation(self, num_rays: int) -> Dict[str, Any]:
        """Simulate a lidar observation."""
        robot_pos = np.array(self.env_state["robot"]["position"])
        robot_orient = self.env_state["robot"]["orientation"]
        
        # Generate lidar rays
        angles = np.linspace(0, 2 * np.pi, num_rays, endpoint=False)
        ranges = np.ones(num_rays) * 5.0  # Default range of 5m
        
        # Check intersections with obstacles
        for obstacle_id, obstacle in self.env_state["obstacles"].items():
            obstacle_pos = np.array(obstacle["position"][:2])  # 2D position
            
            # Simple rectangular obstacle model
            if "dimensions" in obstacle:
                width = obstacle["dimensions"][0] / 2
                depth = obstacle["dimensions"][1] / 2
                
                # Check each ray for intersection
                for i, angle in enumerate(angles):
                    # Ray direction
                    ray_dir = np.array([np.cos(angle + robot_orient), np.sin(angle + robot_orient)])
                    
                    # Vector from robot to obstacle
                    to_obstacle = obstacle_pos - robot_pos[:2]
                    
                    # Project onto ray direction
                    proj_dist = np.dot(to_obstacle, ray_dir)
                    
                    # Only consider obstacles in front of the ray
                    if proj_dist > 0:
                        # Distance from ray to obstacle center
                        lateral_dist = np.linalg.norm(to_obstacle - proj_dist * ray_dir)
                        
                        # Check if ray intersects obstacle (simple approximation)
                        if lateral_dist < max(width, depth) and proj_dist < ranges[i]:
                            ranges[i] = proj_dist
        
        return {
            "ranges": ranges.tolist(),
            "angles": angles.tolist(),
            "min_range": float(np.min(ranges)),
            "max_range": float(np.max(ranges))
        }
    
    def _simulate_touch_observation(self) -> Dict[str, Any]:
        """Simulate a touch sensor observation."""
        # Check if the robot is in contact with any object
        contact = False
        contact_object = None
        contact_force = 0.0
        
        # If gripper is closed and holding an object, there's contact
        if self.env_state["robot"]["gripper_state"] == "closed" and self.env_state["robot"]["holding_object"] is not None:
            contact = True
            contact_object = self.env_state["robot"]["holding_object"]
            contact_force = self.env_state["objects"][contact_object].get("mass", 0.5) * 9.81  # F = m*g
        
        return {
            "contact": contact,
            "contact_object": contact_object,
            "contact_force": contact_force
        }
    
    def _get_environment_state(self) -> Dict[str, Any]:
        """Get the current state of the environment."""
        return self.env_state
    
    def _render_environment(self, environment_type: str) -> str:
        """
        Render the current state of the environment.
        
        Args:
            environment_type: Type of environment
            
        Returns:
            Base64-encoded PNG image of the environment
        """
        # Create figure based on environment type
        if environment_type.lower() in ["simple", "tabletop"]:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Set limits
            ax.set_xlim(-2, 2)
            ax.set_ylim(-2, 2)
            
            # Draw robot
            robot_pos = self.env_state["robot"]["position"]
            robot_orient = self.env_state["robot"]["orientation"]
            
            # Draw robot body
            robot_circle = plt.Circle((robot_pos[0], robot_pos[1]), 0.2, color='blue', alpha=0.7)
            ax.add_patch(robot_circle)
            
            # Draw robot direction
            direction_x = 0.3 * np.cos(robot_orient)
            direction_y = 0.3 * np.sin(robot_orient)
            ax.arrow(robot_pos[0], robot_pos[1], direction_x, direction_y, 
                    head_width=0.1, head_length=0.1, fc='blue', ec='blue')
            
            # Draw objects
            for obj_id, obj in self.env_state["objects"].items():
                obj_pos = obj["position"]
                
                if len(obj["dimensions"]) == 3:  # Cube or box
                    width, depth = obj["dimensions"][0], obj["dimensions"][1]
                    rect = plt.Rectangle((obj_pos[0] - width/2, obj_pos[1] - depth/2), 
                                        width, depth, color=obj["color"], alpha=0.7)
                    ax.add_patch(rect)
                else:  # Cylinder
                    radius = obj["dimensions"][0]
                    circle = plt.Circle((obj_pos[0], obj_pos[1]), radius, color=obj["color"], alpha=0.7)
                    ax.add_patch(circle)
                
                # Add text label
                ax.text(obj_pos[0], obj_pos[1], obj_id, fontsize=8, 
                       ha='center', va='center', color='black')
            
            # Draw obstacles
            for obs_id, obs in self.env_state["obstacles"].items():
                obs_pos = obs["position"]
                
                if len(obs["dimensions"]) == 3:  # Box
                    width, depth = obs["dimensions"][0], obs["dimensions"][1]
                    rect = plt.Rectangle((obs_pos[0] - width/2, obs_pos[1] - depth/2), 
                                        width, depth, color=obs["color"], alpha=0.5)
                    ax.add_patch(rect)
                else:  # Cylinder
                    radius = obs["dimensions"][0]
                    circle = plt.Circle((obs_pos[0], obs_pos[1]), radius, color=obs["color"], alpha=0.5)
                    ax.add_patch(circle)
            
            # Draw targets
            for target_id, target in self.env_state.get("targets", {}).items():
                target_pos = target["position"]
                width, depth = target["dimensions"][0], target["dimensions"][1]
                rect = plt.Rectangle((target_pos[0] - width/2, target_pos[1] - depth/2), 
                                    width, depth, color=target["color"], alpha=0.3)
                ax.add_patch(rect)
                
                # Add text label
                ax.text(target_pos[0], target_pos[1], target_id, fontsize=8, 
                       ha='center', va='center', color='black')
            
            # Add status text
            status_text = f"Robot: {robot_pos}\n"
            status_text += f"Gripper: {self.env_state['robot']['gripper_state']}\n"
            if self.env_state['robot']['holding_object']:
                status_text += f"Holding: {self.env_state['robot']['holding_object']}"
            
            ax.text(1.5, 1.5, status_text, fontsize=10, 
                   bbox=dict(facecolor='white', alpha=0.7))
            
            ax.set_title(f"{environment_type.capitalize()} Environment")
            ax.set_xlabel("X (m)")
            ax.set_ylabel("Y (m)")
            ax.grid(True)
            ax.set_aspect('equal')
            
        elif environment_type.lower() in ["room", "outdoor"]:
            # 3D rendering for more complex environments
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # Draw robot
            robot_pos = self.env_state["robot"]["position"]
            ax.scatter([robot_pos[0]], [robot_pos[1]], [robot_pos[2]], 
                      color='blue', s=200, marker='o', label='Robot')
            
            # Draw objects
            for obj_id, obj in self.env_state["objects"].items():
                obj_pos = obj["position"]
                ax.scatter([obj_pos[0]], [obj_pos[1]], [obj_pos[2]], 
                          color=obj["color"], s=100, marker='s', label=obj_id)
            
            # Draw obstacles
            for obs_id, obs in self.env_state["obstacles"].items():
                obs_pos = obs["position"]
                
                if len(obs["dimensions"]) == 3:  # Box
                    width, depth, height = obs["dimensions"]
                    x, y, z = obs_pos
                    
                    # Create wireframe box
                    xx, yy = np.meshgrid([x-width/2, x+width/2], [y-depth/2, y+depth/2])
                    z1 = np.ones_like(xx) * (z - height/2)
                    z2 = np.ones_like(xx) * (z + height/2)
                    
                    ax.plot_wireframe(xx, yy, z1, color=obs["color"], alpha=0.5)
                    ax.plot_wireframe(xx, yy, z2, color=obs["color"], alpha=0.5)
                    
                    for i in range(2):
                        for j in range(2):
                            ax.plot([xx[i,j], xx[i,j]], [yy[i,j], yy[i,j]], 
                                   [z1[i,j], z2[i,j]], color=obs["color"], alpha=0.5)
                
                elif len(obs["dimensions"]) == 2:  # Cylinder
                    radius, height = obs["dimensions"]
                    x, y, z = obs_pos
                    
                    # Create cylinder
                    theta = np.linspace(0, 2*np.pi, 20)
                    x_circle = x + radius * np.cos(theta)
                    y_circle = y + radius * np.sin(theta)
                    z_bottom = np.ones_like(theta) * (z - height/2)
                    z_top = np.ones_like(theta) * (z + height/2)
                    
                    ax.plot(x_circle, y_circle, z_bottom, color=obs["color"], alpha=0.5)
                    ax.plot(x_circle, y_circle, z_top, color=obs["color"], alpha=0.5)
            
            # Set labels and title
            ax.set_title(f"{environment_type.capitalize()} Environment")
            ax.set_xlabel("X (m)")
            ax.set_ylabel("Y (m)")
            ax.set_zlabel("Z (m)")
            ax.set_xlim(-3, 3)
            ax.set_ylim(-3, 3)
            ax.set_zlim(0, 3)
            
            # Add legend
            ax.legend()
        
        # Save the figure to a BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        
        # Encode the image as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        
        return img_str
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the parameters for the tool."""
        return {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "description": "Type of action to perform",
                    "enum": ["move", "grasp", "release", "sense", "reset"]
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the action"
                },
                "environment_type": {
                    "type": "string",
                    "description": "Type of environment to simulate",
                    "enum": ["simple", "tabletop", "room", "outdoor"],
                    "default": "simple"
                },
                "render": {
                    "type": "boolean",
                    "description": "Whether to render the environment state",
                    "default": True
                }
            },
            "required": ["action_type", "parameters"]
        }

# Task planning tools
class TaskPlanningTool(EmbodiedTool):
    """Tool for planning and organizing tasks for embodied AI development."""
    
    def __init__(self):
        """Initialize the task planning tool."""
        super().__init__(
            name="plan_research_tasks",
            description="Plan and organize research tasks for embodied AI development."
        )
    
    def __call__(
        self,
        research_topic: str,
        scope: List[str] = None,
        time_constraint: str = "1 week",
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Plan research tasks for a given topic.
        
        Args:
            research_topic: The main research topic
            scope: List of specific areas to focus on
            time_constraint: Time available for the research
            output_format: Format for the output (markdown, json)
            
        Returns:
            Dict containing the research plan
        """
        try:
            # Default scope if not provided
            if scope is None:
                scope = [
                    "Current state of technology",
                    "Key players and products",
                    "Technical approaches",
                    "Market opportunities"
                ]
            
            # Generate research plan
            research_plan = self._generate_research_plan(research_topic, scope, time_constraint)
            
            # Format the output
            if output_format.lower() == "markdown":
                formatted_output = self._format_as_markdown(research_plan)
            elif output_format.lower() == "json":
                formatted_output = research_plan
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # Prepare result
            result = {
                "research_topic": research_topic,
                "scope": scope,
                "time_constraint": time_constraint,
                "research_plan": research_plan,
                "formatted_output": formatted_output
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error planning research tasks: {e}")
            return {"error": str(e)}
    
    def _generate_research_plan(
        self,
        research_topic: str,
        scope: List[str],
        time_constraint: str
    ) -> Dict[str, Any]:
        """Generate a research plan for the given topic and scope."""
        # Parse time constraint
        days_available = self._parse_time_constraint(time_constraint)
        
        # Calculate task allocation based on scope and time
        task_allocation = self._allocate_tasks(scope, days_available)
        
        # Generate phases of research
        phases = [
            {
                "name": "Initial Research",
                "description": "Gather preliminary information and define research questions",
                "duration": "20% of total time",
                "tasks": [
                    {
                        "name": "Define research questions",
                        "description": "Clearly articulate the specific questions to be answered",
                        "estimated_time": "0.5 days"
                    },
                    {
                        "name": "Identify key sources",
                        "description": "Identify authoritative sources for information",
                        "estimated_time": "0.5 days"
                    },
                    {
                        "name": "Create research framework",
                        "description": "Develop a structured approach to organize findings",
                        "estimated_time": "1 day"
                    }
                ]
            },
            {
                "name": "Deep Dive",
                "description": "Conduct in-depth research on each area of scope",
                "duration": "50% of total time",
                "tasks": []
            },
            {
                "name": "Analysis",
                "description": "Analyze findings and identify patterns, trends, and insights",
                "duration": "20% of total time",
                "tasks": [
                    {
                        "name": "Synthesize findings",
                        "description": "Combine information from different sources into coherent insights",
                        "estimated_time": "1 day"
                    },
                    {
                        "name": "Identify trends and patterns",
                        "description": "Recognize emerging trends and patterns in the research",
                        "estimated_time": "1 day"
                    }
                ]
            },
            {
                "name": "Report Creation",
                "description": "Create a comprehensive research report",
                "duration": "10% of total time",
                "tasks": [
                    {
                        "name": "Draft report",
                        "description": "Write the initial draft of the research report",
                        "estimated_time": "1 day"
                    },
                    {
                        "name": "Review and refine",
                        "description": "Review the report for accuracy, clarity, and completeness",
                        "estimated_time": "0.5 days"
                    },
                    {
                        "name": "Finalize report",
                        "description": "Incorporate feedback and finalize the report",
                        "estimated_time": "0.5 days"
                    }
                ]
            }
        ]
        
        # Add scope-specific tasks to the Deep Dive phase
        for area in scope:
            task = {
                "name": f"Research {area}",
                "description": f"Conduct in-depth research on {area}",
                "estimated_time": f"{task_allocation[area]} days"
            }
            phases[1]["tasks"].append(task)
        
        # Calculate timeline
        timeline = self._calculate_timeline(phases, days_available)
        
        # Generate deliverables
        deliverables = [
            {
                "name": "Research Plan",
                "description": "Detailed plan outlining the research approach",
                "format": "Document",
                "due": timeline[0]["end_date"]
            },
            {
                "name": "Preliminary Findings",
                "description": "Initial findings from the research",
                "format": "Presentation",
                "due": timeline[1]["end_date"]
            },
            {
                "name": "Research Report",
                "description": "Comprehensive report on the research topic",
                "format": "Document",
                "due": timeline[3]["end_date"]
            }
        ]
        
        # Generate research methods
        research_methods = [
            {
                "name": "Literature Review",
                "description": "Review of academic and industry publications"
            },
            {
                "name": "Market Analysis",
                "description": "Analysis of market trends, players, and opportunities"
            },
            {
                "name": "Technology Assessment",
                "description": "Evaluation of current and emerging technologies"
            },
            {
                "name": "Competitive Analysis",
                "description": "Analysis of competitors and their offerings"
            }
        ]
        
        return {
            "research_topic": research_topic,
            "scope": scope,
            "time_constraint": time_constraint,
            "days_available": days_available,
            "phases": phases,
            "timeline": timeline,
            "deliverables": deliverables,
            "research_methods": research_methods
        }
    
    def _parse_time_constraint(self, time_constraint: str) -> int:
        """Parse the time constraint string into number of days."""
        time_constraint = time_constraint.lower()
        
        if "day" in time_constraint:
            days = int(time_constraint.split()[0])
        elif "week" in time_constraint:
            days = int(time_constraint.split()[0]) * 5  # Assuming 5 working days per week
        elif "month" in time_constraint:
            days = int(time_constraint.split()[0]) * 20  # Assuming 20 working days per month
        else:
            # Default to 5 days if format is not recognized
            days = 5
        
        return days
    
    def _allocate_tasks(self, scope: List[str], days_available: int) -> Dict[str, float]:
        """Allocate time for each scope area based on available days."""
        # Allocate 50% of time to deep dive, divided among scope areas
        deep_dive_days = days_available * 0.5
        days_per_area = deep_dive_days / len(scope)
        
        allocation = {}
        for area in scope:
            allocation[area] = round(days_per_area, 1)
        
        return allocation
    
    def _calculate_timeline(self, phases: List[Dict[str, Any]], days_available: int) -> List[Dict[str, Any]]:
        """Calculate the timeline for each phase based on available days."""
        timeline = []
        current_day = 0
        
        for phase in phases:
            # Extract percentage from duration (e.g., "20% of total time")
            percentage = float(phase["duration"].split("%")[0]) / 100
            phase_days = round(days_available * percentage)
            
            start_day = current_day
            end_day = current_day + phase_days
            
            timeline_entry = {
                "phase": phase["name"],
                "start_day": start_day,
                "end_day": end_day,
                "duration_days": phase_days,
                "start_date": f"Day {start_day + 1}",
                "end_date": f"Day {end_day}"
            }
            
            timeline.append(timeline_entry)
            current_day = end_day
        
        return timeline
    
    def _format_as_markdown(self, research_plan: Dict[str, Any]) -> str:
        """Format the research plan as a markdown document."""
        md = f"# Research Plan: {research_plan['research_topic']}\n\n"
        
        # Scope
        md += "## Scope\n\n"
        for area in research_plan["scope"]:
            md += f"- {area}\n"
        md += "\n"
        
        # Timeline
        md += "## Timeline\n\n"
        md += f"Total time available: {research_plan['time_constraint']} ({research_plan['days_available']} working days)\n\n"
        
        md += "| Phase | Start | End | Duration |\n"
        md += "|-------|-------|-----|----------|\n"
        for phase in research_plan["timeline"]:
            md += f"| {phase['phase']} | {phase['start_date']} | {phase['end_date']} | {phase['duration_days']} days |\n"
        md += "\n"
        
        # Phases and Tasks
        md += "## Research Phases and Tasks\n\n"
        for phase in research_plan["phases"]:
            md += f"### {phase['name']}\n\n"
            md += f"{phase['description']}\n\n"
            md += "| Task | Description | Estimated Time |\n"
            md += "|------|-------------|---------------|\n"
            for task in phase["tasks"]:
                md += f"| {task['name']} | {task['description']} | {task['estimated_time']} |\n"
            md += "\n"
        
        # Deliverables
        md += "## Deliverables\n\n"
        md += "| Deliverable | Description | Format | Due |\n"
        md += "|------------|-------------|--------|-----|\n"
        for deliverable in research_plan["deliverables"]:
            md += f"| {deliverable['name']} | {deliverable['description']} | {deliverable['format']} | {deliverable['due']} |\n"
        md += "\n"
        
        # Research Methods
        md += "## Research Methods\n\n"
        for method in research_plan["research_methods"]:
            md += f"### {method['name']}\n\n"
            md += f"{method['description']}\n\n"
        
        return md
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the parameters for the tool."""
        return {
            "type": "object",
            "properties": {
                "research_topic": {
                    "type": "string",
                    "description": "The main research topic"
                },
                "scope": {
                    "type": "array",
                    "description": "List of specific areas to focus on",
                    "items": {
                        "type": "string"
                    }
                },
                "time_constraint": {
                    "type": "string",
                    "description": "Time available for the research (e.g., '1 week', '3 days')",
                    "default": "1 week"
                },
                "output_format": {
                    "type": "string",
                    "description": "Format for the output",
                    "enum": ["markdown", "json"],
                    "default": "markdown"
                }
            },
            "required": ["research_topic"]
        } 

# Web research tools
class WebResearchTool(EmbodiedTool):
    """Tool for conducting web research on embodied AI topics."""
    
    def __init__(self):
        """Initialize the web research tool."""
        super().__init__(
            name="conduct_web_research",
            description="Conduct web research on embodied AI topics and gather information."
        )
    
    def __call__(
        self,
        query: str,
        num_results: int = 5,
        include_snippets: bool = True,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Conduct web research on a given query.
        
        Args:
            query: The search query
            num_results: Number of results to return
            include_snippets: Whether to include text snippets from the results
            focus_areas: Specific areas to focus the research on
            
        Returns:
            Dict containing the research results
        """
        try:
            # Validate inputs
            if num_results <= 0:
                raise ValueError("Number of results must be positive")
            
            # Default focus areas if not provided
            if focus_areas is None:
                focus_areas = ["technology", "applications", "companies", "research"]
            
            # Simulate web search results
            search_results = self._simulate_search_results(query, num_results, focus_areas)
            
            # Extract snippets if requested
            if include_snippets:
                for result in search_results:
                    result["snippet"] = self._generate_snippet(result["title"], result["url"], query)
            
            # Summarize the results
            summary = self._summarize_results(search_results, query)
            
            # Prepare result
            result = {
                "query": query,
                "num_results": len(search_results),
                "focus_areas": focus_areas,
                "results": search_results,
                "summary": summary
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error conducting web research: {e}")
            return {"error": str(e)}
    
    def _simulate_search_results(
        self,
        query: str,
        num_results: int,
        focus_areas: List[str]
    ) -> List[Dict[str, Any]]:
        """Simulate web search results for the given query."""
        # Define a set of simulated results for embodied AI topics
        simulated_results = [
            # Technology focused results
            {
                "title": "Advances in Embodied AI: A Comprehensive Survey",
                "url": "https://example.com/embodied-ai-survey",
                "source": "Journal of Artificial Intelligence Research",
                "date": "2023-05-15",
                "focus": "technology"
            },
            {
                "title": "Embodied Intelligence: Bridging Perception and Action",
                "url": "https://example.com/embodied-intelligence",
                "source": "MIT Technology Review",
                "date": "2023-07-22",
                "focus": "technology"
            },
            {
                "title": "Multi-Modal Learning for Embodied AI Systems",
                "url": "https://example.com/multi-modal-learning",
                "source": "Conference on Computer Vision and Pattern Recognition",
                "date": "2023-06-10",
                "focus": "technology"
            },
            
            # Applications focused results
            {
                "title": "Embodied AI in Healthcare: Current Applications and Future Directions",
                "url": "https://example.com/embodied-ai-healthcare",
                "source": "Journal of Medical AI",
                "date": "2023-04-05",
                "focus": "applications"
            },
            {
                "title": "Household Robots: Embodied AI for Everyday Tasks",
                "url": "https://example.com/household-robots",
                "source": "Consumer Technology Association",
                "date": "2023-08-12",
                "focus": "applications"
            },
            {
                "title": "Industrial Applications of Embodied AI Systems",
                "url": "https://example.com/industrial-embodied-ai",
                "source": "Industry 4.0 Magazine",
                "date": "2023-03-30",
                "focus": "applications"
            },
            
            # Companies focused results
            {
                "title": "Top 10 Companies Leading the Embodied AI Revolution",
                "url": "https://example.com/top-embodied-ai-companies",
                "source": "Forbes Technology",
                "date": "2023-09-01",
                "focus": "companies"
            },
            {
                "title": "Boston Dynamics Unveils New Embodied AI Platform",
                "url": "https://example.com/boston-dynamics-platform",
                "source": "TechCrunch",
                "date": "2023-07-15",
                "focus": "companies"
            },
            {
                "title": "Startup Ecosystem in Embodied AI: Funding and Trends",
                "url": "https://example.com/embodied-ai-startups",
                "source": "Venture Beat",
                "date": "2023-08-20",
                "focus": "companies"
            },
            
            # Research focused results
            {
                "title": "Reinforcement Learning for Embodied AI: A Research Perspective",
                "url": "https://example.com/rl-embodied-ai",
                "source": "arXiv",
                "date": "2023-06-28",
                "focus": "research"
            },
            {
                "title": "Benchmarking Embodied AI Systems: Challenges and Opportunities",
                "url": "https://example.com/benchmarking-embodied-ai",
                "source": "Nature Machine Intelligence",
                "date": "2023-05-10",
                "focus": "research"
            },
            {
                "title": "Embodied AI Research at Stanford: Annual Report",
                "url": "https://example.com/stanford-embodied-ai",
                "source": "Stanford AI Lab",
                "date": "2023-04-15",
                "focus": "research"
            }
        ]
        
        # Filter results based on focus areas
        filtered_results = [r for r in simulated_results if r["focus"] in focus_areas]
        
        # Sort by relevance (simulated by matching terms in the title with the query)
        query_terms = set(query.lower().split())
        for result in filtered_results:
            title_terms = set(result["title"].lower().split())
            result["relevance"] = len(query_terms.intersection(title_terms))
        
        filtered_results.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Return the requested number of results
        return filtered_results[:num_results]
    
    def _generate_snippet(self, title: str, url: str, query: str) -> str:
        """Generate a text snippet for a search result."""
        # Generate a simulated snippet based on the title and query
        query_terms = query.lower().split()
        
        snippets = {
            "Advances in Embodied AI: A Comprehensive Survey": 
                "This comprehensive survey examines recent advances in embodied AI, focusing on perception, "
                "action, and learning. The paper discusses key algorithms, architectures, and benchmarks "
                "that have driven progress in the field.",
                
            "Embodied Intelligence: Bridging Perception and Action":
                "Embodied intelligence represents a paradigm shift in AI research, emphasizing the importance "
                "of physical interaction with the environment. This article explores how embodied AI systems "
                "integrate perception and action to solve complex tasks.",
                
            "Multi-Modal Learning for Embodied AI Systems":
                "Multi-modal learning enables embodied AI systems to process and integrate information from "
                "different sensory modalities. This paper presents a novel architecture that combines visual, "
                "auditory, and tactile inputs for improved performance on navigation and manipulation tasks.",
                
            "Embodied AI in Healthcare: Current Applications and Future Directions":
                "Embodied AI is transforming healthcare through applications in surgical assistance, "
                "rehabilitation robotics, and patient care. This review examines current implementations "
                "and discusses ethical considerations and future directions.",
                
            "Household Robots: Embodied AI for Everyday Tasks":
                "The latest generation of household robots leverages embodied AI to perform everyday tasks "
                "with unprecedented flexibility and reliability. This article showcases recent products and "
                "discusses technical challenges in developing robots for unstructured home environments.",
                
            "Industrial Applications of Embodied AI Systems":
                "Embodied AI systems are revolutionizing industrial automation by enabling robots to adapt "
                "to changing conditions and learn new tasks. This report highlights case studies from "
                "manufacturing, logistics, and quality control applications.",
                
            "Top 10 Companies Leading the Embodied AI Revolution":
                "This article profiles the top 10 companies at the forefront of embodied AI development, "
                "including established players and promising startups. Each company's technology, market "
                "strategy, and competitive advantages are analyzed.",
                
            "Boston Dynamics Unveils New Embodied AI Platform":
                "Boston Dynamics has announced a new software platform that makes its advanced embodied AI "
                "capabilities accessible to developers. The platform includes tools for perception, navigation, "
                "and manipulation that can be deployed across different robot hardware.",
                
            "Startup Ecosystem in Embodied AI: Funding and Trends":
                "Investment in embodied AI startups has reached record levels, with over $2 billion in "
                "funding in the past year alone. This report analyzes funding trends, key investors, and "
                "emerging application areas that are attracting capital.",
                
            "Reinforcement Learning for Embodied AI: A Research Perspective":
                "This paper examines how reinforcement learning algorithms can be applied to embodied AI "
                "challenges. The authors present a framework for sample-efficient learning of complex "
                "behaviors through a combination of simulation and real-world training.",
                
            "Benchmarking Embodied AI Systems: Challenges and Opportunities":
                "Standardized benchmarks are essential for measuring progress in embodied AI research. "
                "This article discusses existing benchmarks, their limitations, and proposes new metrics "
                "that better capture the capabilities of embodied systems.",
                
            "Embodied AI Research at Stanford: Annual Report":
                "Stanford's AI Lab presents its annual report on embodied AI research, highlighting "
                "breakthroughs in robot learning, human-robot interaction, and simulation environments. "
                "The report includes demonstrations of robots performing complex manipulation and "
                "navigation tasks."
        }
        
        # Return the predefined snippet if available, otherwise generate a generic one
        if title in snippets:
            return snippets[title]
        else:
            return f"This result discusses {query} in the context of embodied AI applications and technologies. Click the link to learn more about the latest developments in this field."
    
    def _summarize_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Generate a summary of the search results."""
        # Count results by focus area
        focus_counts = {}
        for result in results:
            focus = result["focus"]
            focus_counts[focus] = focus_counts.get(focus, 0) + 1
        
        # Generate summary
        summary = f"Found {len(results)} results for query: '{query}'\n\n"
        
        # Add breakdown by focus area
        summary += "Results by focus area:\n"
        for focus, count in focus_counts.items():
            summary += f"- {focus.capitalize()}: {count} results\n"
        
        # Add recent trends based on dates
        dates = [result["date"] for result in results]
        most_recent = max(dates) if dates else "N/A"
        summary += f"\nMost recent result: {most_recent}\n"
        
        # Add top sources
        sources = [result["source"] for result in results]
        source_counts = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        summary += "\nTop sources:\n"
        for source, count in top_sources:
            summary += f"- {source}: {count} results\n"
        
        return summary
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the parameters for the tool."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                },
                "include_snippets": {
                    "type": "boolean",
                    "description": "Whether to include text snippets from the results",
                    "default": True
                },
                "focus_areas": {
                    "type": "array",
                    "description": "Specific areas to focus the research on",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["query"]
        }