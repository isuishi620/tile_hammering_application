from __future__ import annotations

import inspect
from typing import Any, Callable, Iterable, List

from PyQt5.QtCore import QObject, pyqtSignal

from .model import ModelBase
from .view import ViewBase


Handler = Callable[..., None]


class ControllerBase(QObject):
    """各ウィンドウ用コントローラーの共通処理。"""

    signal = pyqtSignal(object)

    def __init__(self, model: ModelBase, view: ViewBase):
        super().__init__()
        self.model = model
        self.view = view

        self.model.trigger_signal.connect(self.handle_trigger_signal)
        self.view.signal.connect(self.handle_view_signal)

        self.trigger_methods: List[Callable[[], None]] = []
        self.timeout_methods: List[Callable[[], None]] = []

    # ------------------------------------------------------------------ #
    # ビューシグナルの振り分け補助
    # ------------------------------------------------------------------ #
    def handle_view_signal(
        self,
        name: str,
        widget: object,
        event: str,
        payload: Any | None = None,
    ) -> None:
        """ビューからのシグナルを対応するハンドラーへ振り分ける。"""
        try:
            for candidate in self._candidate_handlers(name, event):
                if hasattr(self, candidate):
                    handler = getattr(self, candidate)
                    self._invoke(handler, name, widget, event, payload)
                    return
            raise NotImplementedError(f"{name}({event}) has no handler")
        except Exception as exc:  # pragma: no cover - 防御的なUI経路
            self.view.error(str(exc))

    def _candidate_handlers(self, name: str, event: str) -> Iterable[str]:
        return (
            f"on_{name}_{event}",
            f"on_{event}",
            f"on_{name}",
            "on_any",
        )

    def _invoke(self, handler: Handler, name: str, widget: object, event: str, payload: Any) -> None:
        """ハンドラーの想定引数数を守って呼び出す。"""
        args = (name, widget, event, payload)
        argc = len(inspect.signature(handler).parameters)
        handler(*args[:argc])

    # ------------------------------------------------------------------ #
    # トリガー処理
    # ------------------------------------------------------------------ #
    def handle_trigger_signal(self) -> None:
        try:
            for method in list(self.trigger_methods):
                method()
        except Exception as exc:  # pragma: no cover - 防御的なUI経路
            self.view.error(str(exc))

    def add_trigger_method(self, method: Callable[[], None]) -> None:
        if method not in self.trigger_methods:
            self.trigger_methods.append(method)

    def remove_trigger_method(self, method: Callable[[], None]) -> None:
        if method in self.trigger_methods:
            self.trigger_methods.remove(method)

    def reset_trigger_method(self) -> None:
        self.trigger_methods.clear()

    # ------------------------------------------------------------------ #
    # タイマー補助
    # ------------------------------------------------------------------ #
    def handle_timer_signal(self) -> None:
        if not self.view.isVisible():
            return
        try:
            for method in list(self.timeout_methods):
                method()
        except Exception as exc:  # pragma: no cover - 防御的なUI経路
            self.view.error(str(exc))

    def add_timeout_method(self, method: Callable[[], None]) -> None:
        if method not in self.timeout_methods:
            self.timeout_methods.append(method)

    def remove_timeout_method(self, method: Callable[[], None]) -> None:
        if method in self.timeout_methods:
            self.timeout_methods.remove(method)

    def reset_timeout_method(self) -> None:
        self.timeout_methods.clear()

    # ------------------------------------------------------------------ #
    # 共通の開始/停止処理
    # ------------------------------------------------------------------ #
    def start_process(self) -> None:
        """利用可能なら音声/カメラ処理を開始する。"""
        audio = getattr(self.model, "audio", None)
        if audio is not None:
            audio.start()
        self.model.audio_is_stream = True
        self.model.camera_is_stream = True

    def end_process(self) -> None:
        """利用可能なら音声/カメラ処理を停止する。"""
        audio = getattr(self.model, "audio", None)
        if audio is not None:
            audio.stop()
        self.model.audio_is_stream = False
        self.model.camera_is_stream = False
