from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import *
from telethon import TelegramClient
import asyncio
import pickle

data_store = open('resource/kpi_id.pckl', 'rb')
accounts = pickle.load(data_store)
data_store.close()
api_id = 1234567
api_hash = 'test'
client = ''


class id_manager:
    def __init__(self, ui):
        self.ok = 'nothing'
        self.ui = ui
        self.acc_list = accounts
        self.session_name = ''
        self.loaded_data = {}
        self.selected_item = ''

    def list_selected(self, item):
        self.selected_item = item.text()
        print(self.selected_item)

    def list_remove(self):
        try:
            row_num = self.ui.listWidget.currentRow()
            self.ui.listWidget.takeItem(row_num)
            if self.selected_item in self.loaded_data:
                del self.loaded_data[self.selected_item]
                new_select = self.ui.listWidget.currentItem().text()
                print(new_select)
                self.selected_item = str(new_select)
        except Exception as e:
            print(e)

    def list_save(self):
        global accounts
        new_list = {}
        for i in self.loaded_data:
            if i in new_list:
                pass
            else:
                user_id = self.loaded_data[i][0]
                user_name = f'@{self.loaded_data[i][1]}'
                new_list[user_id] = user_name
        print(new_list)
        data_store = open('resource/kpi_id.pckl', 'wb')
        pickle.dump(new_list, data_store)
        data_store.close()

        data_store = open('resource/kpi_id.pckl', 'rb')
        accounts = pickle.load(data_store)
        data_store.close()
        self.ui.statusBar().showMessage('Data Saved')

    def add_user(self):
        self.ui.Button_count.setEnabled(False)
        self.ui.button_create_sess.setEnabled(False)
        self.ui.button_send_code.setEnabled(False)
        self.ui.button_reload.setEnabled(False)
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)
        self.session_name = self.ui.combo_session_2.currentText()
        to_add = self.ui.box_add_user.text()
        self.ui.box_add_user.clear()
        self.thread = QThread()
        self.worker = checking_accounts(self.session_name, to_add, 'Add')
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(
            lambda: self.ui.button_create_sess.setEnabled(True))
        self.thread.finished.connect(
            lambda: self.ui.button_send_code.setEnabled(True))
        self.thread.finished.connect(
            lambda: self.ui.Button_count.setEnabled(True))
        self.thread.finished.connect(
            lambda: self.ui.button_reload.setEnabled(True))
        self.worker.progress.connect(self.list_updater)
        self.worker.progress_2.connect(self.bar_updater)
        self.worker.clear_text.connect(self.clear_status_bar)
        self.worker.incomplete.connect(self.incomplete)
        self.worker.complete.connect(self.complete)
        self.worker.finished.connect(self.finishing)
        self.thread.start()

    def reload_list(self):
        global accounts
        data_store = open('resource/kpi_id.pckl', 'rb')
        accounts = pickle.load(data_store)
        data_store.close()
        self.ui.listWidget.clear()
        self.ui.Button_count.setEnabled(False)
        self.ui.button_create_sess.setEnabled(False)
        self.ui.button_send_code.setEnabled(False)
        self.ui.button_reload.setEnabled(False)
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)
        self.session_name = self.ui.combo_session_2.currentText()
        self.ui.label_4.setHidden(True)

        self.thread = QThread()
        self.worker = checking_accounts(
            self.session_name, self.acc_list, 'Reload')
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(
            lambda: self.ui.button_create_sess.setEnabled(True))
        self.thread.finished.connect(
            lambda: self.ui.button_send_code.setEnabled(True))
        self.thread.finished.connect(
            lambda: self.ui.Button_count.setEnabled(True))
        self.thread.finished.connect(
            lambda: self.ui.button_reload.setEnabled(True))
        self.worker.progress.connect(self.list_updater)
        self.worker.progress_2.connect(self.bar_updater)
        self.worker.clear_text.connect(self.clear_status_bar)
        self.worker.incomplete.connect(self.incomplete)
        self.worker.complete.connect(self.complete)
        self.worker.finished.connect(self.finishing)
        self.thread.start()

    def list_updater(self, item):
        self.ui.listWidget.addItem(item)

    def clear_status_bar(self):
        self.ui.statusBar().clearMessage()

    def bar_updater(self, data):
        self.ui.statusBar().showMessage(f'{data}')

    def incomplete(self):
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)

    def complete(self):
        self.ui.button_save.setEnabled(True)
        self.ui.button_remove.setEnabled(True)
        self.ui.button_add_user.setEnabled(True)

    def finishing(self, data):
        if data != {}:
            for i in data:
                if i in self.loaded_data:
                    pass
                else:
                    self.loaded_data[i] = data[i]


class checking_accounts(QObject):
    progress = pyqtSignal(str)
    progress_2 = pyqtSignal(str)
    finished = pyqtSignal(dict)
    clear_text = pyqtSignal()
    incomplete = pyqtSignal()
    complete = pyqtSignal()

    def __init__(self, sess_name, acc_list, func_name):
        super().__init__()
        self.sess_name = sess_name
        self.acc_list = acc_list
        self.processed_acc = {}
        self.func_name = func_name

    def run(self):
        async def user_data():
            global accounts
            self.progress_2.emit('Getting Data...')
            client = TelegramClient(self.sess_name, api_id, api_hash)
            await client.connect()
            me = await client.get_me()
            if me == 'None' or me is None:
                print('Session incomplete')
                self.progress_2.emit(
                    'Session Invalid. Create a new Session to continue')
                self.finished.emit({})
                self.incomplete.emit()
            else:
                accounts = dict(
                    sorted(accounts.items(), key=lambda item: item[1]))
                async with client:
                    for user in accounts:
                        try:
                            try:
                                entity = await client.get_entity(user)
                            except Exception:
                                entity = await client.get_entity(accounts[user])
                            id_num = entity.id
                            username = entity.username
                            first_name = entity.first_name
                            last_name = entity.last_name
                            full_name = f'{first_name}'
                            if last_name is not None:
                                full_name += f' {last_name}'
                            if username is not None:
                                full_name += f' : {username}'
                            else:
                                full_name += ': Nothing'

                            self.processed_acc[full_name] = [id_num, username]
                            self.progress.emit(full_name)

                        except Exception:
                            self.progress.emit(
                                f'Could Not Find {user} {accounts[user]}')
                            self.processed_acc[f'Could Not Find {user} {accounts[user]}'] = [id_num, 'Unknown']

                await client.disconnect()
                try:
                    await client.disconnected
                except OSError:
                    print('Error on disconnect')
                self.clear_text.emit()
                self.finished.emit(self.processed_acc)
                self.complete.emit()

        async def add_user():
            self.progress_2.emit('Getting Data...')
            client = TelegramClient(self.sess_name, api_id, api_hash)
            await client.connect()
            me = await client.get_me()
            if me == 'None' or me is None:
                print('Session incomplete')
                self.progress_2.emit(
                    'Session Invalid. Create a new Session to continue')
                self.finished.emit({})
                self.incomplete.emit()
            else:
                async with client:
                    try:
                        print(self.acc_list)
                        if self.acc_list.isdigit():
                            entity = await client.get_entity(int(self.acc_list))
                        else:
                            entity = await client.get_entity(self.acc_list)
                        id_num = entity.id
                        username = entity.username
                        first_name = entity.first_name
                        last_name = entity.last_name
                        full_name = f'{first_name}'
                        if last_name is not None:
                            full_name += f' {last_name}'
                        if username is not None:
                            full_name += f': {username}'
                        else:
                            full_name += ':Nothing'

                        self.processed_acc[full_name] = [id_num, username]
                        self.progress.emit(full_name)
                        self.progress_2.emit(
                            'User Added To List. Press Save to Save Data. Duplicates will be removed')
                    except Exception as e:
                        print(e)
                        self.progress_2.emit(
                            f'Error Getting Data on User {self.acc_list}')
                self.finished.emit(self.processed_acc)
                self.complete.emit()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if self.func_name == 'Reload':
            loop.run_until_complete(user_data())
        elif self.func_name == 'Add':
            loop.run_until_complete(add_user())
        loop.close()
