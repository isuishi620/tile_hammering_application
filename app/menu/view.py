import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.base.view import ViewBase

class MenuView(ViewBase):
    def __init__(self, ui_path):
        super().__init__(ui_path)

        self._set_label()
        self._set_buttons()
       
        # self.checkBox.setText('USBAudio')
        # self.checkBox.setEnabled(False)

    def _set_label(self):
        # label_mode
        self.label_mode.setText('Mode Select')


    def _set_buttons(self):        
        # pushButton_new_training
        self.pushButton_new_training.setText('New\n Training')
        # pushButton_load_condition
        self.pushButton_load_condition.setText('Condition\n Load')
        # pushButton_end
        self.pushButton_end.setText('END')

    pass
