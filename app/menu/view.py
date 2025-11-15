from __future__ import annotations

from app.base.view import ViewBase


class MenuView(ViewBase):
    """ボタンとラベルの文言を整えるだけのシンプルなビュー。"""

    def __init__(self, ui_path: str):
        super().__init__(ui_path)
        self._configure_labels()
        self._configure_buttons()

    def _configure_labels(self) -> None:
        self.label_mode.setText("Mode Select")

    def _configure_buttons(self) -> None:
        self.pushButton_new_training.setText("New\nTraining")
        self.pushButton_load_condition.setText("Condition\nLoad")
        self.pushButton_end.setText("End")
