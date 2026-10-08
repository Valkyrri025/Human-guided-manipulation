"""Save an inspectable machine report without requiring PyTorch."""
import importlib.util
import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys


def command(args):
    if not shutil.which(args[0]):
        return {"available": False}
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    return {"available": True, "returncode": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


report = {
    "python": sys.version, "python_executable": sys.executable,
    "platform": platform.platform(),
    "gpu": command(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free", "--format=csv,noheader"]),
    "cuda_compiler": command(["nvcc", "--version"]),
    "git": command(["git", "--version"]),
    "conda": command(["conda", "--version"]),
    "uv": command(["uv", "--version"]),
    "packages": {},
}
for package in ["torch", "robosuite", "mujoco", "numpy", "opencv-python", "imageio-ffmpeg"]:
    try:
        report["packages"][package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        report["packages"][package] = None
if importlib.util.find_spec("torch"):
    import torch
    report["torch"] = {"version": torch.__version__, "cuda_build": torch.version.cuda,
                       "cuda_available": torch.cuda.is_available()}
    if torch.cuda.is_available():
        x = torch.arange(16, device="cuda", dtype=torch.float32)
        report["torch"]["gpu_compute_test"] = float((x * x).sum().item())
        report["torch"]["device"] = torch.cuda.get_device_name(0)
        report["torch"]["capability"] = torch.cuda.get_device_capability(0)
        report["torch"]["wheel_architectures"] = torch.cuda.get_arch_list()
else:
    report["torch"] = {"installed": False, "gpu_compute_test": "not run"}
output = Path("outputs/machine.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
