import platform
import subprocess

from localization import tr


class NotificationService:
    @staticmethod
    def _escape_applescript_string(value):
        return (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\r", " ")
            .replace("\n", " ")
        )

    def notify_task_due(self, task_title):
        if platform.system() != "Darwin":
            return False

        title = self._escape_applescript_string(tr("Task Manager"))
        message = self._escape_applescript_string(
            f"{tr('Task is due')}: {task_title}"
        )
        script = f'display notification "{message}" with title "{title}"'
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0