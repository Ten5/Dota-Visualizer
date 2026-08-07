import os
import sys
import subprocess
import shutil

def build_standalone():
    """Builds a standalone executable bundle for the Dota 2 Visualizer application."""
    print("=" * 60)
    print("Building Dota 2 History Visualizer Standalone Executable")
    print("=" * 60)

    # Ensure required asset directories exist
    os.makedirs("assets/hero_images", exist_ok=True)
    os.makedirs("assets/music", exist_ok=True)
    os.makedirs("cache", exist_ok=True)

    icon_path = os.path.join("assets", "icon.png")
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file '{icon_path}' not found. Building without custom icon.")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=Dota2Visualizer",
        "--add-data=assets:assets",
        "--add-data=cache:cache",
    ]

    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")

    cmd.append("main.py")

    print(f"Running build command:\n{' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_dir = os.path.abspath("dist")
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL! 🚀")
        print(f"Standalone application bundle located in:\n{dist_dir}")
        print("=" * 60)
    else:
        print("\nBUILD FAILED! Check PyInstaller output for error details.")
        sys.exit(1)

if __name__ == "__main__":
    build_standalone()
