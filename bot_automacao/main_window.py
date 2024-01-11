import os
import re
from pathlib import Path
from threading import Thread
from time import sleep

import keyboard
import pyautogui
import pynput
from pynput import mouse
from PySide6 import QtCore, QtGui, QtWidgets


class ActionsLayout(QtWidgets.QScrollArea):
    def __init__(self):
        super().__init__()
        widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(widget)
        self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setWidget(widget)
        self.setWidgetResizable(True)


class RunThread(QtCore.QThread):
    finished = QtCore.Signal()

    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.keyboard_listener = pynput.keyboard.Listener(
            on_release=self.read_keys
        )

    def read_keys(self, *args):
        if os.name == 'nt':
            keyboard.wait('esc')
            if not self.isFinished():
                self.finished.emit()
                self.terminate()
        else:
            if args[0] == pynput.keyboard.Key.esc:
                self.keyboard_listener.stop()
                if not self.isFinished():
                    self.finished.emit()
                    self.terminate()

    def run(self):
        self.widget.hide()
        if os.name == 'nt':
            Thread(target=self.read_keys).start()
        else:
            self.keyboard_listener.start()
        for e, action_combobox in enumerate(self.widget.actions_comboboxes):
            if action_combobox.currentText() == 'Delay':
                sleep(int(self.widget.actions_inputs[e].text()))
                continue
            elif self.widget.default_delay_input.text():
                sleep(int(self.widget.default_delay_input.text()))
            x, y = re.findall(
                r'(\d+), (\d+)',
                self.widget.select_coords_buttons[e].text(),
            )[0]
            pyautogui.click(int(x), int(y))
            if action_combobox.currentText() != 'Clique':
                pyautogui.write(self.widget.actions_inputs[e].text())
        if os.name != 'nt':
            self.keyboard_listener.stop()
        self.finished.emit()


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(800, 600)
        with open('styles.qss', 'r') as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('Bot Automação')

        self.mouse_listener = mouse.Listener(on_click=self.on_select_coords)

        self.message_box = QtWidgets.QMessageBox()
        self.message_box.setWindowTitle('Aviso')

        self.actions_labels = []
        self.actions_comboboxes = []
        self.actions_inputs = []
        self.select_coords_buttons = []
        self.remove_action_buttons = []

        self.default_delay_label = QtWidgets.QLabel('Delay Padrão (Opcional):')
        self.default_delay_input = QtWidgets.QLineEdit()
        self.default_delay_input.setFixedWidth(180)
        self.default_delay_input.setValidator(QtGui.QIntValidator())
        self.default_delay_layout = QtWidgets.QHBoxLayout()
        self.default_delay_layout.addWidget(self.default_delay_label)
        self.default_delay_layout.addWidget(self.default_delay_input)
        self.default_delay_layout.addStretch()

        self.actions_layout = ActionsLayout()
        for _ in range(3):
            self.actions_layout.layout.addLayout(self.create_action_layout())

        self.add_action_button = QtWidgets.QPushButton('+')
        self.add_action_button.clicked.connect(self.add_action)

        self.run_button = QtWidgets.QPushButton('Rodar')
        self.run_button.clicked.connect(self.start_run_thread)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.default_delay_layout)
        self.main_layout.addWidget(self.actions_layout)
        self.main_layout.addWidget(self.add_action_button)
        self.main_layout.addWidget(self.run_button)

        self.run_thread = RunThread(self)
        self.run_thread.finished.connect(self.show_finish_message)

    def update_actions_labels(self):
        for e, label in enumerate(self.actions_labels):
            label.setText(f'{e + 1} - Ação:')

    def create_action_layout(self):
        action_label = QtWidgets.QLabel(
            f'{len(self.actions_labels) + 1} - Ação:'
        )
        action_label.setStyleSheet('margin-top: 10px;')
        action_combobox = QtWidgets.QComboBox()
        action_combobox.addItem('Clique')
        action_combobox.addItem('Preencher')
        action_combobox.addItem('Delay')
        action_combobox.setFixedWidth(400)
        action_input = QtWidgets.QLineEdit()
        action_input.setVisible(False)
        select_coords_button = QtWidgets.QPushButton(' Selecionar')
        select_coords_button.setFixedWidth(200)
        select_coords_button.setIcon(
            QtGui.QIcon(str(Path('assets') / 'selection.png'))
        )
        select_coords_button.setIconSize(QtCore.QSize(40, 40))
        select_coords_button.setStyleSheet(
            'border: 0; background: transparent; padding: 5px; text-align: left;'
        )
        remove_action_button = QtWidgets.QPushButton()
        remove_action_button.setIcon(
            QtGui.QIcon(str(Path('assets') / 'trash.png'))
        )
        remove_action_button.setIconSize(QtCore.QSize(40, 40))
        remove_action_button.setStyleSheet(
            'border: 0; background: transparent; padding: 5px;'
        )
        action_layout = QtWidgets.QHBoxLayout()
        action_layout.addWidget(action_label)
        action_layout.addWidget(action_combobox)
        action_layout.addWidget(action_input)
        action_layout.addWidget(select_coords_button)
        action_layout.addWidget(remove_action_button)
        self.actions_labels.append(action_label)
        self.actions_comboboxes.append(action_combobox)
        self.actions_inputs.append(action_input)
        self.select_coords_buttons.append(select_coords_button)
        self.remove_action_buttons.append(remove_action_button)
        action_combobox.currentTextChanged.connect(
            lambda *args: self.on_action_combobox_changed(
                *args, self.actions_comboboxes.index(action_combobox)
            )
        )
        select_coords_button.clicked.connect(
            lambda: self.select_coords(
                self.select_coords_buttons.index(select_coords_button)
            )
        )
        remove_action_button.clicked.connect(
            lambda: self.remove_action(
                self.remove_action_buttons.index(remove_action_button)
            )
        )
        return action_layout

    def on_select_coords(self, x, y, button, pressed, action_index):
        self.select_coords_buttons[action_index].setText(f' ({x}, {y})')
        self.mouse_listener.stop()
        self.show()

    @QtCore.Slot()
    def select_coords(self, action_index):
        self.hide()
        self.mouse_listener = mouse.Listener(
            on_click=lambda *args: self.on_select_coords(*args, action_index)
        )
        self.mouse_listener.start()

    @QtCore.Slot()
    def remove_action(self, action_index):
        self.actions_comboboxes.pop(action_index)
        self.actions_labels.pop(action_index)
        self.select_coords_buttons.pop(action_index)
        self.remove_action_buttons.pop(action_index)
        self.actions_layout.layout.removeItem(
            self.actions_layout.layout.itemAt(action_index)
        )
        widget = QtWidgets.QWidget()
        widget.setLayout(self.actions_layout.layout)
        self.actions_layout.setWidget(widget)
        self.update_actions_labels()

    @QtCore.Slot()
    def add_action(self):
        self.actions_layout.layout.addLayout(self.create_action_layout())

    @QtCore.Slot()
    def on_action_combobox_changed(self, text, action_index):
        visibles = {
            'Clique': (False, True, True),
            'Preencher': (True, True, True),
            'Delay': (True, False, False),
        }
        try:
            visible = visibles[text]
            self.actions_inputs[action_index].setText('')
        except (KeyError, RuntimeError):
            return
        if visible[0]:
            self.actions_comboboxes[action_index].setFixedWidth(300)
        if text == 'Delay':
            self.actions_inputs[action_index].setValidator(QtGui.QIntValidator())
            self.actions_inputs[action_index].setFixedWidth(180)
            self.actions_comboboxes[action_index].setFixedWidth(500)
        elif text == 'Preencher':
            self.actions_inputs[action_index].setValidator(QtGui.QRegularExpressionValidator(r'.*'))
            self.actions_inputs[action_index].setFixedWidth(200)
            self.actions_comboboxes[action_index].setFixedWidth(200)
        elif text == 'Clique':
            self.actions_comboboxes[action_index].setFixedWidth(400)
        self.actions_inputs[action_index].setVisible(visible[0])
        self.remove_action_buttons[action_index].setVisible(visible[1])
        self.select_coords_buttons[action_index].setVisible(visible[2])

    @QtCore.Slot()
    def start_run_thread(self):
        for e, combobox in enumerate(self.actions_comboboxes):
            if combobox.currentText() != 'Delay' and 'Selecionar' in self.select_coords_buttons[e].text():
                self.message_box.setText('Selecione as coordenadas pendentes')
                self.message_box.show()
                return
            elif combobox.currentText() != 'Clique' and not self.actions_inputs[e].text():
                self.message_box.setText('Preencha os campos obrigatórios')
                self.message_box.show()
                return
        self.message_box.setText('Aperte ESC para parar a automação')
        self.message_box.exec()
        self.run_thread.start()

    @QtCore.Slot()
    def show_finish_message(self):
        self.show()
        self.message_box.setText('Finalizado')
        self.message_box.show()
