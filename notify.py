
import subprocess # no such things as import osascript

# possible sounds i like, not sure which to choose yet -> ["Bottle", "Glass", "Pop", "Purr"]

def notify(title, message, sound="Glass"):
    """Show a macOS notification banner via osascript (no Python API for this)."""
    script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
    subprocess.run(['osascript', '-e', script]) # execute notification in mac os


def main():
    """Send notification — quick manual test of notify()."""
    notify("Posture Check 🦒", "Your head's leaning forward — ease your chin back!")

if __name__ == "__main__":
    main()
