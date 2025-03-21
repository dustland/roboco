#!/usr/bin/env python
"""
Simple Genesis Simulation

This script demonstrates how to use Genesis directly within the isolated environment.
It creates a simple scene with a ground plane, adds a cube, and simulates physics.
"""

import genesis as gs
import time

def create_simple_scene():
    """Create a simple scene with ground and a cube."""
    # Create a scene
    scene = gs.Scene()
    
    # Add ground
    ground = scene.add_morph(gs.morphs.Plane())
    ground.make_rigid()
    ground.position = [0, 0, 0]
    
    # Add a cube
    cube = scene.add_morph(gs.morphs.Box(half_extents=[0.05, 0.05, 0.05]))
    cube.make_rigid()
    cube.position = [0, 0, 0.5]
    
    # Add default lighting
    scene.add_default_lighting()
    
    # Set up camera
    scene.camera.position = [1, 1, 0.5]
    scene.camera.look_at([0, 0, 0.2])
    
    return scene

def main():
    """Run main simulation."""
    print("Creating Genesis scene...")
    scene = create_simple_scene()
    
    # Run simulation for 2 seconds
    duration = 2.0
    dt = 0.01
    frames = int(duration / dt)
    
    print(f"Starting simulation for {duration} seconds ({frames} frames)")
    
    # Setup physics
    scene.prepare_step(dt=dt)
    
    # Run simulation
    for i in range(frames):
        scene.step()
    
    print("Simulation completed")
    
    # Render final frame
    output_path = "final_render.png"
    scene.render_to_file(output_path)
    print(f"Rendered scene to {output_path}")
    
    return 0

if __name__ == "__main__":
    main() 