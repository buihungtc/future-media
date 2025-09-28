import subprocess
import sys
import signal
import time
from pathlib import Path


def main():
    project_root = Path(__file__).parent.resolve()

    scripts = [
        "request_flask.py",
        "sub_module1.py",
        "sub_module2.py",
    ]

    procs = []

    try:
        # Start all scripts
        for script in scripts:
            script_path = project_root / script
            if not script_path.exists():
                print(f"[ERROR] Not found: {script_path}")
                # If any script is missing, stop and clean up what started
                raise FileNotFoundError(script_path)

            print(f"[START] {script}")
            # On Windows, CREATE_NEW_PROCESS_GROUP lets us signal the child group if needed
            creationflags = 0
            if sys.platform.startswith("win"):
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            p = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(project_root),
                stdout=None,  # inherit parent's stdout
                stderr=None,  # inherit parent's stderr
                creationflags=creationflags,
            )
            procs.append((script, p))

        print("\nAll processes started. Press Ctrl+C to stop them.\n")

        # Wait until interrupted
        while True:
            # Optionally, detect if any process exited unexpectedly
            for name, p in procs:
                ret = p.poll()
                if ret is not None:
                    print(f"[EXIT] {name} exited with code {ret}. Stopping others...")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping child processes...")
        # Try graceful terminate first
        for name, p in procs:
            if p.poll() is None:
                try:
                    p.terminate()
                    print(f"[TERMINATE] Sent terminate to {name}")
                except Exception as e:
                    print(f"[WARN] terminate failed for {name}: {e}")

        # Give some time to exit
        time.sleep(2)

        # Force kill remaining
        for name, p in procs:
            if p.poll() is None:
                try:
                    p.kill()
                    print(f"[KILL] Forced kill for {name}")
                except Exception as e:
                    print(f"[WARN] kill failed for {name}: {e}")

    except FileNotFoundError as e:
        print(f"[FATAL] Missing script: {e}")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        # Ensure all are stopped before exiting
        for name, p in procs:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
        print("[DONE] Launcher exiting.")


if __name__ == "__main__":
    main()
