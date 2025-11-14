import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication

UI_PATH = "sandbox/01_QtDesignerで作成したUIの読み込み/layout.ui"

def main():
    # GUIアプリを動かすためのQApplication
    app = QApplication(sys.argv)
    
    # Qt Designerで作成したuiファイルの読み込み
    ui = uic.loadUi(UI_PATH)
    
    # 描画
    ui.show()

    # ui上にあるpushButtonをクリックしたときのsignalを
    # pushButton_clicked()という関数(slot)に接続
    ui.pushButton.clicked.connect(pushButton_clicked)
    
    # イベントループの開始
    return app.exec_()

def pushButton_clicked():
    print('pushButton_clicked')

if __name__ == "__main__":
    sys.exit(main())
