import asyncio
import sys
from pathlib import Path


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Make project root available for backend imports
sys.path.insert(0, str(PROJECT_ROOT))


def get_status_value(status):
    """Safely get enum/string status value."""
    return getattr(status, "value", str(status))


async def main():
    print("=" * 60)
    print("  Local AI Voice Studio - Model Download")
    print("=" * 60)
    print()

    try:
        from backend.services.model_manager import get_model_manager
        from backend.services.model_registry import get_model_registry
    except ImportError as exc:
        print("[ERROR] Failed to import model manager/registry.")
        print()
        print(f"Details: {exc}")
        print()
        print("Make sure you are running this script from the project")
        print("and that all required Python dependencies are installed.")
        return 1

    try:
        registry = get_model_registry()
        manager = get_model_manager()
    except Exception as exc:
        print("[ERROR] Failed to initialize model manager.")
        print()
        print(f"Details: {exc}")
        return 1

    try:
        models = registry.get_all()
    except Exception as exc:
        print("[ERROR] Failed to load model registry.")
        print()
        print(f"Details: {exc}")
        return 1

    print(f"Available models: {len(models)}")
    print()

    if not models:
        print("[WARNING] No models found in the registry.")
        print()
        return 0

    # ============================================================
    # Show model status
    # ============================================================

    print("Model Status")
    print("-" * 60)

    for model in models:
        try:
            status = registry.get_status(model.id)
            status_value = get_status_value(status)

            if status_value == "installed":
                icon = "INSTALLED"
            else:
                icon = "NOT INSTALLED"

            print(
                f"  [{icon}] "
                f"{model.name} "
                f"({model.size_gb} GB) - "
                f"{model.engine.value}"
            )

        except Exception as exc:
            print(f"  [ERROR] {model.id}: {exc}")

    print()

    # ============================================================
    # Install missing models
    # ============================================================

    for model in models:
        try:
            status = registry.get_status(model.id)
            status_value = get_status_value(status)

            if status_value == "installed":
                continue

            print("=" * 60)
            print(f"Installing: {model.name}")
            print(f"Model ID:   {model.id}")
            print(f"Size:       {model.size_gb} GB")
            print(f"Engine:     {model.engine.value}")
            print("=" * 60)
            print()

            try:
                async for progress in manager.install_model(model.id):
                    progress_status = get_status_value(progress.status)
                    message = getattr(progress, "message", "")
                    progress_value = getattr(progress, "progress", 0)

                    try:
                        percent = progress_value * 100
                    except (TypeError, ValueError):
                        percent = 0

                    print(
                        f"  [{progress_status}] "
                        f"{message} "
                        f"({percent:.0f}%)"
                    )

                    if progress_status in ("completed", "error"):
                        break

                print()

            except Exception as exc:
                print()
                print(f"[ERROR] Failed to install {model.name}")
                print(f"        {exc}")
                print()

        except Exception as exc:
            print(f"[ERROR] Could not process {model.id}: {exc}")
            print()

    # ============================================================
    # Final status
    # ============================================================

    print("=" * 60)
    print("  Final Model Status")
    print("=" * 60)
    print()

    for model in models:
        try:
            status = registry.get_status(model.id)
            status_value = get_status_value(status)

            if status_value == "installed":
                print(f"  [INSTALLED]     {model.name}")
            else:
                print(f"  [NOT INSTALLED] {model.name}")

        except Exception as exc:
            print(f"  [ERROR]         {model.name}: {exc}")

    print()
    print("Model download process finished.")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("Download cancelled by user.")
        exit_code = 130
    except Exception as exc:
        print()
        print("=" * 60)
        print("  Unexpected Error")
        print("=" * 60)
        print()
        print(exc)
        exit_code = 1

    sys.exit(exit_code)