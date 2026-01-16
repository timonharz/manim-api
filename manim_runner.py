import sys
import os
import json
import importlib.util
import traceback
from pathlib import Path

# Ensure manimlib is importable from the current directory
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from manimlib.scene.scene import Scene


def find_scene_classes(module, scene_name=None):
    """Find the scene classes to render from the module."""
    import inspect
    
    scene_classes = []
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) and 
            issubclass(obj, Scene) and 
            obj is not Scene and
            obj.__module__ == module.__name__):
            scene_classes.append((name, obj))
    
    if not scene_classes:
        raise ValueError("No Scene classes found in the provided code")
    
    # If specific scene requested, return just that one
    if scene_name:
        for name, cls in scene_classes:
            if name == scene_name:
                return [(name, cls)]
        raise ValueError(f"Scene '{scene_name}' not found. Available scenes: {[n for n, _ in scene_classes]}")
    
    # Otherwise return all scenes found
    return scene_classes


def main():
    if len(sys.argv) < 2:
        print("Usage: python manim_runner.py <config_path>")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        code_path = Path(config['code_path'])
        scene_name = config.get('scene_name')
        camera_config = config.get('camera_config', {})
        base_file_writer_config = config.get('file_writer_config', {})

        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("user_scene", code_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["user_scene"] = module
        spec.loader.exec_module(module)

        # Find the scene classes
        scene_classes = find_scene_classes(module, scene_name)
        print(f"Found scenes: {[name for name, _ in scene_classes]}")

        # Run each scene
        for i, (name, SceneClass) in enumerate(scene_classes):
            print(f"Rendering scene: {name} ({i+1}/{len(scene_classes)})...")
            
            # Create a unique config for this scene
            file_writer_config = base_file_writer_config.copy()
            original_filename = file_writer_config.get("file_name", "output")
            
            # Append index/name to ensure unique output files if multiple scenes
            if len(scene_classes) > 1:
                file_writer_config["file_name"] = f"{original_filename}_{i:02d}"
            
            scene = SceneClass(
                window=None,
                camera_config=camera_config,
                file_writer_config=file_writer_config,
                skip_animations=False,
                always_update_mobjects=False,
                show_animation_progress=False,
                leave_progress_bars=False,
            )
            scene.run()
        
        # Cleanup
        if "user_scene" in sys.modules:
            del sys.modules["user_scene"]

    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
