import sys
import os
import pyperclip
import requests
import webbrowser
import datetime
from threading import Thread
from PyQt5 import uic
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QLineEdit, \
    QMainWindow, QMessageBox, QAction, QDesktopWidget, \
    QPushButton, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QWidgetAction
from PyQt5.QtCore import QRunnable, QThread, pyqtSignal, \
    QObject, Qt, QTimer, QThreadPool, pyqtSlot, QDate
from PyQt5.QtGui import *
from telethon import TelegramClient
import asyncio
import pickle
from session_creator import *
from id_manager import *
from Chart_Design import *

#[x]switch to pyqtgraph
#[x]add a crosshair
#[x]show value of x and y on hover
#[x]ability to show both hourly and day based chart
#[x]allow user_id/username to be added separately to the chart
#[x]change legend names
#[x]if hourly chart selected, show hours on top of the chart
#[x] add color order for each button pre-set
#[x] when addding to chart, make index 0 the furthest left available button
#[x] send proper data when counting by hours
#[ ] test worker class for entity getting
#[x] avoid doing entity for the same user twice, global variable
#[x] same user going twice in add user combobox with multi_session
#[ ] code number has expired error message
#[ ] keep a default useless api_id and hash and remove extra buttons from session creator
#[ ] session name cannot be empty
#[x] check people joining message, uncount them
#[x] if no user is added to charts, don't respond to hourly or daily changes
#[ ] if same value selected + not in chart does not work
#[x] multi session date not detecting latest message and dividing properly, wait until all sessions are either rejected or complete
#[x] chart showing inaccurate KPI number
#[x] copy function not working in kde. Find a different library
#[ ] change button/chart colors to something that does not match with existing ones
#[x] mult session not working properly for charts
#[x] change legend to names
#[x] limit chart button and legend length to 15
#[ ] add exit prompt only if counting
#[x] add user name on tooltip
#[x] set all button text to empty on count
#[ ] pre-save all needed data from message in variable at the beginning
#[ ] count peer_channel messages as the channel name

version = 'v2.1'
new_version = ''
stop_process = False
verified_entities = {}

def version_check():  # for checking new releases on github
    global new_version
    try:
        response = requests.get(
            "https://api.github.com/repos/Sakib0194/Telecounter/releases/latest")
        new_version = response.json()["name"]
    except:
        new_version = 'v2.1'

Thread(target=version_check).start()

api_id = 1234567
api_hash = 'test'

if os.path.exists('resource/kpi_id.pckl'):
    pass
else:
    data_store = open('resource/kpi_id.pckl', 'wb')
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
        self.log_chart = create(self.ui)
        self.group_name = ''
        self.group_name_2 = ''
        self.cu_session = ''
        self.worker = ''
        self.cu_dots = ''
        self.box_selected = ''
        self.starting_date = ''
        self.ending_date = ''

        self.group_starting = 0
        self.group_ending = 0
        self.all_latest_row_num = 0
        self.kpi_latest_row_num = 0
        self.force_stop = 2
        self.counting_time = 1
        self.mess_value = 0
        self.mess_id_latest = 0
        self.time_difference = 0
        
        self.create_log = True
        self.multi_sess_selected = False
        self.reload_pressed = False
        self.starting_paste = True
        self.ending_paste = True
        self.pri_group = False
        self.running = False
        self.finishing_log = False
        self.counting = False
        self.add_time = False

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
        self.date_counts = {}
        self.date_counts_kpi = {}
        self.date_hour_counts = {}
        self.date_hour_counts_kpi = {}
        self.user_date_counts = {}
        self.user_date_hour_counts = {}
        self.added_in_chart = {}
        self.added_in_chart_reverse = {}
        self.user_selections = {}
        self.user_id_name = {}
        self.chart_button_color = {self.ui.chart_button_1 : 'blue', self.ui.chart_button_2 : (199, 0, 57), self.ui.chart_button_3 : (194, 221, 147),
                self.ui.chart_button_4 : (222, 194, 179), self.ui.chart_button_5 : (154, 101, 255), self.ui.chart_button_6 : (72, 228, 143), 
                self.ui.chart_button_7 : (255, 195, 0), self.ui.chart_button_8 : (147, 157, 221), self.ui.chart_button_9 : (59, 228, 202), 
                self.ui.chart_button_10 : (238, 255, 11)}
        self.chart_button_color_rgb = {self.ui.chart_button_1 : 'blue', self.ui.chart_button_2 : '#C70039', self.ui.chart_button_3 : '#C2DD93',
                self.ui.chart_button_4 : '#DEC2B3', self.ui.chart_button_5 : '#9A65FF', self.ui.chart_button_6 : '#48E48F', 
                self.ui.chart_button_7 : '#FFC300', self.ui.chart_button_8 : '#939DDD', self.ui.chart_button_9 : '#3BE4CA', 
                self.ui.chart_button_10 : '#EEFF0B'}
        
        self.incomplete_sess = []
        self.complete_sess = []
        self.session_list = []
        self.empty_buttons = []
        self.added_users = []
        self.already_in_chart = []

        self.button_calender_1 = QPushButton(self.ui.box_starting_mess)
        self.button_calender_3 = QPushButton(self.ui.box_ending_date)

        self.today = datetime.datetime.today().strftime('%Y %m %d').split(' ')
        
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
        self.button_calender_3.clicked.connect(self.ui.calender_display_3)
        self.ui.calender.selectionChanged.connect(self.calender_event)
        QApplication.instance().focusChanged.connect(self.focus_change)
        self.ui.table_widget_2.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.ui.table_widget_2.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.ui.table_widget_1.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.ui.table_widget_1.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.ui.listWidget.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.ui.listWidget.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.ui.chart_type.currentIndexChanged.connect(self.chart_type_changed)
        self.ui.add_user_box.currentTextChanged.connect(self.adding_to_chart)
        self.ui.chart_button_1.clicked.connect(lambda state, x=self.ui.chart_button_1: self.deleting_chart_value(x))
        self.ui.chart_button_2.clicked.connect(lambda state, x=self.ui.chart_button_2: self.deleting_chart_value(x))
        self.ui.chart_button_3.clicked.connect(lambda state, x=self.ui.chart_button_3: self.deleting_chart_value(x))
        self.ui.chart_button_4.clicked.connect(lambda state, x=self.ui.chart_button_4: self.deleting_chart_value(x))
        self.ui.chart_button_5.clicked.connect(lambda state, x=self.ui.chart_button_5: self.deleting_chart_value(x))
        self.ui.chart_button_6.clicked.connect(lambda state, x=self.ui.chart_button_6: self.deleting_chart_value(x))
        self.ui.chart_button_7.clicked.connect(lambda state, x=self.ui.chart_button_7: self.deleting_chart_value(x))
        self.ui.chart_button_8.clicked.connect(lambda state, x=self.ui.chart_button_8: self.deleting_chart_value(x))
        self.ui.chart_button_9.clicked.connect(lambda state, x=self.ui.chart_button_9: self.deleting_chart_value(x))
        self.ui.chart_button_10.clicked.connect(lambda state, x=self.ui.chart_button_10: self.deleting_chart_value(x))
        

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
        self.ui.box_ending_date.hide()
        
        self.ui.calender.setMaximumDate(QDate(int(self.today[0]), int(self.today[1]), int(self.today[2])))
        self.ui.calender.setSelectedDate(QDate(int(self.today[0]), int(self.today[0]), 1))

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

        self.button_calender_3.setText('📅')
        self.button_calender_3.setCursor(Qt.ArrowCursor)
        actions = QWidgetAction(self.button_calender_3)
        actions.setDefaultWidget(self.button_calender_3)
        self.ui.box_ending_date.addAction(actions, QLineEdit.TrailingPosition)

    def show_date_box(self):
        self.ui.calender.show()
        self.ui.resize(628, 588) 
        self.ui.box_ending_date.setMinimumSize(174, 35)
        self.ui.box_ending_date.setMaximumSize(16777215, 35)
        self.ui.box_starting_mess.setMinimumSize(174, 35)
        self.ui.box_ending_date.resize(174, 35)
        self.ui.box_starting_mess.resize(174, 35)
        self.button_clear_1.setText('Clear')
        self.ui.box_starting_mess.setPlaceholderText('Starting Date')
        self.ui.box_ending_date.setPlaceholderText('Ending Date')
        self.ui.box_ending_mess.setPlaceholderText('Group Username/Link')
        self.ui.box_ending_date.show()
        self.ui.label.setText('Start And End Date')
        self.ui.label_10.setText('Group Username/Link')
        self.ui.box_starting_mess.setToolTip('Counting will start at the beginning of this date')
        self.ui.box_ending_date.setToolTip('Counting will stop at the beginning of this date')
        self.ui.box_ending_mess.setToolTip('Counting will happen at this group')

    def remove_date_box(self):
        self.ui.calender.hide()
        self.ui.resize(628, 325) 
        self.ui.box_ending_date.hide()
        self.ui.box_ending_date.clear()
        self.ui.box_starting_mess.clear()
        self.ui.box_starting_mess.setMinimumSize(350, 35)
        self.ui.box_ending_date.setMaximumSize(0, 35)
        self.ui.button_clear_1.show()
        self.ui.label.setText('Starting Message Link')
        self.ui.label_10.setText('Ending Message Link')
        self.ui.box_starting_mess.setPlaceholderText('Necessary: Message Link To Start From')
        self.ui.box_ending_mess.setPlaceholderText('Optional: Message Link to End At')
        if self.ui.box_starting_mess.text() == '':
            self.button_clear_1.setText('Paste')
            self.starting_paste = True
        else:
            self.button_clear_1.setText('Clear')
            self.starting_paste = False
        self.ui.box_starting_mess.setToolTip('Start count from this essage ink')
        self.ui.box_ending_mess.setToolTip('End count from this essage ink')
        self.ui.setMinimumSize(0,0) 
        self.ui.resize(628, 325) 

    def box_decider(self):
        starting_mess_text = self.ui.box_starting_mess.text()
        ending_date_text = self.ui.box_ending_date.text()
        date_entered = False

        if len(ending_date_text.split('-')) == 3:
            date_entered = True
        
        elif len(starting_mess_text.split('-')) == 3 and self.ui.box_ending_date.isVisible():
            date_entered = True

        else:
            date_entered = False

        if date_entered == True:
            pass
        else:
            if self.ui.box_ending_date.isVisible():
                self.remove_date_box()
            else:
                self.show_date_box()

    def calender_display_1(self):
        if self.ui.calender.isVisible():
            self.ui.calender.hide()
            self.ui.setMinimumSize(0,0) 
            self.ui.resize(628, 325) 
            self.box_selected = '' 
            self.box_decider()

        else:
            self.ui.resize(628, 588) 
            self.ui.calender.show() 
            self.box_selected = 'box_starting_mess'
            self.ui.box_starting_mess.setFocus()
            selected_date = self.ui.calender.selectedDate().toString("dd-MM-yyyy")
            self.ui.box_starting_mess.clear()
            self.ui.box_starting_mess.setText(selected_date)
            self.box_decider()

    def calender_display_3(self):
        if self.ui.calender.isVisible():
            self.ui.calender.hide()
            self.ui.setMinimumSize(0,0) 
            self.ui.resize(628, 325) 
            self.box_selected = '' 
            self.box_decider()
            
        else:
            self.ui.resize(628, 588) 
            self.ui.calender.show()
            self.box_selected = 'box_starting_mess'
            self.ui.box_starting_mess.setFocus()
            selected_date = self.ui.calender.selectedDate().toString("dd-MM-yyyy")
            self.ui.box_starting_mess.clear()
            self.ui.box_starting_mess.setText(selected_date)
            self.box_decider()

    def focus_change(self, old, new):
        try:
            new_widg = new.objectName()
            if new_widg == 'box_starting_mess' or new_widg == 'box_ending_date':
                self.box_selected = new_widg
        except:
            pass
        
    def sort_empty_buttons(self):
        self.empty_buttons = []
        for i in self.chart_button_color:
            if i in self.added_in_chart:
                pass
            else:
                self.empty_buttons.append(i)

    def calender_event(self):
        selected_date = self.ui.calender.selectedDate().toString("dd-MM-yyyy")
        if self.box_selected != '':
            if self.box_selected == 'box_starting_mess':
                self.ui.box_starting_mess.clear()
                self.ui.box_starting_mess.setText(selected_date)
                self.ui.box_starting_mess.setFocus()

            elif self.box_selected == 'box_ending_date':
                self.ui.box_ending_date.clear()
                self.ui.box_ending_date.setText(selected_date)
                self.ui.box_ending_date.setFocus()

    def check_update(self):  # for opening the new version available window
        print('Current Version', version)
        version_num = float(version.split('v')[1])
        new_version_num = float(new_version.split('v')[1])  #error here
        if version_num < new_version_num:
            self.w = version_form()
            self.w.show()
        self.timer.stop()

    def empty_statusbar(self): #clear status bar message
        self.clear_statusbar.stop()
        self.ui.statusBar().clearMessage()

    def sorting_event_1(self):  #triggered when clicking on table column buttons for sorting
        self.ui.table_widget_1.clearSelection()
    
    def sorting_event_2(self):  #triggered when clicking on table column buttons for sorting
        self.ui.table_widget_2.clearSelection()

    def deleting_chart_value(self, button_name):
        if button_name in self.added_in_chart:
            self.already_in_chart.remove(self.added_in_chart[button_name])
            del self.added_in_chart[button_name]
            self.added_in_chart_reverse = {v: k for k, v in self.added_in_chart.items()}
            self.empty_buttons.append(button_name)
            button_name.setText('Empty')
            self.sort_empty_buttons()
            self.reload_charts_router()

    def adding_to_chart(self, user):
        if user == '':
            pass
        else:
            sel_value = self.user_selections[user]
            if sel_value in self.already_in_chart:
                pass

            else:
                if self.empty_buttons == []:
                    pass
                else:
                    taking_button = self.empty_buttons[0]
                    if len(user) > 15:
                        user = f'{user[:15]}...'
                    taking_button.setText(user)
                    self.empty_buttons.remove(taking_button)
                    self.added_in_chart[taking_button] = sel_value
                    self.added_in_chart_reverse = {v: k for k, v in self.added_in_chart.items()}
                    self.already_in_chart.append(sel_value)
                    self.sort_empty_buttons()
                    self.reload_charts_router()
                
    def reload_charts_router(self):
        cu_chart_type = self.ui.chart_type.currentIndex()
        
        if cu_chart_type == 1:
            self.reload_charts_hour()

        elif cu_chart_type == 0:
            self.reload_charts_date()
        
    def reload_charts_date(self):

        #if valued added or taken this function is called
        #this one checks what buttons were added in the charts
        #and sends relevant data to the chart designer 

        other_values = []
        kpi_mess_found = False
        all_mess_found = False

        for i in self.added_in_chart:
    
            if self.added_in_chart[i] == 'KPI Count':
                kpi_mess_found = True

            elif self.added_in_chart[i] == 'All Count':
                all_mess_found = True

            else:
                other_values.append(self.added_in_chart[i])

        self.log_chart.remove_widget()
        
        self.log_chart.create_chart(data=self.date_counts, kpi_data=self.date_counts_kpi, 
                    user_data=self.user_date_counts, kpi_selected=kpi_mess_found, all_selected=all_mess_found, 
                    users_to_check=other_values, button_colors=self.chart_button_color, 
                    chart_used_buttons=self.added_in_chart_reverse, user_names=self.user_id_name,
                    rgb_colors=self.chart_button_color_rgb)
                            
    def reload_charts_hour(self):
        other_values = []
        kpi_mess_found = False
        all_mess_found = False

        for i in self.added_in_chart:
    
            if self.added_in_chart[i] == 'KPI Count':
                kpi_mess_found = True

            elif self.added_in_chart[i] == 'All Count':
                all_mess_found = True

            else:
                other_values.append(self.added_in_chart[i])

        self.log_chart.remove_widget()
        
        self.log_chart.create_chart(self.date_hour_counts, self.date_hour_counts_kpi,
                    self.user_date_hour_counts, hourly=True, kpi_selected=kpi_mess_found, all_selected=all_mess_found, 
                    users_to_check=other_values, button_colors=self.chart_button_color, 
                    chart_used_buttons=self.added_in_chart_reverse, user_names=self.user_id_name,
                    rgb_colors=self.chart_button_color_rgb)

    def chart_type_changed(self, event):
        #sends event here when the combo box for changing chart type
        #current selected value changes

        if event == 1:
            self.reload_charts_hour()

        elif event == 0:
            self.reload_charts_date()
            
    def set_button_empty(self):
        self.ui.chart_button_1.setText('empty')
        self.ui.chart_button_2.setText('empty')
        self.ui.chart_button_3.setText('empty')
        self.ui.chart_button_4.setText('empty')
        self.ui.chart_button_5.setText('empty')
        self.ui.chart_button_6.setText('empty')
        self.ui.chart_button_7.setText('empty')
        self.ui.chart_button_8.setText('empty')
        self.ui.chart_button_9.setText('empty')
        self.ui.chart_button_10.setText('empty')

    def cell_copier(self):  #copies cells selected in the table widget
        self.all_cell_selected = {} 
        self.kpi_cell_selected = {}
        self.largest_text_all = {}
        self.largest_text_kpi = {}

        #format {row{column:value}}
        #keeping track of row and column so they can be sorted numerically
        #sorting is necessary because selectedItems is created by keeping row/column
        #in mind. Sort happens by row => column order

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
                cb = QApplication.clipboard()
                cb.clear(mode=cb.Clipboard)
                cb.setText(full_text, mode=cb.Clipboard)
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
        self.ui.resize(628, 325) 
        self.ui.setMinimumSize(0,0)
        self.ui.resize(628, 325)  

        if self.ui.tabWidget.currentIndex() == 1:
            self.resize(1060, 400)
        elif self.ui.tabWidget.currentIndex() == 2:
            self.resize(700, 550)
        else:
            self.ui.resize(628, 325) 

    def text_changed_starting(self):
        # if text box empty, paste from clipboard on click
        # if text box has text, clear box on click

        text = self.ui.box_starting_mess.text()
        if self.ui.box_ending_date.isVisible():
            self.ui.button_clear_1.setText('Clear')
            self.starting_paste = False
        else:
            if text == '':
                self.ui.button_clear_1.setText('Paste')
                self.starting_paste = True
            else:
                self.ui.button_clear_1.setText('Clear')
                self.starting_paste = False

    def text_changed_ending(self):
        # if text box empty, paste from clipboard on click
        # if text box has text, clear box on click

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
        if self.ui.box_ending_date.isVisible():
            self.ui.box_starting_mess.clear()
            self.ui.box_ending_date.clear()
        
        else:
            if self.starting_paste is True:
                self.ui.box_starting_mess.setText(str(pyperclip.paste()))
            else:
                self.ui.box_starting_mess.clear()

    def edit_box_2(self):   #Paste/Clear button on Message Box
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
            #send to datetime parsing if a date was entered

        else:
            self.cu_timezone()
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
            if '/c/' in starting_data:  #/c/ is included in private group links
                self.ui.statusBar().showMessage(f'Private Group Detected')
                self.pri_group = True

            ending_data = self.ui.box_ending_mess.text()
            ending_data = "".join(ending_data.split())  #to prevent any spacing mistake
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
                    
                    elif self.group_starting > self.group_ending and self.group_ending != 0:
                        self.ui.statusBar().showMessage(f'Starting Message ID cannot be bigger than ending message ID')

                    elif self.group_starting == self.group_ending-1:
                        self.ui.statusBar().showMessage(f'Starting and Ending Message ID cannot be the same!')
                    else:
                        self.client_starter()
            except Exception as e:
                print(e)
                self.ui.statusBar().showMessage(
                    f'Make sure the links are in correct format. Example: https://t.me/TestGroup/123456 or https://t.me/c/123456/123456')

    def datetime_parser(self):
        self.starting_date = self.ui.box_starting_mess.text().split('-')
        self.starting_date = datetime.datetime(int(self.starting_date[2]), int(self.starting_date[1]), int(self.starting_date[0]))
        self.ending_date = self.ui.box_ending_date.text().split('-')

        self.cu_timezone()

        #add or take time to match the user's Telegram app

        if self.add_time == True:
            self.starting_date += datetime.timedelta(minutes=self.time_difference)
        else:
            self.starting_date -= datetime.timedelta(minutes=self.time_difference)

        self.group_name = self.ui.box_ending_mess.text()
        self.cu_session = self.ui.combobox_session.currentText()

        if self.ui.checkbox_multi_sess.isChecked():
            self.multi_sess_selected = True
        else:
            self.multi_sess_selected = False

        if self.ui.check_create_log.isChecked():
                self.create_log = True
        else:
            self.create_log = False

        if self.ending_date == ['']:
            self.ending_date = datetime.datetime.today()
        else:
            self.ending_date = datetime.datetime(int(self.ending_date[2]), int(self.ending_date[1]), int(self.ending_date[0]))

        self.ending_date += datetime.timedelta(days=1)

        if self.add_time == True:
            self.ending_date += datetime.timedelta(minutes=self.time_difference)
        else:
            self.ending_date -= datetime.timedelta(minutes=self.time_difference)
        
        if '/c/' in self.group_name:
            self.ui.statusBar().showMessage(f'Private Group Detected')
            self.pri_group = True
            self.group_name = self.group_name.replace('https://t.me/c/', '')
            self.group_name = "".join(self.group_name.split())

        elif 't.me' in self.group_name:
            self.group_name = self.group_name.replace('https://t.me/', '')
            self.group_name = "".join(self.group_name.split())
    
        if '/' in self.group_name:
            self.group_name = self.group_name.split('/')[0]
        
        elif '@' in self.group_name:
            self.group_name = self.group_name.split('@')[1]

        if self.starting_date == self.ending_date:
            self.ui.statusBar().showMessage('Start and Ending date cannot be the same')

        elif self.starting_date > self.ending_date:
            self.ui.statusBar().showMessage('Start date cannot be smaller than ending date')
        elif self.group_name == '':
            self.ui.statusBar().showMessage('Group Username cannot be empty')
        else:
            self.client_starter()

    def cu_timezone(self):
        now = datetime.datetime.now()
        local_now = now.astimezone()
        local_tz = local_now.tzinfo
        local_tzname = local_tz.tzname(local_now)

        if '+' in local_tzname:
            self.add_time = True
        else:
            self.add_time = False
        
        #add or remove time based on time zone
        #default time is UTC +0. If not done

        local_tzname = local_tzname.replace('+', '')    
        local_tzname = local_tzname.replace('-', '')
        local_tzname = int("".join(local_tzname.split()))
        self.time_difference = local_tzname * 60

    def date_messages(self, data):
        #date count history to pass to the designer
        #0 = All Message Day Based Data Format: {date:amount}
        #1 = KPI Message Day Based Data Format: {date:amount}
        #2 = All Message Hour Based Data Format: {hour:amount}
        #3 = KPI Message Hour Based Data Format: {hour:amount}
        #4 = User Message Day Based Data Format: {date:{user:amount}}
        #5 = User Message Hour Based Data Format {hour:{user:amount}}

        for i in data[0]:
            if i in self.date_counts:
                self.date_counts[i] += data[0][i]
            else:
                self.date_counts[i] = data[0][i]

        for i in data[1]:
            if i in self.date_counts_kpi:
                self.date_counts_kpi[i] += data[1][i]
            else:
                self.date_counts_kpi[i] = data[1][i]

        for i in data[2]:
            if i in self.date_hour_counts:
                self.date_hour_counts[i] += data[2][i]
            else:
                self.date_hour_counts[i] = data[2][i]

        for i in data[3]:
            if i in self.date_hour_counts_kpi:
                self.date_hour_counts_kpi[i] += data[3][i]
            else:
                self.date_hour_counts_kpi[i] = data[3][i]

        for i in data[4]:
            if i in self.user_date_counts:
                pass
            else:
                self.user_date_counts[i] = {}
            for u in data[4][i]:
                if u in self.user_date_counts[i]:
                    self.user_date_counts[i][u] += data[4][i][u]
                else:
                    self.user_date_counts[i][u] = data[4][i][u]

        for i in data[5]:
            if i in self.user_date_hour_counts:
                pass
            else:
                self.user_date_hour_counts[i] = {}
            for u in data[5][i]:
                if u in self.user_date_hour_counts[i]:
                    self.user_date_hour_counts[i][u] += data[5][i][u]
                else:
                    self.user_date_hour_counts[i][u] = data[5][i][u]

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
        self.ui.chart_type.setCurrentIndex(0)
        self.ui.chart_type.setEnabled(False)
        self.ui.add_user_box.setEnabled(False)
        self.running = True
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
        self.ui.chart_type.setEnabled(True)
        self.ui.add_user_box.setEnabled(True)
        self.group_name = ''
        self.group_name_2 = ''
        self.group_starting = 0
        self.group_ending = 0
        self.starting_date = ''
        self.ending_date = ''
        self.cu_session = ''
        self.running = False
        self.finishing_log = False
        self.force_stop = 3
        self.counting_time = 1
        self.cu_dots = ''
        self.incomplete_sess = []
        self.complete_sess = []

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

        #the value goes negative when there is a lack of messages/counting
        #so make it zero 

        if int(list_data[1]) <= -1: 
            self.label_changer(0, 0)
        else:
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

        #the value goes negative when there is a lack of messages/counting
        #so make it zero 
        
        for i in self.cu_total_mess:
            if self.cu_total_mess[i] <= -1:
                pass
            else:
                tot_mess += self.cu_total_mess[i]

        for i in self.cu_kpi_mess:
            tot_kpi += self.cu_kpi_mess[i]
        self.progress_bar(bar_value)

        if tot_mess <= -1:
            self.label_changer(0, 0)
        else:
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
            self.enable_widgets()
            self.row_timer.stop()
            try:
                self.log_chart.remove_widget()
                self.added_in_chart[self.ui.chart_button_1] = 'All Count'
                self.added_in_chart[self.ui.chart_button_6] = 'KPI Count'
                self.added_in_chart_reverse = {v: k for k, v in self.added_in_chart.items()}
                self.ui.chart_button_1.setText('All Count')
                self.ui.chart_button_6.setText('KPI Count')
                self.already_in_chart = ['All Count', 'KPI Count']
                self.log_chart.create_chart(self.date_counts, self.date_counts_kpi, self.user_date_counts, button_colors=self.chart_button_color, 
                            chart_used_buttons=self.added_in_chart_reverse, user_names=self.user_id_name,
                            rgb_colors=self.chart_button_color_rgb)
                self.empty_buttons.remove(self.ui.chart_button_1)
                self.empty_buttons.remove(self.ui.chart_button_6)
            except:
                pass

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
            
        elif total_num[0] == 'error':
            self.ui.total_2.setText(f'Total Message: 0')
            self.ui.total_1.setText(f'Total KPI: 0') 
            self.ui.statusBar().showMessage(
                total_num[1])
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

    def latest_mess_id(self, id_session):
        self.mess_id_latest = id_session[0]
        self.complete_sess.append(id_session[1])
        self.thread_timer.setInterval(500)

    def date_message_id(self, id_nums):
        if self.group_starting == 0:
            self.group_starting = id_nums[0]
        elif self.group_starting != 0 and id_nums[0] < self.group_starting:
            self.group_starting = id_nums[0]
        
        if self.group_ending == 0:
            self.group_ending = id_nums[1]
        elif self.group_ending != 0 and id_nums[1] > self.group_ending:
            self.group_ending = id_nums[1]

    def counted_users(self, users):
        #adds to the combobox in the chart tab
        self.ui.add_user_box.clear()
        for user in users:
            if users[user] in self.added_users:
                pass
            else:
                self.added_users.append(f'{users[user]}')
                self.user_selections[users[user]] = user
        
        #during multi session to prevent previous data to get lost
        old_user_selection = self.user_selections
        self.user_selections = {str(v) : str(k) for k, v in users.items()}
        for i in old_user_selection:
            if i not in self.user_selections:
                self.user_selections[i] = old_user_selection[i]
                
        if 'All Count' in self.added_users:
            pass
        else:
            self.added_users.append('')
            self.added_users.append('All Count')
            self.added_users.append('KPI Count')
            self.user_selections[''] = ''
            self.user_selections['All Count'] = 'All Count'
            self.user_selections['KPI Count'] = 'KPI Count'
        self.added_users.sort()   
        
        #keeps a list of all username for easy telegram id to telegram name 
        #format {user_id:tg_name}
        
        for user in self.added_users:
            if user == '':
                pass
            elif user == 'KPI Count':
                pass
            elif user == 'All Count':
                pass
            else:
                self.user_id_name[self.user_selections[user]] = user

        self.ui.add_user_box.addItems(self.added_users)

    def client_starter(self):
        #reset variables, table rows, labels
        #detects multi session or single session
        #and verifies whether a session is active
        
        self.reload_kpi()
        self.session_detector()
        self.disable_widgets()
        self.label_changer(0, 0)
        self.set_button_empty()
        self.ui.total_2.setText(f'Total Message: 0')
        self.ui.total_1.setText(f'Total KPI: 0')
        self.empty_buttons = [self.ui.chart_button_1, self.ui.chart_button_2, self.ui.chart_button_3,
                self.ui.chart_button_4, self.ui.chart_button_5, self.ui.chart_button_6, self.ui.chart_button_7,
                self.ui.chart_button_8, self.ui.chart_button_9, self.ui.chart_button_10]

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
        self.date_counts = {}
        self.date_counts_kpi = {}
        self.user_selections = {}
        self.user_id_name = {}
        self.date_counts = {}
        self.date_counts_kpi = {}
        self.date_hour_counts = {}
        self.date_hour_counts_kpi = {}
        self.user_date_counts = {}
        self.user_date_hour_counts = {}
        self.added_in_chart = {}
        self.added_users = []
        self.counting = True
        self.finishing_log = False

        #verify the session selected/available ones and start the
        #main function which starts up the thread

        if self.multi_sess_selected == True:
            pool = QThreadPool.globalInstance()
            available_sess = self.session_list
            for i in available_sess:
                self.ui.statusBar().showMessage(f'Verifying Session {i}')
                if self.ui.calender.isVisible() or '-' in self.ui.box_starting_mess.text(): #TODO save somewhere whether date was added or not
                    self.worker = session_verifier(self.group_name, i, self.pri_group, date_added=True, start_date=self.starting_date, end_date=self.ending_date)
                else:
                    self.worker = session_verifier(self.group_name, i, self.pri_group)
                self.worker.signal.incomplete_sess.connect(self.incom_sess)
                self.worker.signal.finished.connect(self.finishing)
                self.worker.signal.latest_mess.connect(self.latest_mess_id)
                self.worker.signal.date_mess_ids.connect(self.date_message_id)
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
            if self.ui.calender.isVisible() or '-' in self.ui.box_starting_mess.text():
                self.worker = session_verifier(self.group_name, self.cu_session, self.pri_group, date_added=True, start_date=self.starting_date, end_date=self.ending_date)
            else:
                self.worker = session_verifier(self.group_name, self.cu_session, self.pri_group)
            self.worker.signal.incomplete_sess.connect(self.incom_sess)
            self.worker.signal.finished.connect(self.finishing)
            self.worker.signal.latest_mess.connect(self.latest_mess_id)
            self.worker.signal.date_mess_ids.connect(self.date_message_id)
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
            print(self.mess_id_latest)
            self.thread_timer.stop()

        elif self.mess_id_latest == 0 and self.cu_session in self.incomplete_sess:
            self.thread_timer.stop()
            self.ui.statusBar().showMessage(f'{self.cu_session} Incomplete Session or Invalid Group')
            self.enable_widgets()
            return
        
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
                             self.cu_session, self.create_log, 1, 1,
                             mess_value=message_value, multi_sess=False,
                             max_bar=100, add_time=self.add_time,
                             time_difference=self.time_difference)
            self.worker.signal.progress.connect(self.data_distributor)
            self.worker.signal.list_size.connect(self.row_amount)
            self.worker.signal.row_data.connect(self.set_row_data)
            self.worker.signal.row_data_2.connect(self.set_row_data_kpi)
            self.worker.signal.mess_char.connect(self.total_mess_saver)
            self.worker.signal.finished.connect(self.finishing)
            self.worker.signal.date_counts.connect(self.date_messages)
            self.worker.signal.counted_users.connect(self.counted_users)
            pool.start(self.worker)
            break
    
    def multi_client(self):
        #for processing multi session
        #verifies whether the session is good to go or
        #if private group is joined if selected
        #divides the part of each session and starts the
        #thread accordingly
        if self.mess_id_latest != 0 and len(self.session_list) == len(self.incomplete_sess) + len(self.complete_sess):
            self.thread_timer.stop()

        elif self.mess_id_latest == 0 and len(self.session_list) == len(self.incomplete_sess):
            self.thread_timer.stop()
            self.ui.statusBar().showMessage(f'{self.cu_session} Incomplete Session or Invalid Group')
            self.enable_widgets()
            return

        elif len(self.session_list) == len(self.incomplete_sess):
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

        new_starting = self.group_starting
        parts_start = {}
        parts_end = {}

        if int(threadCount) > len(available_sess):
            total_max_thread = len(available_sess)
        else:
            total_max_thread = int(threadCount)
        
        #this part is important that depends which thread will run
        #from which message and stop where. If I have 4 sessions and
        #message starts from 0 to 100 message ID it will go like this
        #Sess 1 = 0-25, Sess 2 = 25-50 Sess 2 = 50-75 Sess 2 = 75-100

        for i in range(total_max_thread-1, -1, -1):
            if i == total_max_thread -1:
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
        #if there is a odd nunber of sessions the dividing  thread value can have
        #float value. So give each session an integer value and lastly
        #give the final session whatever value is left

        for i in available_sess:
            thread_num += 1
            part_bar = int(100/total_max_thread)
            if i == available_sess[-1]:
                part_bar = final_part_value
            self.worker = Worker(self.group_name, parts_start[i],
                             parts_end[i],
                             i, self.create_log, thread_num, 
                             total_max_thread, mess_value=message_value,
                             multi_sess=True, max_bar=part_bar,
                             add_time=self.add_time,
                             time_difference=self.time_difference)

            final_part_value -= part_bar
            self.worker.signal.progress.connect(self.data_distributor_multi)
            self.worker.signal.list_size.connect(self.row_amount)
            self.worker.signal.row_data.connect(self.set_row_data)
            self.worker.signal.row_data_2.connect(self.set_row_data_kpi)
            self.worker.signal.mess_char.connect(self.total_mess_saver)
            self.worker.signal.finished.connect(self.finishing)
            self.worker.signal.date_counts.connect(self.date_messages)
            self.worker.signal.counted_users.connect(self.counted_users)
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
    latest_mess = pyqtSignal(list)
    incomplete_sess = pyqtSignal(str)
    date_mess_ids = pyqtSignal(list)
    date_counts = pyqtSignal(list)
    counted_users = pyqtSignal(dict)


class Worker(QRunnable):
    def __init__(self, group_name, group_starting,
                 group_ending, session_name, create_log, 
                 thread_num, total_thread, mess_value=0, 
                 multi_sess=False, max_bar=0, add_time=False,
                 time_difference=0):
        super().__init__()
        self.pending = 0
        self.cu_session = session_name
        self.last_id = group_ending
        self.group_ending = group_ending
        self.group_name = group_name
        self.group_starting = group_starting
        self.mess_value = mess_value
        self.create_log = create_log
        self.thread_num = thread_num
        self.total_thread = total_thread
        self.multi_sess = multi_sess
        self.max_bar = max_bar
        self.add_time = add_time
        self.time_difference = time_difference

        self.total_mess = 0
        self.counter = 0
        self.bar = 0
        self.pending_message = 0
        self.row_number_all = 0
        self.row_number_kpi = 0

        self.message_data = {}
        self.date_mess_count = {}
        self.kpi_mess_count = {}
        self.date_hour_mess_count = {}
        self.kpi_hour_mess_count = {}
        self.user_date_mess_count = {}
        self.user_date_hour_mess_count = {}
        self.all_checked_users = {}
        
        self.date_today = ''
        self.signal = worker_signals()
        print(self.group_name, self.group_starting, self.group_ending, self.thread_num, self.add_time, self.time_difference)

    @pyqtSlot()
    def run(self):
        async def kpi_counter():
            global stop_process, verified_entities
            
            client = TelegramClient(self.cu_session, api_id, api_hash)
            await client.connect()
            me = await client.get_me()
            print(self.cu_session)
            if me == 'None' or me is None:
                print('Session incomplete')
                self.signal.finished.emit(['incomplete', 'incomplete', self.thread_num])

            else:
                async with client:
                    #start iterating from the selected message links
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
                        
                        elif message.action is not None:
                            pass

                        else:
                            try:
                                #get the date in both daily and hourly in int form
                                #add or take time based on timezone and count the message
                                #amount for each. 
                                self.date_today = message.date
                                if self.add_time == True:
                                    self.date_today += datetime.timedelta(minutes=self.time_difference)
                                else:
                                    self.date_today -= datetime.timedelta(minutes=self.time_difference)

                                int_date = int(self.date_today.strftime("%Y%m%d"))
                                int_hour_date = int(self.date_today.strftime("%Y%m%d%H"))

                                if int_date in self.date_mess_count:
                                    self.date_mess_count[int_date] += 1
                                else:
                                    self.date_mess_count[int_date] = 1

                                if int_hour_date in self.date_hour_mess_count:
                                    self.date_hour_mess_count[int_hour_date] += 1
                                else:
                                    self.date_hour_mess_count[int_hour_date] = 1

                                try:
                                    #another try in case there is no message sender

                                    mess_sender = message.from_id.user_id
                                            
                                    if int_date in self.user_date_mess_count and mess_sender in self.user_date_mess_count[int_date]:
                                        self.user_date_mess_count[int_date][mess_sender] = self.user_date_mess_count[int_date][mess_sender] + 1

                                    elif int_date in self.user_date_mess_count and mess_sender not in self.user_date_mess_count[int_date]:
                                        self.user_date_mess_count[int_date][mess_sender] = 1
                                    
                                    elif int_date not in self.user_date_mess_count:
                                        self.user_date_mess_count[int_date] = {}
                                        self.user_date_mess_count[int_date][mess_sender] = 1

                                    if int_hour_date in self.user_date_hour_mess_count and mess_sender in self.user_date_hour_mess_count[int_hour_date]:
                                        self.user_date_hour_mess_count[int_hour_date][mess_sender] = self.user_date_hour_mess_count[int_hour_date][mess_sender] + 1

                                    elif int_hour_date in self.user_date_hour_mess_count and mess_sender not in self.user_date_hour_mess_count[int_hour_date]:
                                        self.user_date_hour_mess_count[int_hour_date][mess_sender] = 1
                                    
                                    elif int_hour_date not in self.user_date_hour_mess_count:
                                        self.user_date_hour_mess_count[int_hour_date] = {}
                                        self.user_date_hour_mess_count[int_hour_date][mess_sender] = 1
                                except Exception as e:
                                    print(e)

                            except Exception as e:
                                print(e)
                                print('Error while getting date')
                            try:
                                try:
                                    try:
                                        #adds date data, message amount to dict for passing it to the charts
                                        #
                                        if message.from_id.user_id in accounts:
                                            int_date = int(self.date_today.strftime("%Y%m%d"))
                                            if int_date in self.kpi_mess_count:
                                                self.kpi_mess_count[int_date] += 1
                                            else:
                                                self.kpi_mess_count[int_date] = 1

                                            int_hour_date = int(self.date_today.strftime("%Y%m%d%H"))
                                            if int_hour_date in self.kpi_hour_mess_count:
                                                self.kpi_hour_mess_count[int_hour_date] += 1
                                            else:
                                                self.kpi_hour_mess_count[int_hour_date] = 1

                                    except Exception as e:
                                        print('Error while adding KPI Date')
                                        print(e)
                                    
                                    try:
                                        #keeps track of message length for counting average character
                                        mess_text = message.message
                                        mess_len = len(str(mess_text))
                                        if mess_len == 0:
                                            mess_len = 1    #if it's a sticker len is going to be 0, so make it 1
                                        self.signal.mess_char.emit([message.from_id.user_id, mess_len])
                                    except Exception as e:
                                        exc_type, exc_obj, exc_tb = sys.exc_info()
                                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                        #print(exc_type, fname, exc_tb.tb_lineno, e)

                                    #for keeping track of message data by each user
                                    mess_sender = message.from_id.user_id
                                    if mess_sender in self.message_data:
                                        self.message_data[mess_sender] = self.message_data[mess_sender] + 1
                                    elif mess_sender not in self.message_data:
                                        self.message_data[mess_sender] = 1

                                    if int(message.id) == self.group_starting: 
                                        #group_start is the stopping point for this run
                                        #add the count to the variables and break the loop
                                        
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
                                        if message.from_id.user_id in accounts:
                                            self.counter += 1

                                    #pending controls the bar value. So after each message add the 
                                    #message value * how many many messages. Message passed calculated
                                    #by the last message id that was counted - current id 

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
                                
                            except Exception as e:
                                exc_type, exc_obj, exc_tb = sys.exc_info()
                                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                #print(exc_type, fname, exc_tb.tb_lineno, e)


                    #in case the bar value does not fill up where it is supposed to
                    #fill it up manually

                    if self.bar > self.max_bar:
                        pass
                    elif self.bar != self.max_bar and self.multi_sess == False:
                        self.bar = self.max_bar
                    
                    elif self.bar != self.max_bar and self.multi_sess == True:
                            self.bar = self.max_bar

                    self.signal.progress.emit(
                        [self.bar, self.total_mess, self.counter, self.thread_num])

                    self.signal.date_counts.emit([self.date_mess_count, self.kpi_mess_count, self.date_hour_mess_count, self.kpi_hour_mess_count, self.user_date_mess_count, self.user_date_hour_mess_count])
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
                                if sender in verified_entities:
                                    id_num = verified_entities[sender][0]
                                    username = verified_entities[sender][1]
                                    first_name = verified_entities[sender][2]
                                    last_name = verified_entities[sender][3]
                                else:
                                    entity = await client.get_entity(sender)
                                    id_num = entity.id
                                    username = entity.username
                                    first_name = entity.first_name
                                    last_name = entity.last_name
                                    verified_entities[sender] = [id_num, username, first_name, last_name]
                                    
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
                                
                                if username is not None:
                                    self.all_checked_users[sender] = username.lower()
                                
                                elif first_name is not None:
                                    self.all_checked_users[sender] = full_name.lower()
                                
                                else:
                                    self.all_checked_users[sender] = sender

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
                    self.signal.counted_users.emit(self.all_checked_users)
                    await client.disconnect()
                    try:
                        await client.disconnected
                    except OSError:
                        print('Error on disconnect')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(kpi_counter())

class session_verifier(QRunnable):
    def __init__(self, group_name, session_name, private_group, date_added=False, start_date='', end_date=''):
        super().__init__()
        self.pending = 0
        self.cu_session = session_name
        self.group_name = group_name
        self.private_group = private_group
        self.date_added = date_added
        self.start_date = start_date
        self.end_date = end_date
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
                        if self.date_added == True:
                            start_mess = 0
                            end_mess = 0
                            new_start_date = int(self.start_date.strftime('%Y%m%d'))
                            start_mess_veri = False
                            
                            while start_mess_veri == False:
                                async for message in client.iter_messages(self.group_name, offset_date=self.start_date):
                                    
                                    #due to big difference in dates sometimes it fails to get any message id
                                    #so keep looping until the message id is found
                                    #numeric date was added so in case the selected message is the first
                                    #message in the chat not necessary to add +1 to it
                                    
                                    new_mess_date = int(message.date.strftime('%Y%m%d'))
                                    
                                    if str(message.id).isnumeric():
                                        start_mess_veri = True
                                        
                                    if new_start_date < new_mess_date:
                                        start_mess = message.id
                                    else:
                                        start_mess = message.id + 1     #TODO switch to get_messages
                                    break
                            
                            async for message in client.iter_messages(self.group_name, offset_date=self.end_date):
                                end_mess = message.id + 1
                                break
                            
                            print([start_mess, end_mess])
                            #print('Start', start_mess, 'End', end_mess)
                            self.signal.date_mess_ids.emit([start_mess, end_mess])

                        if self.private_group == True:
                            group_list = []
                            async for group in client.iter_dialogs():
                                group_list.append(group.id)

                        if self.private_group == True and self.group_name in group_list:
                            async for message in client.iter_messages(self.group_name):
                                self.signal.latest_mess.emit([message.id, self.cu_session])
                                break

                        elif self.private_group == True and self.group_name not in group_list:
                            print('Not joined in the Private Group')
                            self.signal.incomplete_sess.emit(f'{self.cu_session} is incomplete')
                        
                        elif self.private_group == False:
                            async for message in client.iter_messages(self.group_name):
                                self.signal.latest_mess.emit([message.id, self.cu_session])
                                break

                await client.disconnect()
                try:
                    await client.disconnected
                except Exception:
                    print('Error on disconnect')
            except Exception as e:
                print(e)
                self.signal.incomplete_sess.emit(f'{self.cu_session} is incomplete')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(verifier())


app = QApplication(sys.argv)
w = main_form()
w.show()
sys.exit(app.exec_())
