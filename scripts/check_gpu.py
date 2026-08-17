import platform
import subprocess
import sys

try:
    import psutil
except ImportError:
    psutil = None


def run_nvidia_smi():
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return None

        line = result.stdout.strip().splitlines()[0]
        parts = [x.strip() for x in line.split(",")]

        return {
            "name": parts[0],
            "vram_mb": float(parts[1]),
            "driver": parts[2],
        }

    except Exception:
        return None


def main():
    print("=" * 60)
    print("  GPU / CUDA Detection")
    print("=" * 60)
    print()

    print(f"OS:      {platform.system()} {platform.version()}")
    print(f"Python:  {platform.python_version()}")
    print(f"CPU:     {platform.processor()}")

    if psutil:
        mem = psutil.virtual_memory()

        print(
            f"RAM:     {mem.total / (1024 ** 3):.1f} GB"
        )

    print()

    gpu = run_nvidia_smi()

    if gpu:
        print(f"GPU:     {gpu['name']}")
        print(f"VRAM:    {gpu['vram_mb'] / 1024:.1f} GB")
        print(f"Driver:  {gpu['driver']}")
    else:
        print("GPU:     NVIDIA GPU not detected")

    print()

    try:
        import torch

        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA:    {torch.version.cuda}")

        cuda_available = torch.cuda.is_available()

        print(
            f"CUDA Available: "
            f"{'YES ✓' if cuda_available else 'NO ✗'}"
        )

        if cuda_available:
            print(
                f"GPU Name:       "
                f"{torch.cuda.get_device_name(0)}"
            )

            props = torch.cuda.get_device_properties(0)

            print(
                f"VRAM Total:     "
                f"{props.total_memory / (1024 ** 3):.1f} GB"
            )

            capability = torch.cuda.get_device_capability(0)

            print(
                f"Compute Cap:    "
                f"{capability[0]}.{capability[1]}"
            )

            print(
                f"cuDNN:          "
                f"{torch.backends.cudnn.version()}"
            )

        else:
            if gpu:
                print()
                print(
                    "WARNING: NVIDIA GPU detected but "
                    "PyTorch CUDA is NOT available."
                )

                print()
                print(
                    "Your PyTorch installation is probably "
                    "CPU-only."
                )

    except ImportError:
        print("PyTorch: NOT INSTALLED")
        print("CUDA:    Not available")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()