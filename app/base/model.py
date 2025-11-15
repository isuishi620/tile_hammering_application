from PyQt5.QtCore import QObject


class ModelBase(QObject):
    """モデル内でQtのシグナル/スロットを扱えるようにする基底クラス。"""

    def __init__(self):
        super().__init__()
