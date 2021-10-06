import sys
import os
import pyperclip
import requests
import webbrowser
import time
import datetime
from threading import Thread
from PyQt5 import uic
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QLineEdit, \
    QMainWindow, QMessageBox, QAction, QDesktopWidget, \
    QPushButton, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QWidgetAction
from PyQt5.QtCore import QRunnable, QThread, pyqtSignal, \
    QObject, Qt, QTimer, QThreadPool, pyqtSlot
from PyQt5.QtGui import *
from telethon import TelegramClient
import asyncio
import pickle
from session_creator import *
from id_manager import *

#[ ] add charting based on kpi and all other users
#[ ] count message based on dates
#[ ] add extra features to delete joining messages
#[ ] create logging system


version = 'v2.0'
new_version = ''
stop_process = False

def version_check():  # for checking new releases on github
    global new_version
    try:
        response = requests.get(
            "https://api.github.com/repos/Sakib0194/Telecounter/releases/latest")
        new_version = response.json()["name"]
    except:
        new_version = 'v2.0'

Thread(target=version_check).start()

api_id = 1234567
api_hash = 'test'

if os.path.exists('resource/kpi_id.pckl'):
    pass
else:
    data_store = open('kpi_id.pckl', 'wb')
    pickle.dump({}, data_store)
    data_store.close()

data_store = open('resource/kpi_id.pckl', 'rb')  # retrieve saved kpi id
accounts = pickle.load(data_store)
data_store.close()


class version_form(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.setWindowIcon(QIcon('resource/logo.png'))
        except Exception:
            pass
        layout = QVBoxLayout()
        layout_2 = QHBoxLayout()
        self.label = QLabel(f'New Version {new_version} is available')
        layout.addWidget(self.label)
        self.button_update = QPushButton('Update')
        self.button_cancel = QPushButton('Cancel')
        layout_2.addWidget(self.button_update)
        layout_2.addWidget(self.button_cancel)
        layout.addLayout(layout_2)
        self.setLayout(layout)
        self.button_update.clicked.connect(self.update_gui)
        self.button_cancel.clicked.connect(self.exiting)

    def update_gui(self):
        webbrowser.open_new(
            'https://github.com/Sakib0194/Telecounter/releases')

    def exiting(self):
        self.close()


class main_form(QMainWindow):
    global client

    def __init__(self):
        super().__init__()
        try:
            self.setWindowIcon(QIcon('resource/logo.png'))
        except Exception:
            pass
        self.ui = uic.loadUi('resource/Design.ui', self)

        self.manager = id_manager(self.ui)
        self.sess = session_builder(self.ui)

        self.group_name = ''
        self.group_name_2 = ''
        self.cu_session = ''
        self.worker = ''
        self.cu_dots = ''
        self.box_selected = ''

        self.group_starting = 0
        self.group_ending = 0
        self.all_latest_row_num = 0
        self.kpi_latest_row_num = 0
        self.force_stop = 2
        self.counting_time = 1
        self.mess_value = 0
        self.mess_id_latest = 0
        
        self.create_log = True
        self.multi_sess_selected = False
        self.reload_pressed = False
        self.starting_paste = True
        self.ending_paste = True
        self.pri_group = False
        self.running = False
        self.finishing_log = False
        self.counting = False

        self.all_cell_selected = {}
        self.kpi_cell_selected = {}
        self.finishing_data = {}
        self.total_mess_char = {}
        self.largest_text_all = {}
        self.largest_text_kpi = {}
        self.all_log_row = {}
        self.kpi_log_row = {}
        self.cu_bar_value = {}
        self.cu_total_mess = {}
        self.cu_kpi_mess = {}
        
        self.incomplete_sess = []
        self.session_list = []

        self.button_calender_1 = QPushButton(self.ui.box_starting_mess)
        self.button_calender_2 = QPushButton(self.ui.box_ending_mess)
        self.button_calender_3 = QPushButton(self.ui.box_ending_date)
        
        self.session_detector()
        self.exit_detector()
        self.connections()
        self.new_buttons()
        self.modifier()

        self.timer = QTimer()
        self.thread_timer = QTimer()
        self.row_timer = QTimer()
        self.clear_statusbar = QTimer()

        self.row_timer.setInterval(500)
        self.row_timer.timeout.connect(self.row_data_setter)

        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.check_update)

        self.clear_statusbar.setInterval(3000)
        self.clear_statusbar.timeout.connect(self.empty_statusbar)
        
        self.timer.start()
        self.show()

    def connections(self):  # connect all events
        self.ui.button_create_sess.clicked.connect(self.sess.sess_creator)
        self.ui.button_send_code.clicked.connect(self.sess.tg_code_sender)
        self.ui.button_clear_1.clicked.connect(self.edit_box_1)
        self.ui.button_clear_2.clicked.connect(self.edit_box_2)
        self.ui.button_reload.clicked.connect(self.reload_router)
        self.ui.button_add_user.clicked.connect(self.manager.add_user)
        self.ui.listWidget.itemClicked.connect(self.manager.list_selected)
        self.ui.button_remove.clicked.connect(self.manager.list_remove)
        self.ui.button_save.clicked.connect(self.manager.list_save)
        self.ui.box_ending_mess.textChanged.connect(self.text_changed_ending)
        self.ui.box_starting_mess.textChanged.connect(self.text_changed_starting)
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui.Button_count.clicked.connect(self.data_parser)
        self.ui.button_exit.clicked.connect(self.exiting)
        self.ui.table_widget_1.horizontalHeader().sortIndicatorChanged.connect(self.sorting_event_1)
        self.ui.table_widget_2.horizontalHeader().sortIndicatorChanged.connect(self.sorting_event_2)
        self.button_calender_1.clicked.connect(self.ui.calender_display_1)
        self.button_calender_2.clicked.connect(self.ui.calender_display_2)
        self.button_calender_3.clicked.connect(self.ui.calender_display_3)
        self.ui.calender.selectionChanged.connect(self.calender_event)
        QApplication.instance().focusChanged.connect(self.focus_change)
        

    def modifier(self):  # modify widgets, button before the window loads
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)
        self.ui.button_clear_2.setText('Paste')
        self.ui.button_clear_1.setText('Paste')
        self.ui.resize(628, 325)
        self.ui.box_tg_code.resize(75, 30)
        self.ui.button_send_code.resize(90, 30)
        self.ui.table_widget_1.setColumnWidth(0, 115)
        self.ui.table_widget_2.setColumnWidth(0, 115)
        self.ui.table_widget_1.setColumnWidth(1, 110)
        self.ui.table_widget_2.setColumnWidth(1, 110)
        self.ui.table_widget_1.setColumnWidth(2, 80)
        self.ui.table_widget_2.setColumnWidth(2, 80)
        self.ui.calender.hide()
        self.ui.calender.setVerticalHeaderFormat(0)
        self.ui.box_ending_date.hide()
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def new_buttons(self):
        self.button_calender_1.setText('📅')
        self.button_calender_1.setCursor(Qt.ArrowCursor)
        actions = QWidgetAction(self.button_calender_1)
        actions.setDefaultWidget(self.button_calender_1)
        self.ui.box_starting_mess.addAction(actions, QLineEdit.TrailingPosition)

        self.button_calender_2.setText('📅')
        self.button_calender_2.setCursor(Qt.ArrowCursor)
        actions = QWidgetAction(self.button_calender_2)
        actions.setDefaultWidget(self.button_calender_2)
        self.ui.box_ending_mess.addAction(actions, QLineEdit.TrailingPosition)

        self.button_calender_3.setText('📅')
        self.button_calender_3.setCursor(Qt.ArrowCursor)
        actions = QWidgetAction(self.button_calender_3)
        actions.setDefaultWidget(self.button_calender_3)
        self.ui.box_ending_date.addAction(actions, QLineEdit.TrailingPosition)

    def show_date_box(self):
        self.ui.box_ending_date.setMinimumSize(205, 35)
        self.ui.box_ending_date.setMaximumSize(205, 35)
        self.ui.box_starting_mess.setMinimumSize(205, 35)
        self.ui.box_starting_mess.setMaximumSize(205, 35)
        self.ui.box_starting_mess.setPlaceholderText('Starting Date')
        self.ui.box_ending_date.setPlaceholderText('Ending Date')
        self.ui.box_ending_mess.setPlaceholderText('Group Username/Link')
        self.ui.box_ending_date.resize(200, 35)
        self.ui.button_clear_1.hide()
        self.ui.box_ending_date.show()
        self.ui.label.setText('Start And End Date')
        self.ui.label_10.setText('Group Username/Link')

    def calender_display_1(self):
        if self.ui.calender.isVisible():
            self.ui.calender.hide()
            self.ui.setMinimumSize(0,0) 
            self.ui.resize(628, 325) 
            self.box_selected = '' 

        else:
            self.ui.resize(628, 588) 
            self.ui.calender.show() 
            self.box_selected = 'box_starting_mess'
            self.show_date_box()

    def calender_display_2(self):
        if self.ui.calender.isVisible():
            self.ui.calender.hide()
            self.ui.setMinimumSize(0,0) 
            self.ui.resize(628, 325) 
            self.box_selected = '' 
            
        else:
            self.ui.resize(628, 588) 
            self.ui.calender.show()
            self.box_selected = 'box_ending_mess'
            self.show_date_box()

    def calender_display_3(self):
        if self.ui.calender.isVisible():
            self.ui.calender.hide()
            self.ui.setMinimumSize(0,0) 
            self.ui.resize(628, 325) 
            self.box_selected = '' 
            
        else:
            self.ui.resize(628, 588) 
            self.ui.calender.show()
            self.box_selected = 'box_ending_date'
            self.show_date_box()

    def focus_change(self, old, new):
        try:
            new_widg = new.objectName()
            if new_widg == 'box_ending_mess' or new_widg == 'box_starting_mess':
                self.box_selected = new_widg
        except:
            pass

    def calender_event(self):
        selected_date = self.ui.calender.selectedDate().toString("dd-MM-yyyy")
        if self.box_selected != '':
            if self.box_selected == 'box_starting_mess':
                self.ui.box_starting_mess.clear()
                self.ui.box_starting_mess.setText(selected_date)
            
            elif self.box_selected == 'box_ending_mess':
                self.ui.box_ending_mess.clear()
                self.ui.box_ending_mess.setText(selected_date)

    def check_update(self):  # for opening the new version available form
        print('Current Version', version)
        version_num = float(version.split('v')[1])
        new_version_num = float(new_version.split('v')[1])
        if version_num < new_version_num:
            self.w = version_form()
            self.w.show()
        self.timer.stop()

    def empty_statusbar(self): #clear status bar message
        self.clear_statusbar.stop()
        self.ui.statusBar().clearMessage()

    def sorting_event_1(self):  #triggered when clicking on table column buttons
        self.ui.table_widget_1.clearSelection()
    
    def sorting_event_2(self):
        self.ui.table_widget_2.clearSelection()

    def cell_copier(self):  #copies cells selected in the table widget
        self.all_cell_selected = {}
        self.kpi_cell_selected = {}
        self.largest_text_all = {}
        self.largest_text_kpi = {}
        full_text = ''
        current_tab = self.ui.tabWidget.currentIndex() 
        current_focus = QtWidgets.QApplication.focusWidget().objectName()
        
        if current_focus == 'table_widget_1':
            for i in self.ui.table_widget_1.selectedItems():
                row_num = i.row()
                col_num = i.column()
                cell_text = i.text()
                if row_num not in self.all_cell_selected:
                    self.all_cell_selected[row_num] = {}
                self.all_cell_selected[row_num][col_num] = cell_text

                if col_num not in self.largest_text_all:
                    self.largest_text_all[col_num] = 0
                
                if len(cell_text) > self.largest_text_all[col_num]:
                    self.largest_text_all[col_num] = len(cell_text)

        if current_focus == 'table_widget_2':
            for i in self.ui.table_widget_2.selectedItems():
                row_num = i.row()
                col_num = i.column()
                cell_text = i.text()
                if row_num not in self.kpi_cell_selected:
                    self.kpi_cell_selected[row_num] = {}
                self.kpi_cell_selected[row_num][col_num] = cell_text

                if col_num not in self.largest_text_kpi:
                    self.largest_text_kpi[col_num] = 0
                
                if len(cell_text) > self.largest_text_kpi[col_num]:
                    self.largest_text_kpi[col_num] = len(cell_text)
        
        #sort all data by keys so rows and columns aligns properly
        self.all_cell_selected = dict(sorted(self.all_cell_selected.items()))
        self.largest_text_all = dict(sorted(self.largest_text_all.items()))
        self.kpi_cell_selected = dict(sorted(self.kpi_cell_selected.items()))
        self.largest_text_kpi = dict(sorted(self.largest_text_kpi.items()))
        
        for i in self.all_cell_selected:
            self.all_cell_selected[i] = dict(sorted(self.all_cell_selected[i].items()))

        for i in self.kpi_cell_selected:
            self.kpi_cell_selected[i] = dict(sorted(self.kpi_cell_selected[i].items()))

        for cell in self.all_cell_selected:
            for dat in self.all_cell_selected[cell]:
                text_to_add = self.all_cell_selected[cell][dat]
                full_text += f'{text_to_add}'.ljust(self.largest_text_all[dat] + 1)
            full_text += '\n'

        for cell in self.kpi_cell_selected:
            for dat in self.kpi_cell_selected[cell]:
                text_to_add = self.kpi_cell_selected[cell][dat]
                full_text += f'{text_to_add}'.ljust(self.largest_text_kpi[dat] + 1)
            full_text += '\n'

        if self.all_cell_selected != {} or self.kpi_cell_selected  != {}:
            if current_tab == 1:
                pyperclip.copy(full_text)
                self.ui.statusBar().showMessage(f'Cells Copied')
                self.clear_statusbar.start()

    def keyPressEvent(self, event): #copy event when pressing CTRL C
        if QKeySequence(event.key()+int(event.modifiers())) == QKeySequence("Ctrl+C"):
            self.cell_copier()

    def tab_changed(self): 
        # resize form if message log tab selected
        #if the calender widget is on, remove that
        self.box_selected = '' 
        self.ui.calender.hide()
        self.ui.setMinimumSize(0,0) 
        self.ui.resize(628, 325)  

        if self.ui.tabWidget.currentIndex() == 1:
            self.resize(850, 400)
        else:
            self.resize(400, 350)

    def text_changed_starting(self):
        # if text box empty, paste from clipboard on click
        # if text box has text, clearself.all_log_row box on click

        text = self.ui.box_starting_mess.text()
        if text == '':
            self.ui.button_clear_1.setText('Paste')
            self.starting_paste = True
        else:
            self.ui.button_clear_1.setText('Clear')
            self.starting_paste = False

    def text_changed_ending(self):
        text = self.ui.box_ending_mess.text()
        if text == '':
            self.ui.button_clear_2.setText('Paste')
            self.ending_paste = True
        else:
            self.ui.button_clear_2.setText('Clear')
            self.ending_paste = False

    def closeEvent(self, event):
        global stop_process
        # show warning on clicking close/exit
        close = QMessageBox()
        if self.running is True:
            if self.force_stop != 1:
                self.force_stop -= 1
                close.setText(
                    f"Cannot close! Action ongoing\nTry {self.force_stop} more time to Force Close the App")
                close.setStandardButtons(QMessageBox.Cancel)
                close.setIcon(QMessageBox.Warning)
                close = close.exec()
                event.ignore()
            else:
                stop_process = True
                event.accept()
        else:
            close.setText("You sure?")
            close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            close.setIcon(QMessageBox.Question)
            close = close.exec()
            if close == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    def reload_router(self): #for checking whether Reload button at ID manager was clicked 
        self.reload_pressed = True
        self.sess.reload_value()
        self.manager.reload_list()

    def exit_detector(self):
        quit = QAction("Quit", self)
        quit.triggered.connect(self.close)

    def reload_kpi(self):   #reloads pickle kpi data to the list
        global accounts
        data_store = open('resource/kpi_id.pckl', 'rb')
        accounts = pickle.load(data_store)
        data_store.close()

    def exiting(self):
        self.close()

    def session_detector(self):
        # check currently available session files

        all_files = []
        self.session_list = []
        self.ui.combobox_session.clear()
        self.ui.combo_session_2.clear()
        for files in os.listdir(os.curdir):
            if files.endswith('session'):
                base_name = os.path.splitext(files)[0]
                all_files.append(base_name)
                self.session_list.append(base_name)
        if all_files == []:
            self.ui.combobox_session.addItem('Nothing Found')
            self.ui.combobox_session.setCurrentIndex(0)
            self.ui.combo_session_2.addItem('Nothing Found')
            self.ui.combo_session_2.setCurrentIndex(0)
        else:
            self.ui.combobox_session.addItems(all_files)
            self.ui.combobox_session.setCurrentIndex(0)
            self.ui.combo_session_2.addItems(all_files)
            self.ui.combo_session_2.setCurrentIndex(0)

    def edit_box_1(self):   #Paste/Clear button on Message Box
        if self.starting_paste is True:
            self.ui.box_starting_mess.setText(str(pyperclip.paste()))
        else:
            self.ui.box_starting_mess.clear()

    def edit_box_2(self):
        if self.ending_paste is True:
            self.ui.box_ending_mess.setText(str(pyperclip.paste()))
        else:
            self.ui.box_ending_mess.clear()

    def data_parser(self): 
        #verifies message box message links
        # for private group/public group
        # whether date was entered
        # or for invalid link

        if '-' in self.ui.box_starting_mess.text():
            self.datetime_parser()
        else:
            if self.ui.check_create_log.isChecked():
                self.create_log = True
            else:
                self.create_log = False
            
            if self.ui.checkbox_multi_sess.isChecked():
                self.multi_sess_selected = True
            else:
                self.multi_sess_selected = False

            starting_data = self.ui.box_starting_mess.text()
            starting_data = "".join(starting_data.split())
            if '/c/' in starting_data:
                self.ui.statusBar().showMessage(f'Private Group Detected')
                self.pri_group = True

            ending_data = self.ui.box_ending_mess.text()
            ending_data = "".join(ending_data.split())
            self.cu_session = self.ui.combobox_session.currentText()
            try:
                if starting_data == '':
                    pass
                elif 'https://t.me/' not in starting_data:
                    self.ui.statusBar().showMessage(
                        f'https://t.me/group_name/message_id is the correct format')
                else:
                    if '/c/' in starting_data:
                        starting_data = starting_data.replace('https://t.me/c/', '')
                        starting_data = "".join(starting_data.split())
                        starting_message = starting_data.split('/')
                        self.group_name = starting_message[0]
                        self.group_name = int(f'-100{self.group_name}')
                    else:
                        starting_data = starting_data.replace('https://t.me/', '')
                        starting_data = "".join(starting_data.split())
                        starting_message = starting_data.split('/')
                        self.group_name = starting_message[0]
                    self.group_starting = int(starting_message[1])

                    if ending_data != '' and 'https://t.me/' in ending_data:
                        if '/c/' in ending_data:
                            ending_data = ending_data.replace(
                                'https://t.me/c/', '')
                            ending_data = "".join(ending_data.split())
                            ending_message = ending_data.split('/')
                            self.group_name_2 = ending_message[0]
                            self.group_name_2 = int(f'-100{self.group_name_2}')
                        else:
                            ending_data = ending_data.replace('https://t.me/', '')
                            ending_data = "".join(ending_data.split())
                            ending_message = ending_data.split('/')
                            self.group_name_2 = ending_message[0]
                        self.group_ending = int(ending_message[1])+1

                    if ending_data != '' and self.group_name_2 != self.group_name:
                        self.ui.statusBar().showMessage(f'Starting and Ending Group is not the same!')
                    else:
                        self.client_starter()
            except Exception as e:
                print(e)
                self.ui.statusBar().showMessage(
                    f'Make sure the links are in correct format. Example: https://t.me/TestGroup/123456 or https://t.me/c/123456/123456')

    def datetime_parser(self):
        pass

    def disable_widgets(self):
        # disables widgets. used for if during multi
        # session run widgets are enabled prematurely 

        self.ui.table_widget_1.setRowCount(5)
        self.ui.table_widget_2.setRowCount(5)
        self.ui.Button_count.setEnabled(False)
        self.ui.button_create_sess.setEnabled(False)
        self.ui.button_send_code.setEnabled(False)
        self.ui.button_reload.setEnabled(False)
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)
        self.running = True
        self.counting = True
        self.finishing_log = False
        self.force_stop = 2

    def enable_widgets(self):
        #used to enable widgets once all done

        self.ui.Button_count.setEnabled(True)
        self.ui.button_create_sess.setEnabled(True)
        self.ui.button_send_code.setEnabled(True)
        self.ui.button_reload.setEnabled(True)
        if self.reload_pressed is True:
            self.ui.button_save.setEnabled(True)
            self.ui.button_remove.setEnabled(True)
            self.ui.button_add_user.setEnabled(True)
        self.group_name = ''
        self.group_name_2 = ''
        self.group_starting = 0
        self.group_ending = 0
        self.cu_session = ''
        self.running = False
        self.finishing_log = False
        self.force_stop = 3
        self.counting_time = 1
        self.cu_dots = ''

    def counting_label(self):
        #sets status bar label

        if self.ui.Button_count.isEnabled() == True:
            if self.running == True or self.finishing_log == True:
                self.disable_widgets()
        if self.cu_dots == '....':
            self.cu_dots = ''
        if self.counting_time == 0:
            self.cu_dots += '.'
            if self.counting == True and self.finishing_log == True:
                self.ui.statusBar().showMessage(f'Counting and Finishing Log{self.cu_dots}')

            elif self.counting == True and self.finishing_log == False:
                self.ui.statusBar().showMessage(f'Counting{self.cu_dots}')

            elif self.counting == False and self.finishing_log == True:
                self.ui.statusBar().showMessage(f'Finishing Log{self.cu_dots}')

            self.counting_time = 1
        else:
            self.counting_time -= 1
        
    def data_distributor(self, list_data):
        #distributes counting data to relevant widgets

        self.counting = True
        print(
            f'Bar Value: {list_data[0]}, Total Message: {list_data[1]}, Counter: {list_data[2]}')
        self.progress_bar(int(list_data[0]))
        self.label_changer(int(list_data[1]), int(list_data[2]))
        self.counting_label()

    def data_distributor_multi(self, list_data):
        #distributes counting data to relevant widgets
        #for multi session

        self.counting = True
        print(
            f'Bar Value: {list_data[0]}, Total Message: {list_data[1]}, Counter: {list_data[2]}')
        thread_number = int(list_data[3])
        self.cu_bar_value[thread_number] = int(list_data[0])
        self.cu_total_mess[thread_number] = int(list_data[1])
        self.cu_kpi_mess[thread_number] = int(list_data[2])

        bar_value = 0
        tot_mess = 0
        tot_kpi = 0

        for i in self.cu_bar_value:
            bar_value += self.cu_bar_value[i]

        if bar_value > 100:
            bar_value = 100

        for i in self.cu_total_mess:
            tot_mess += self.cu_total_mess[i]

        for i in self.cu_kpi_mess:
            tot_kpi += self.cu_kpi_mess[i]
        self.progress_bar(bar_value)
        self.label_changer(tot_mess, tot_kpi)
        self.counting_label()

    def progress_bar(self, num):
        self.ui.progressBar.setValue(num)

    def label_changer(self, num_1, num_2):
        self.ui.label_2.setText(f'Total Checked: {num_1}')
        self.ui.label_3.setText(f'KPI Counter: {num_2}')
        self.ui.label_2.adjustSize()
        self.ui.label_3.adjustSize()

    def total_mess_saver(self, user_data):
        #for counting total message including kpi

        user_id = int(user_data[0])
        mess_char = int(user_data[1])
        if user_id not in self.total_mess_char:
            self.total_mess_char[user_id] = mess_char
        else:
            self.total_mess_char[user_id] = self.total_mess_char[user_id] + mess_char

    def row_data_setter(self):
        #sets data to table widgets
        #once everything is calculated

        if self.running == True:
            pass
        else:
            self.row_timer.stop()
            for i in self.all_log_row:
                name = QtWidgets.QTableWidgetItem(str(self.all_log_row[i][0]))
                username = QtWidgets.QTableWidgetItem(str(self.all_log_row[i][1]))
                count = QtWidgets.QTableWidgetItem()
                count.setData(QtCore.Qt.DisplayRole, self.all_log_row[i][2])
                count.setTextAlignment(QtCore.Qt.AlignCenter)
                row_num = self.all_log_row[i][3]
                user_id = QtWidgets.QTableWidgetItem()
                user_id.setData(QtCore.Qt.DisplayRole, i)
                user_id.setTextAlignment(QtCore.Qt.AlignCenter)
                average_count = QtWidgets.QTableWidgetItem()
                average_count.setData(QtCore.Qt.DisplayRole, self.all_log_row[i][4])
                average_count.setTextAlignment(QtCore.Qt.AlignCenter)
                self.ui.table_widget_1.setItem(
                    row_num, 0, QtWidgets.QTableWidgetItem(name))
                self.ui.table_widget_1.setItem(
                    row_num, 1, QtWidgets.QTableWidgetItem(username))
                self.ui.table_widget_1.setItem(row_num, 2, count)
                self.ui.table_widget_1.setItem(row_num, 3, user_id)
                self.ui.table_widget_1.setItem(row_num, 4, average_count)

            for i in self.kpi_log_row:
                name = QtWidgets.QTableWidgetItem(str(self.kpi_log_row[i][0]))
                username = QtWidgets.QTableWidgetItem(str(self.kpi_log_row[i][1]))
                count = QtWidgets.QTableWidgetItem()
                count.setData(QtCore.Qt.DisplayRole, self.kpi_log_row[i][2])
                count.setTextAlignment(QtCore.Qt.AlignCenter)
                row_num = self.kpi_log_row[i][3]
                user_id = QtWidgets.QTableWidgetItem()
                user_id.setData(QtCore.Qt.DisplayRole, i)
                user_id.setTextAlignment(QtCore.Qt.AlignCenter)
                average_count = QtWidgets.QTableWidgetItem()
                average_count.setData(QtCore.Qt.DisplayRole, self.kpi_log_row[i][4])
                average_count.setTextAlignment(QtCore.Qt.AlignCenter)
                self.ui.table_widget_2.setItem(
                    row_num, 0, QtWidgets.QTableWidgetItem(name))
                self.ui.table_widget_2.setItem(
                    row_num, 1, QtWidgets.QTableWidgetItem(username))
                self.ui.table_widget_2.setItem(row_num, 2, count)
                self.ui.table_widget_2.setItem(row_num, 3, user_id)
                self.ui.table_widget_2.setItem(row_num, 4, average_count)

    def finishing(self, total_num):
        #final function once the session ends
        #either it will set proper numer/text to the widgets
        #or show the error message

        self.enable_widgets()
        if total_num[0] == 'incomplete':
            self.ui.total_2.setText(f'Total Message: 0')
            self.ui.total_1.setText(f'Total KPI: 0') 
            self.ui.statusBar().showMessage(
                'Incomplete Session. Please create one with Create Session button')
        else:
            self.finishing_data[total_num[2]] = [total_num[0], total_num[1]]
            new_all_num = 0
            new_kpi_num = 0
            for i in self.finishing_data:
                new_all_num += self.finishing_data[i][0]

            for i in self.finishing_data:
                new_kpi_num += self.finishing_data[i][1]
            self.ui.statusBar().clearMessage()
            self.ui.total_2.setText(f'Total Message: {new_all_num}')
            self.ui.total_1.setText(f'Total KPI: {new_kpi_num}')
            self.ui.table_widget_2.setRowCount(self.kpi_latest_row_num)
            self.ui.table_widget_1.setRowCount(self.all_latest_row_num)
            self.row_timer.start()

    def row_amount(self, data):
        #settting initial row to widgets
        self.counting = False
        self.ui.table_widget_1.setRowCount(5)
        self.ui.table_widget_2.setRowCount(5)

    def set_row_data(self, data):
        # gathers data for setting up on table widgets

        if self.ui.Button_count.isEnabled() == True:
            if self.running == True or self.finishing_log == True:
                self.disable_widgets()
        self.finishing_log = True
        self.counting_label() 
        if int(data[4]) in self.all_log_row:
            new_count = self.all_log_row[int(data[4])][2] + int(data[2])
            old_row = self.all_log_row[int(data[4])][3]
            self.all_log_row[data[4]] = [data[0], data[1], new_count, old_row]

        else:
            self.all_log_row[data[4]] = [data[0], data[1], int(data[2]), self.all_latest_row_num]
            self.all_latest_row_num += 1 

        try:
            average_char = int(self.total_mess_char[int(data[4])] / int(self.all_log_row[int(data[4])][2]))
            self.all_log_row[data[4]].append(average_char)
        except:
            average_char = 0
            self.all_log_row[data[4]].append(average_char)
        self.ui.table_widget_1.setRowCount(self.all_latest_row_num)

    def set_row_data_kpi(self, data):

        # gathers data for setting up on table widgets

        if int(data[4]) in self.kpi_log_row:
            new_count = self.kpi_log_row[int(data[4])][2] + int(data[2])
            old_row = self.kpi_log_row[int(data[4])][3]
            self.kpi_log_row[data[4]] = [data[0], data[1], new_count, old_row]
        else:
            self.kpi_log_row[data[4]] = [data[0], data[1], int(data[2]), self.kpi_latest_row_num]
            self.kpi_latest_row_num += 1 

        try:
            average_char = int(self.total_mess_char[int(data[4])] / int(self.kpi_log_row[int(data[4])][2]))
            self.kpi_log_row[data[4]].append(average_char)
        except:
            average_char = 0
            self.kpi_log_row[data[4]].append(average_char)
        self.ui.table_widget_2.setRowCount(self.kpi_latest_row_num)

    def mess_value_setter(self, mess_val):
        self.mess_value = mess_val

    def incom_sess(self, sess):
        #keeps track of incomplete sessions
        sess_name = sess.split(' is incomplete')[0]
        self.incomplete_sess.append(sess_name)

    def latest_mess_id(self, id_num):
        self.mess_id_latest = id_num
        self.thread_timer.setInterval(1000)

    def client_starter(self):
        #reset variables, table rows, labels
        #detects multi session or single session
        #and verifies whether a session is active
        self.reload_kpi()
        self.session_detector()
        self.disable_widgets()
        self.label_changer(0, 0)

        self.ui.total_2.setText(f'Total Message: 0')
        self.ui.total_1.setText(f'Total KPI: 0')

        while self.ui.table_widget_1.rowCount() > 0:
            self.ui.table_widget_1.removeRow(0)
        while self.ui.table_widget_2.rowCount() > 0:
            self.ui.table_widget_2.removeRow(0)
        self.ui.progressBar.setValue(0)
        self.mess_id_latest = 0
        self.all_latest_row_num = 0
        self.kpi_latest_row_num = 0
        self.total_mess_char = {}
        self.cu_bar_value = {}
        self.cu_total_mess = {}
        self.cu_kpi_mess = {}
        self.all_log_row = {}
        self.kpi_log_row = {}
        self.finishing_data = {}

        if self.multi_sess_selected == True:
            pool = QThreadPool.globalInstance()
            available_sess = self.session_list
            for i in available_sess:
                self.ui.statusBar().showMessage(f'Verifying Session {i}')
                self.worker = session_verifier(self.group_name, i, self.pri_group)
                self.worker.signal.incomplete_sess.connect(self.incom_sess)
                self.worker.signal.latest_mess.connect(self.latest_mess_id)
                pool.start(self.worker)
                
            try:
                self.thread_timer.timeout.disconnect()
            except:
                pass
            self.thread_timer.setInterval(5000)
            self.thread_timer.timeout.connect(self.multi_client)
            self.thread_timer.start()

        else:
            pool = QThreadPool.globalInstance()
            self.worker = session_verifier(self.group_name, self.cu_session, self.pri_group)
            self.worker.signal.incomplete_sess.connect(self.incom_sess)
            self.worker.signal.latest_mess.connect(self.latest_mess_id)
            pool.start(self.worker)
            self.ui.statusBar().showMessage(f'Verifying Session {self.cu_session}')
            try:
                self.thread_timer.timeout.disconnect()
            except:
                pass
            self.thread_timer.timeout.connect(self.single_client)
            self.thread_timer.setInterval(5000)
            self.thread_timer.start()

    def single_client(self):
        #for processing single session
        #verifies whether the session is good to go or
        #if private group is joined if selected

        if self.mess_id_latest != 0:
            self.thread_timer.stop()
        
        elif self.cu_session in self.incomplete_sess and self.pri_group == True:
            self.thread_timer.stop()
            self.ui.statusBar().showMessage(f'{self.cu_session} Incomplete Session or Private Group not joined')
            self.enable_widgets()
            return

        elif self.cu_session in self.incomplete_sess:
            self.thread_timer.stop()
            self.ui.statusBar().showMessage(f'Incomplete Session {self.cu_session}')
            self.enable_widgets()
            return

        else:
            print('Latest Message Not Found')
            self.thread_timer.setInterval(1000)
            return
        if self.group_ending != 0:
            self.mess_id_latest = self.group_ending
        else:
            self.mess_id_latest += 1

        message_value = 100 / (self.mess_id_latest - self.group_starting)
        threadCount = QThreadPool.globalInstance().maxThreadCount()
        pool = QThreadPool.globalInstance()
        for i in range(threadCount):
            
            self.worker = Worker(self.group_name, self.group_starting,
                             self.mess_id_latest,
                             self.cu_session, self.create_log, 1, 1, mess_value=message_value, multi_sess=False, max_bar=100)
            self.worker.signal.progress.connect(self.data_distributor)
            self.worker.signal.list_size.connect(self.row_amount)
            self.worker.signal.row_data.connect(self.set_row_data)
            self.worker.signal.row_data_2.connect(self.set_row_data_kpi)
            self.worker.signal.mess_char.connect(self.total_mess_saver)
            self.worker.signal.finished.connect(self.finishing)
            pool.start(self.worker)
            break
    
    def multi_client(self):
        #for processing multi session
        #verifies whether the session is good to go or
        #if private group is joined if selected
        #divides the part of each session and starts the
        #thread accordingly
        if self.mess_id_latest != 0:
            self.thread_timer.stop()

        elif self.session_list == self.incomplete_sess:
            self.ui.statusBar().showMessage(f'Could not work with any available session')
            self.thread_timer.stop()
            self.enable_widgets()
            return
        else:
            self.thread_timer.setInterval(1000)
            print('Latest Message Not Found')
            return
        pool = QThreadPool.globalInstance()
        threadCount = QThreadPool.globalInstance().maxThreadCount()
        available_sess = self.session_list

        for i in self.incomplete_sess:
            if i in available_sess:
                available_sess.remove(i)

        self.ui.statusBar().showMessage(f'Working with {len(available_sess)} sessions')
        thread_num = 0
        self.mess_id_latest += 1
        if int(self.group_ending) != 0:
            self.mess_id_latest = int(self.group_ending)
        else:
            self.group_ending = self.mess_id_latest

        total_counting = int((self.mess_id_latest - self.group_starting))
        part_value = int(total_counting/(len(available_sess)))
        print(part_value)
        print(total_counting)
        new_starting = self.group_starting
        parts_start = {}
        parts_end = {}

        for i in range(len(available_sess)-1, -1, -1):
            if i == len(available_sess)-1:
                parts_start[available_sess[i]] = new_starting
                parts_end[available_sess[i]] = new_starting + part_value
                new_starting += part_value
            
            elif i == 0:
                parts_start[available_sess[i]] = new_starting
                parts_end[available_sess[i]] = self.mess_id_latest
            else:
                parts_start[available_sess[i]] = new_starting
                new_starting += part_value
                parts_end[available_sess[i]] = new_starting
        
        message_value = 100 / (self.mess_id_latest - self.group_starting)
        final_part_value = 100
        for i in available_sess:
            thread_num += 1
            part_bar = int(100/len(available_sess))
            if i == available_sess[-1]:
                part_bar = final_part_value
            self.worker = Worker(self.group_name, parts_start[i],
                             parts_end[i],
                             i, self.create_log, thread_num, len(available_sess), mess_value=message_value, multi_sess=True, max_bar=part_bar)
            final_part_value -= part_bar
            self.worker.signal.progress.connect(self.data_distributor_multi)
            self.worker.signal.list_size.connect(self.row_amount)
            self.worker.signal.row_data.connect(self.set_row_data)
            self.worker.signal.row_data_2.connect(self.set_row_data_kpi)
            self.worker.signal.mess_char.connect(self.total_mess_saver)
            self.worker.signal.finished.connect(self.finishing)
            pool.start(self.worker)
            if thread_num >= int(threadCount):
                break

class worker_signals(QObject):
    #signal slots for communicating

    finished = pyqtSignal(list)
    progress = pyqtSignal(list)
    list_size = pyqtSignal(int)
    row_data = pyqtSignal(list)
    row_data_2 = pyqtSignal(list)
    mess_char = pyqtSignal(list)
    mess_value = pyqtSignal(object)
    latest_mess = pyqtSignal(int)
    incomplete_sess = pyqtSignal(str)

class Worker(QRunnable):
    def __init__(self, group_name, group_starting,
                 group_ending, session_name, create_log, 
                 thread_num, total_thread, mess_value=0, multi_sess=False, max_bar=0):
        super().__init__()
        self.pending = 0
        self.cu_session = session_name
        self.last_id = group_ending
        self.group_ending = group_ending
        self.group_name = group_name
        self.group_starting = group_starting
        self.total_mess = 0
        self.counter = 0
        self.mess_value = mess_value
        self.bar = 0
        self.pending_message = 0
        self.message_data = {}
        self.row_number_all = 0
        self.row_number_kpi = 0
        self.create_log = create_log
        self.thread_num = thread_num
        self.total_thread = total_thread
        self.multi_sess = multi_sess
        self.max_bar = max_bar
        self.signal = worker_signals()
        print(self.group_name, self.group_starting, self.group_ending, self.thread_num)

    @pyqtSlot()
    def run(self):
        async def kpi_counter():
            global stop_process
            client = TelegramClient(self.cu_session, api_id, api_hash)
            await client.connect()
            me = await client.get_me()
            print(self.cu_session)
            if me == 'None' or me is None:
                print('Session incomplete')
                self.signal.finished.emit(['incomplete', 'incomplete', self.thread_num])

            else:
                async with client:
                    #start iterating fromt the selected message links
                    async for message in client.iter_messages(self.group_name,
                                        offset_id=self.group_ending):

                        if stop_process == True:
                            #for stopping the thread during processing
                            return

                        if int(message.id) < self.group_starting:
                            if self.pending > self.max_bar:
                                pass
                            else:
                                self.pending = self.max_bar
                            self.total_mess += self.last_id - self.group_starting
                            break
                            
                        elif message.id > self.group_ending:
                            pass

                        else:
                            try:
                                try:

                                    #for keeping track of message data by each user
                                    mess_sender = message.from_id.user_id
                                    if mess_sender in self.message_data:
                                        self.message_data[mess_sender] = self.message_data[mess_sender] + 1
                                    elif mess_sender not in self.message_data:
                                        self.message_data[mess_sender] = 1

                                    if int(message.id) == self.group_starting: 
                                        
                                        if self.pending > self.max_bar:
                                            pass
                                        else:
                                            self.pending += self.max_bar

                                        self.total_mess += self.last_id - self.group_starting

                                        try:
                                            if message.from_id.user_id in accounts:
                                                self.counter += 1
                                        except Exception as e:
                                            print(e)
                                        break

                                    else:
                                        self.pending += self.mess_value * (self.last_id - message.id)
                                        self.total_mess += self.last_id - message.id
                                        self.last_id = message.id
                                        self.pending_message += 1

                                        try:
                                            if message.from_id.user_id in accounts:
                                                self.counter += 1
                                        except Exception as e:
                                            print(e)

                                    if self.pending > 1:
                                        if self.bar != self.max_bar:
                                            self.bar += int(self.pending)
                                        if self.bar > 100:
                                            self.bar = 100
                                        self.pending = self.pending - int(self.pending)
                                        self.signal.progress.emit(
                                            [self.bar, self.total_mess,
                                            self.counter, self.thread_num])
                                        await asyncio.sleep(0.02)
                                        #small sleep time for qt animation
                                        #change to work a bit more smoothly

                                    elif self.pending_message > 5:
                                        self.signal.progress.emit(
                                            [self.bar, self.total_mess,self.counter, self.thread_num])
                                        self.pending_message = 0
                                        await asyncio.sleep(0.02)

                                except Exception as e:
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                    #print(exc_type, fname, exc_tb.tb_lineno, e)


                                try:
                                    mess_text = message.message
                                    mess_len = len(str(mess_text))
                                    if mess_len == 0:
                                        mess_len = 1    #if it's a sticker len is going to be 0, so make it 1
                                    self.signal.mess_char.emit([message.from_id.user_id, mess_len])
                                except Exception as e:
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                    #print(exc_type, fname, exc_tb.tb_lineno, e)

                                
                            except Exception as e:
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                #print(exc_type, fname, exc_tb.tb_lineno, e)

                    if self.bar > self.max_bar:
                        pass
                    elif self.bar != self.max_bar and self.multi_sess == False:
                        self.bar = self.max_bar
                    
                    elif self.bar != self.max_bar and self.multi_sess == True:
                            self.bar = self.max_bar

                    self.signal.progress.emit(
                        [self.bar, self.total_mess, self.counter, self.thread_num])

                    total_all = 0
                    total_kpi = 0
                    self.message_data = dict(
                        sorted(self.message_data.items(),
                            key=lambda item: item[1]))

                    if self.create_log is True:
                        self.signal.list_size.emit(len(self.message_data))

                        for sender in self.message_data:
                            #goes through previously collected user data for log
                            if stop_process == True:
                                return
                            try:
                                entity = await client.get_entity(sender)
                                id_num = entity.id
                                username = entity.username
                                first_name = entity.first_name
                                last_name = entity.last_name
                                full_name = f'{first_name}'
                                if last_name is not None:
                                    full_name += f' {last_name}'
                                total_all += self.message_data[sender]
                                print(full_name, username,
                                    self.message_data[sender])
                                row_data = [
                                    full_name, username,
                                    self.message_data[sender],
                                    self.row_number_all, id_num]
                                self.row_number_all += 1
                                self.signal.row_data.emit(row_data)

                                if sender in accounts:
                                    row_data = [
                                        full_name, username,
                                        self.message_data[sender],
                                        self.row_number_kpi, id_num]
                                    self.row_number_kpi += 1
                                    self.signal.row_data_2.emit(row_data)
                                    total_kpi += self.message_data[sender]
                            except Exception as e:
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                #print(exc_type, fname, exc_tb.tb_lineno, e)

                    self.signal.finished.emit([total_all, total_kpi, self.thread_num])
                    await client.disconnect()
                    try:
                        await client.disconnected
                    except OSError:
                        print('Error on disconnect')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(kpi_counter())

class session_verifier(QRunnable):
    def __init__(self, group_name, session_name, private_group):
        super().__init__()
        self.pending = 0
        self.cu_session = session_name
        self.group_name = group_name
        self.private_group = private_group
        self.signal = worker_signals()

    @pyqtSlot()
    def run(self):
        async def verifier():
            try:
                client = TelegramClient(self.cu_session, api_id, api_hash)
                await client.connect()
                me = await client.get_me()
                if me == 'None' or me is None:
                    print('Session incomplete')
                    self.signal.incomplete_sess.emit(f'{self.cu_session} is incomplete')

                else:
                    #verifies session whether it can be used for counting
                    async with client:
                        if self.private_group == True:
                            group_list = []
                            async for group in client.iter_dialogs():
                                group_list.append(group.id)

                        if self.private_group == True and self.group_name in group_list:
                            async for message in client.iter_messages(self.group_name):
                                self.signal.latest_mess.emit(message.id)
                                print(message.id)
                                break

                        elif self.private_group == True and self.group_name not in group_list:
                            print('Not joined in the Private Group')
                            self.signal.incomplete_sess.emit(f'{self.cu_session} is incomplete')
                        
                        elif self.private_group == False:
                            async for message in client.iter_messages(self.group_name):
                                self.signal.latest_mess.emit(message.id)
                                print(message.id)
                                break

                await client.disconnect()
                try:
                    await client.disconnected
                except Exception:
                    print('Error on disconnect')
            except Exception:
                pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(verifier())


app = QApplication(sys.argv)
w = main_form()
w.show()
sys.exit(app.exec_())
