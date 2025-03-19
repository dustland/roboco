"""
Genesis Integration Tool for Roboco Robotics
This module provides essential task handling capabilities using Genesis physics engine.
"""

from typing import Dict, List, Optional, Union, Any
import numpy as np
from fastapi import HTTPException

try:
    import genesis  # Genesis physics engine import
    GENESIS_AVAILABLE = True
except ImportError:
    GENESIS_AVAILABLE = False


class GenesisTool:
    """A tool for interacting with the Genesis physics engine."""
    
    def __init__(self):
        """Initialize Genesis physics engine and simulation environment."""
        if not GENESIS_AVAILABLE:
            raise ImportError(
                "Genesis physics engine is not available. "
                "Please install it using: pip install genesis-embodied-ai"
            )
        self.sim = genesis.Simulation()
        self.scene = None
        self.robots: Dict[str, Any] = {}
        self.objects: Dict[str, Any] = {}
        
    async def create_scene(self, scene_description: str) -> bool:
        """
        Create a 3D scene based on natural language description.
        
        Args:
            scene_description: Natural language description of the scene
            
        Returns:
            bool: Success status of scene creation
            
        Raises:
            HTTPException: If scene creation fails
        """
        try:
            self.scene = await self.sim.create_scene(scene_description)
            return True
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating scene: {str(e)}"
            )
            
    async def add_robot(
        self, 
        robot_type: str, 
        position: List[float], 
        configuration: Optional[Dict] = None
    ) -> str:
        """
        Add a robot to the scene.
        
        Args:
            robot_type: Type of robot (e.g., "franka", "unitree_go2", "unitree_h1")
            position: [x, y, z] position in world coordinates
            configuration: Optional robot-specific configuration
            
        Returns:
            str: Robot ID if successful
            
        Raises:
            HTTPException: If robot addition fails
        """
        try:
            robot_id = await self.sim.add_robot(robot_type, position, 
                                              configuration)
            self.robots[robot_id] = await self.sim.get_robot(robot_id)
            return robot_id
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error adding robot: {str(e)}"
            )
            
    async def add_object(
        self, 
        object_type: str, 
        position: List[float], 
        properties: Optional[Dict] = None
    ) -> str:
        """
        Add an object to the scene.
        
        Args:
            object_type: Type of object (e.g., "box", "sphere", 
                        "articulated_object")
            position: [x, y, z] position in world coordinates
            properties: Optional object-specific properties
            
        Returns:
            str: Object ID if successful
            
        Raises:
            HTTPException: If object addition fails
        """
        try:
            object_id = await self.sim.add_object(object_type, position, 
                                                properties)
            self.objects[object_id] = await self.sim.get_object(object_id)
            return object_id
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error adding object: {str(e)}"
            )
            
    async def generate_motion(
        self, 
        robot_id: str, 
        task_description: str
    ) -> bool:
        """
        Generate motion for a robot based on task description.
        
        Args:
            robot_id: ID of the robot to control
            task_description: Natural language description of the task
            
        Returns:
            bool: Success status of motion generation
            
        Raises:
            HTTPException: If motion generation fails
        """
        try:
            if robot_id not in self.robots:
                raise ValueError(f"Robot {robot_id} not found")
            
            motion = await self.sim.generate_motion(
                robot=self.robots[robot_id],
                task=task_description
            )
            return await self.sim.execute_motion(robot_id, motion)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating motion: {str(e)}"
            )
            
    async def simulate(
        self, 
        duration: float, 
        timestep: float = 0.001
    ) -> List[Dict]:
        """
        Run physics simulation for specified duration.
        
        Args:
            duration: Simulation duration in seconds
            timestep: Simulation timestep in seconds
            
        Returns:
            List[Dict]: List of simulation states at each timestep
            
        Raises:
            HTTPException: If simulation fails
        """
        try:
            states = []
            for t in np.arange(0, duration, timestep):
                await self.sim.step(timestep)
                states.append(await self.sim.get_state())
            return states
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error during simulation: {str(e)}"
            )
            
    async def render(
        self, 
        camera_params: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Render the current scene.
        
        Args:
            camera_params: Optional camera parameters
            
        Returns:
            np.ndarray: Rendered image
            
        Raises:
            HTTPException: If rendering fails
        """
        try:
            return await self.sim.render(camera_params)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error rendering scene: {str(e)}"
            )
            
    async def generate_soft_robot(self, design: Dict) -> str:
        """
        Generate a soft robot based on design parameters.
        
        Args:
            design: Dictionary containing soft robot design parameters
            
        Returns:
            str: Robot ID if successful
            
        Raises:
            HTTPException: If soft robot generation fails
        """
        try:
            robot_id = await self.sim.generate_soft_robot(design)
            self.robots[robot_id] = await self.sim.get_robot(robot_id)
            return robot_id
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating soft robot: {str(e)}"
            )
            
    async def cleanup(self) -> None:
        """
        Clean up simulation resources.
        
        Raises:
            HTTPException: If cleanup fails
        """
        try:
            await self.sim.cleanup()
            self.scene = None
            self.robots.clear()
            self.objects.clear()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error during cleanup: {str(e)}"
            ) 