from PyQt5.QtCore import QObject


class ModelBase(QObject):
    """Qt aware base class to allow signal/slot usage inside models."""

    def __init__(self):
        super().__init__()
