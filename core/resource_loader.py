"""
Loads resources from internal storage.
Used in pre-built version of Remixer.
"""
import os
import sys


class Loader: # pylint: disable=too-few-public-methods # Aknowledged
    """
    Loads resources from internal storage.
    Used in pre-built version of Remixer.
    """
    @staticmethod
    def resource_path(relative_path):
        """
        Loads resources from internal storage.
        Used in pre-built version of Remixer.
        Parameters:
            relative_path (str): Path to resource.
        """
        try:
            base_path = sys._MEIPASS   # pylint: disable=protected-access disable=no-member   # Reason: Used to load resources in pre-built version of Remixer
        except Exception:              # pylint: disable=broad-exception-caught               # Reason: Intercepts any errors, no action required
            base_path = os.path.abspath(".")
        relative_path = relative_path.replace("./", "").replace("/","\\")

        return os.path.join(base_path, relative_path)
