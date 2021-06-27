import sys, os, pyperclip
from PyQt5 import uic
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QAction, QDesktopWidget
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import *
from telethon import TelegramClient
import asyncio, pickle
from session_creator import *
from id_manager import *
import PyQt5.sip

api_id = 1234567
api_hash = 'test'
client = ''

'''account = {1608710447:'@Alena_70', 1534729591:'@e8ri1', 1653706980:'@Looping3', 1623661882:'@Invisible997', 
1420682282:'@d33pTruth', 1651341982:'@crypt0_general', 1695444446:'@defi_thomas', 1663463356:'@MartiniT7', 
1655027089:'@partick56', 1631510119:'@DFY_Leo', 1608007430:'@C00lpAd', 1426914022:'@Defimon3y', 
1686051355:'@Btcmoon21', 1559965977:'@James_Blond_007', 1564496846:'@eekrummhage', 1695509303:'@AnakinCrypto', 
1619755723:'@RisingS13', 1685793118:'@DefiBuss', 1765483504:'@CS_Maria', 1795480092:'@mmnn00pp', 1768055674:'@Mark3N', 
1617103747:'@muchbRick', 1758865018:'@Josia609', 1486733003:'@stgbee', 1573800503:'@Alicialkr', 1771205214:'@l_gainz_l', 
1701748147:'@Ultra99G', 1760556186:'@d_D_c8'}

data_store = open('resource/kpi_id.pckl', 'wb')
pickle.dump(account, data_store)
data_store.close()'''

if os.path.exists('resource/kpi_id.pckl'):
    pass
else:
    data_store = open('kpi_id.pckl', 'wb')
    pickle.dump({}, data_store)
    data_store.close()

data_store = open('resource/kpi_id.pckl', 'rb')
accounts = pickle.load(data_store)
data_store.close()


class MyForm(QMainWindow):
    global client
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('resource/logo.png')) 
        self.ui = uic.loadUi('resource/Design.ui', self)
        #self.ui.setupUi(self)
        self.group_name = ''
        self.group_name_2 = ''
        self.group_starting = 0
        self.group_ending = 0
        self.cu_session = ''
        self.running = False
        self.force_stop = 3
        self.counting_time = 3
        self.cu_dots = ''
        self.resize(400, 350)
        self.ui.box_tg_code.resize(75, 30)
        self.ui.button_send_code.resize(90, 30)
        self.create_log = True
        self.reload_pressed = False
        self.starting_paste = True
        self.ending_paste = True

        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.manager = id_manager(self.ui)
        self.sess = session_builder(self.ui)
        self.ui.Button_count.clicked.connect(self.data_parser)
        self.ui.button_exit.clicked.connect(self.exiting)
        self.ui.button_exit_2.clicked.connect(self.exiting)
        self.ui.button_new_session.clicked.connect(self.session_page)
        self.ui.button_ids.clicked.connect(self.id_page)
        self.ui.button_log.clicked.connect(self.log_page)
        self.ui.button_back.clicked.connect(self.back_button)
        self.ui.button_back_2.clicked.connect(self.back_button)
        self.ui.button_main_menu.clicked.connect(self.main_menu)
        self.ui.button_create_sess.clicked.connect(self.sess.sess_creator)
        self.ui.button_send_code.clicked.connect(self.sess.tg_code_sender)
        self.ui.table_widget_1.setColumnWidth(0, 200)
        self.ui.table_widget_2.setColumnWidth(0, 200)
        self.ui.table_widget_1.setColumnWidth(1, 80)
        self.ui.table_widget_2.setColumnWidth(1, 80)
        self.ui.button_clear_1.clicked.connect(self.edit_box_1)
        self.ui.button_clear_2.clicked.connect(self.edit_box_2)
        self.ui.button_reload.clicked.connect(self.reload_router)
        self.ui.button_add_user.clicked.connect(self.manager.add_user)
        self.ui.listWidget.itemClicked.connect(self.manager.list_selected)
        self.ui.button_remove.clicked.connect(self.manager.list_remove)
        self.ui.button_save.clicked.connect(self.manager.list_save)
        self.ui.box_ending_mess.textChanged.connect(self.text_changed_ending)
        self.ui.box_starting_mess.textChanged.connect(self.text_changed_starting)
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)
        self.ui.button_clear_2.setText('Paste')
        self.ui.button_clear_1.setText('Paste')
        
        #self.ui.table_widget_1.setItem(1,1,QtWidgets.QTableWidgetItem('@Sakib0194'))
        self.session_detector()
        self.exit_detector()
        self.show()

    def text_changed_starting(self):
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
        close = QMessageBox()
        if self.running == True:
            if self.force_stop != 1:
                self.force_stop -= 1
                close.setText(f"Cannot close! Action ongoing\nTry {self.force_stop} more times to Force Close the App")
                close.setStandardButtons(QMessageBox.Cancel)
                close.setIcon(QMessageBox.Warning)
                close = close.exec()
                event.ignore()
            else:
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
    
    def reload_router(self):
        self.reload_pressed = True
        self.sess.reload_value()
        self.manager.reload_list()

    def exit_detector(self):
        quit = QAction("Quit", self)
        quit.triggered.connect(self.close)

    def exiting(self):
        self.close()
    
    def back_button(self):
        self.resize(400, 350)
        self.ui.stackedWidget.setCurrentWidget(self.ui.page)
        

    def main_menu(self):
        global accounts
        self.resize(400, 350)
        self.ui.stackedWidget.setCurrentWidget(self.ui.page)
        data_store = open('resource/kpi_id.pckl', 'rb')
        accounts = pickle.load(data_store)
        data_store.close()
    
    def session_page(self):
        self.resize(400, 350)
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_2)

    def log_page(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_3)
        self.resize(850, 400)
        

    def id_page(self):
        self.resize(400, 350)
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_4)

    def session_detector(self):
        all_files = []
        self.ui.combobox_session.clear()
        self.ui.combo_session_2.clear()
        for files in os.listdir(os.curdir):
            if files.endswith('session'):
                base_name = os.path.splitext(files)[0]
                all_files.append(base_name)
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

    def edit_box_1(self):
        if self.starting_paste == True:
            self.ui.box_starting_mess.setText(str(pyperclip.paste()))
        else:
            self.ui.box_starting_mess.clear()
    
    def edit_box_2(self):
        if self.ending_paste == True:
            self.ui.box_ending_mess.setText(str(pyperclip.paste()))
        else:
            self.ui.box_ending_mess.clear()

    def data_parser(self):
        if self.ui.check_create_log.isChecked():
            self.create_log = True
        else:
            self.create_log = False

        starting_data = self.ui.box_starting_mess.text()
        starting_data = "".join(starting_data.split())
        if '/c/' in starting_data:
            self.ui.statusBar().showMessage(f'Private Group Detected')
            
        ending_data = self.ui.box_ending_mess.text()
        ending_data = "".join(ending_data.split())
        self.cu_session = self.ui.combobox_session.currentText()
        try:
            if starting_data == '':
                pass
            elif 'https://t.me/' not in starting_data:
                self.ui.statusBar().showMessage(f'https://t.me/group_name/message_id is the correct format')
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
                        ending_data = ending_data.replace('https://t.me/c/', '')
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
            self.ui.statusBar().showMessage(f'Make sure the links are in correct format. Example: https://t.me/TestGroup/123456 or https://t.me/c/123456/123456')

    def counting_label(self):
        if self.cu_dots == '....':
            self.cu_dots = ''
        if self.counting_time == 0:
            self.cu_dots += '.'
            self.ui.statusBar().showMessage(f'Counting{self.cu_dots}')
            self.counting_time = 1
        else:
            self.counting_time -= 1

    def client_starter(self):
        #self.ui.table_widget_1.clear()
        #self.ui.table_widget_2.clear()
        while self.ui.table_widget_1.rowCount() > 0:
            self.ui.table_widget_1.removeRow(0)
        while self.ui.table_widget_2.rowCount() > 0:
            self.ui.table_widget_2.removeRow(0)
        self.ui.table_widget_1.setRowCount(5)
        self.ui.table_widget_2.setRowCount(5)
        self.ui.progressBar.setValue(0)
        self.ui.Button_count.setEnabled(False)
        self.ui.button_create_sess.setEnabled(False)
        self.ui.button_send_code.setEnabled(False)
        self.ui.button_reload.setEnabled(False)
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)
        self.ui.progressBar.setValue(0)
        self.running = True
        self.force_stop = 3
        self.thread = QThread()
        self.worker = Worker(self.group_name, self.group_starting, self.group_ending, self.cu_session, self.create_log)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.data_distributor)
        self.worker.list_size.connect(self.row_amount)
        self.worker.row_data.connect(self.set_row_data)
        self.worker.row_data_2.connect(self.set_row_data_kpi)
        self.worker.finished.connect(self.finishing)
        self.thread.start()

    def data_distributor(self, list_data):
        print(f'Bar Value: {list_data[0]}, Total Message: {list_data[1]}, Counter: {list_data[2]}')
        self.progress_bar(int(list_data[0]))
        self.label_changer(int(list_data[1]), int(list_data[2]))
        self.counting_label()

    def progress_bar(self, num):
        self.ui.progressBar.setValue(num)
    
    def label_changer(self, num_1, num_2):
        self.ui.label_2.setText(f'Total Checked: {num_1}')
        self.ui.label_3.setText(f'KPI Counter: {num_2}')
        self.ui.label_2.adjustSize()
        self.ui.label_3.adjustSize()

    def finishing(self, total_num):
        self.ui.Button_count.setEnabled(True)
        self.ui.button_create_sess.setEnabled(True)
        self.ui.button_send_code.setEnabled(True)
        self.ui.button_reload.setEnabled(True)
        if self.reload_pressed == True:
            self.ui.button_save.setEnabled(True)
            self.ui.button_remove.setEnabled(True)
            self.ui.button_add_user.setEnabled(True)
        self.group_name = ''
        self.group_name_2 = ''
        self.group_starting = 0
        self.group_ending = 0
        self.cu_session = ''
        self.running = False
        self.force_stop = 3
        self.counting_time = 3
        self.cu_dots = ''
        if total_num[0] == 'incomplete':
            self.ui.total_2.setText(f'Total: 0')
            self.ui.total_1.setText(f'Total: 0')
            self.ui.statusBar().showMessage('Incomplete Session. Please create one with Create Session button')
        else:
            self.ui.statusBar().clearMessage()
            self.ui.total_2.setText(f'Total: {total_num[0]}')
            self.ui.total_1.setText(f'Total: {total_num[1]}')

    def row_amount(self, num):
        self.ui.table_widget_1.setRowCount(num)
        self.ui.table_widget_2.setRowCount(len(accounts))

    def set_row_data(self, data):
        name = QtWidgets.QTableWidgetItem(data[0])
        count = QtWidgets.QTableWidgetItem(str(data[1]))
        count.setTextAlignment(QtCore.Qt.AlignCenter)
        row_num = data[2]
        user_id = QtWidgets.QTableWidgetItem(str(data[3]))
        user_id.setTextAlignment(QtCore.Qt.AlignCenter)
        self.ui.table_widget_1.setItem(row_num,0,QtWidgets.QTableWidgetItem(name))
        self.ui.table_widget_1.setItem(row_num,1,QtWidgets.QTableWidgetItem(count))
        self.ui.table_widget_1.setItem(row_num,2,QtWidgets.QTableWidgetItem(user_id))

        if self.cu_dots == '....':
            self.cu_dots = ''
        if self.counting_time == 0:
            self.cu_dots += '.'
            self.ui.statusBar().showMessage(f'Finishing Logs{self.cu_dots}')
            self.counting_time = 3
        else:
            self.counting_time -= 1

    def set_row_data_kpi(self, data):
        name = QtWidgets.QTableWidgetItem(data[0])
        count = QtWidgets.QTableWidgetItem(str(data[1]))
        count.setTextAlignment(QtCore.Qt.AlignCenter)
        row_num = data[2]
        user_id = QtWidgets.QTableWidgetItem(str(data[3]))
        user_id.setTextAlignment(QtCore.Qt.AlignCenter)
        self.ui.table_widget_2.setItem(row_num,0,QtWidgets.QTableWidgetItem(name))
        self.ui.table_widget_2.setItem(row_num,1,QtWidgets.QTableWidgetItem(count))
        self.ui.table_widget_2.setItem(row_num,2,QtWidgets.QTableWidgetItem(user_id))

class Worker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(list)
    list_size = pyqtSignal(int)
    row_data = pyqtSignal(list)
    row_data_2 = pyqtSignal(list)

    def __init__(self, group_name, group_starting, group_ending, session_name, create_log):
        super().__init__()
        self.pending = 0
        self.cu_session = session_name
        self.last_id = group_ending
        self.group_ending = group_ending
        self.group_name = group_name
        self.group_starting = group_starting
        self.total_mess = 0
        self.counter = 0
        self.mess_value = 0
        self.bar = 0
        self.pending_message = 0
        self.message_data = {}
        self.row_number_all = 0
        self.row_number_kpi = 0
        self.create_log = create_log

    def run(self):
        async def kpi_counter():
            
            client = TelegramClient(self.cu_session, api_id, api_hash)
            await client.connect()
            me = await client.get_me()
            if me == 'None' or me == None:
                print('Session incomplete')
                self.finished.emit(['incomplete','incomplete'])

            else:
                async with client:
                        #a = time.time()
                        async for message in client.iter_messages(self.group_name, offset_id=self.group_ending): 
                            try:
                                mess_sender = message.from_id.user_id
                                if mess_sender in self.message_data:
                                    self.message_data[mess_sender] = self.message_data[mess_sender] + 1
                                elif mess_sender not in self.message_data:
                                    self.message_data[mess_sender] = 1

                            except Exception as e:
                                print(e)
                            try:
                                if self.last_id != 0:
                                    self.total_mess += (self.last_id - message.id)
                                    self.pending += self.mess_value * (self.last_id - message.id)
                                else:
                                    self.total_mess += 1
                                    self.pending += self.mess_value

                                #self.pending += self.mess_value * (self.last_id - message.id)
                                self.last_id = message.id 

                                if self.mess_value == 0:
                                    if self.group_ending == 0:
                                        self.mess_value_counter(message.id)
                                    else:
                                        self.mess_value_counter(self.group_ending)

                                self.pending_message += 1

                                try:
                                    if int(message.id) <= self.group_starting:    
                                        self.pending = 100
                                        
                                        if '/auscm' in message.message:
                                            pass
                                        else:
                                            if message.from_id.user_id in accounts:
                                                self.counter += 1
                                        break
                                        
                                    else:
                                        if '/auscm' in message.message:
                                            pass
                                        else:
                                            if message.from_id.user_id in accounts:
                                                self.counter += 1

                                    if self.pending > 1:
                                        if self.bar != 99:
                                            self.bar += int(self.pending)
                                        self.pending = self.pending - int(self.pending)
                                        self.progress.emit([self.bar, self.total_mess, self.counter])  
                                        await asyncio.sleep(0.02)   

                                    elif self.pending_message > 5:
                                        self.progress.emit([self.bar, self.total_mess, self.counter])
                                        self.pending_message = 0
                                        await asyncio.sleep(0.02)   
                                except Exception as e:
                                    self.pending += self.mess_value
                                    if self.pending_message > 5:
                                        self.progress.emit([self.bar, self.total_mess, self.counter])
                                        self.pending_message = 0
                                    #print(e)
                                    pass
                            except Exception as e:
                                #print(e)
                                pass
                        if self.pending > 1:
                            self.bar += int(self.pending)
                            if self.bar > 100:
                                self.bar = 100
                                self.pending = self.pending - int(self.pending)  
                        self.progress.emit([self.bar, self.total_mess, self.counter])

                        total_all = 0
                        total_kpi = 0
                        self.message_data = dict(sorted(self.message_data.items(), key=lambda item: item[1]))
                        if self.create_log == True:
                            self.list_size.emit(len(self.message_data))
                            
                            for sender in self.message_data:
                                try:
                                    entity = await client.get_entity(sender)
                                    id_num = entity.id
                                    username = entity.username
                                    first_name = entity.first_name
                                    last_name = entity.last_name
                                    full_name = f'{first_name}'
                                    if last_name != None:
                                        full_name += f' {last_name}'
                                    if username != None:
                                        full_name += f' : {username}'
                                    else:
                                        full_name += f':Nothing'
                                    total_all += self.message_data[sender]
                                    print(full_name, self.message_data[sender])
                                    row_data = [full_name, self.message_data[sender], self.row_number_all, id_num]
                                    self.row_number_all += 1
                                    self.row_data.emit(row_data)

                                    if sender in accounts:
                                        row_data = [full_name, self.message_data[sender], self.row_number_kpi, id_num]
                                        self.row_number_kpi += 1
                                        self.row_data_2.emit(row_data)
                                        total_kpi += self.message_data[sender]
                                except Exception as e:
                                    print(e)

                        self.finished.emit([total_all, total_kpi])
                        await client.disconnect()
                        try:
                            await client.disconnected
                        except OSError:
                            print('Error on disconnect')
                        #print('emitted', self.total_mess)
                        #b = time.time() - a
                        #print("Total time", b)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(kpi_counter())
        loop.close()

    def mess_value_counter(self, num):
        initial = self.group_starting
        try:
            self.mess_value = 100/(num - initial)
        except Exception as e:
            print(e)
            self.mess_value = 100
        print(num - initial)
        print(self.mess_value)

   
app = QApplication(sys.argv)
w = MyForm()
w.show()
sys.exit(app.exec_())