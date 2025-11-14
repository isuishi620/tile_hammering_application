import inspect
from PyQt5.QtCore import QObject

from model import Model
from view import View


class Controller(QObject):
    """コントローラークラス"""

    def __init__(self, model: Model, view: View) -> None:
        super().__init__()
        self.model = model
        self.view = view
        self.view.signal.connect(self.handle_view_signal)

    def on_pushButton_clicked(self) -> None:
        self.view.text(self.view.label, self.model.time)
        self.view.plot(self.view.plot_item, self.model.data)

    def handle_view_signal(self, name: str, ins: object) -> None:
        """
        Viewから (ウィジェット名, インスタンス) を受け取り、
        on_{name}_clicked を動的に呼び出す。
        """
        try:
            handler_name = f'on_{name}_clicked'
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                sig = inspect.signature(handler)
                num_params = len(sig.parameters)
                if num_params == 2:
                    handler(name, ins)  # on_xxx(self, name, ins)
                elif num_params == 1:
                    handler(name)       # on_xxx(self, name)
                else:
                    handler()           # on_xxx(self)
            else:
                raise NotImplementedError(f'{name} に対応するハンドラーが存在しません')
        except Exception as e:
            self.view.error(str(e))
