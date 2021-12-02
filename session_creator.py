from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import *
from telethon import TelegramClient
import asyncio


class session_builder:
    def __init__(self, ui):
        self.ui = ui
        self.api_hash = ''  # TODO add default api_id and hash before making it exe
        self.api_id = 0
        self.tg_pass = ''
        self.sess_name = ''
        self.tg_code = 0
        self.phone = ''
        self.phone_hash = ''
        self.reload_pressed = False

    def sess_create(self):
        async def create():
            api_id = self.api_id
            api_hash = self.api_hash
            sess_name = self.sess_name
            tg_code = self.tg_code
            phone = self.phone.replace(' ', '')
            password = self.tg_pass
            client = TelegramClient(sess_name, api_id, api_hash)
            await client.connect()
            try:
                await client.sign_in(phone, tg_code,
                                     phone_code_hash=self.phone_hash)
            except Exception as e:
                print(e)
                if 'SessionPasswordNeededError' in str(e) or 'Two-steps verification is enabled and a password is required' in str(e):
                    await client.sign_in(password=password)
                elif 'The phone code entered was invalid' in str(e):
                    pass
                else:
                    pass
            self.ui.combobox_session.addItem(sess_name)
            await client.disconnect()
            try:
                await client.disconnected
            except OSError:
                print('Error on disconnect')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(create())

    def reload_value(self):
        self.reload_pressed = True

    def data_getter(self):
        self.tg_pass = self.ui.box_pass.text()
        self.sess_name = self.ui.box_session_name.text()
        self.tg_code = self.ui.box_tg_code.text()
        self.phone = self.ui.box_phone.text()
        self.phone = self.phone.replace(' ', '')

    def clear_boxes(self):
        self.ui.box_phone.clear()
        self.ui.box_pass.clear()
        self.ui.box_session_name.clear()
        self.ui.box_session_name.clear()
        self.ui.box_tg_code.clear()

    def status_bar_updater(self, text_data):
        print(text_data)
        if text_data.startswith('add_sess'):
            text_data = text_data[9:]
            self.ui.combobox_session.addItem(text_data)
            self.ui.combo_session_2.addItem(text_data)
        elif text_data.startswith('ph_hash'):
            text_data = text_data[8:]
            self.phone_hash = text_data
        else:
            self.ui.statusBar().showMessage(f'{text_data}')

    def tg_code_sender(self):
        self.data_getter()
        if self.ui.box_session_name.text() == '':
            self.ui.statusBar().showMessage('Session name cannot be empty')
            return
        self.ui.Button_count.setEnabled(False)
        self.ui.button_create_sess.setEnabled(False)
        self.ui.button_send_code.setEnabled(False)
        self.ui.button_reload.setEnabled(False)
        self.ui.button_save.setEnabled(False)
        self.ui.button_remove.setEnabled(False)
        self.ui.button_add_user.setEnabled(False)
        self.thread = QThread()
        self.worker = code_create('tele_code', self.api_id, self.api_hash,
                                  self.sess_name, self.phone, self.tg_pass,
                                  self.tg_code, self.phone_hash)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.ui.
                                     button_create_sess.setEnabled(True))
        self.thread.finished.connect(lambda: self.ui.
                                     button_send_code.setEnabled(True))
        self.thread.finished.connect(lambda: self.ui.
                                     Button_count.setEnabled(True))
        self.thread.finished.connect(lambda: self.ui.
                                     button_reload.setEnabled(True))
        self.worker.progress.connect(self.status_bar_updater)
        self.worker.finished.connect(self.finishing)
        self.thread.start()

    def finishing(self):
        if self.reload_pressed is True:
            self.ui.button_save.setEnabled(True)
            self.ui.button_remove.setEnabled(True)
            self.ui.button_add_user.setEnabled(True)

    def sess_creator(self):
        try:
            self.data_getter()
            if self.ui.box_session_name.text() == '':
                self.ui.statusBar().showMessage('Session name cannot be empty')
                return
            self.ui.Button_count.setEnabled(False)
            self.ui.button_create_sess.setEnabled(False)
            self.ui.button_send_code.setEnabled(False)
            self.thread = QThread()
            self.worker = code_create('create', self.api_id, self.api_hash,
                                      self.sess_name, self.phone, self.tg_pass,
                                      self.tg_code, self.phone_hash)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(lambda: self.ui.
                                         button_create_sess.setEnabled(True))
            self.thread.finished.connect(lambda: self.ui.
                                         button_send_code.setEnabled(True))
            self.thread.finished.connect(lambda: self.ui.
                                         Button_count.setEnabled(True))
            self.worker.progress.connect(self.status_bar_updater)
            self.worker.completed.connect(self.clear_boxes)
            self.thread.start()
        except Exception as e:
            print(e)


class code_create(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    completed = pyqtSignal()

    def __init__(self, func_name, api_id, api_hash, sess_name, phone, password,
                 tg_code, phone_hash):
        super().__init__()
        self.func_name = func_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.sess_name = sess_name
        self.phone = phone
        self.tg_pass = password
        self.tg_code = tg_code
        self.phone_hash = phone_hash

    def run(self):
        async def tele_code():
            try:
                api_id = self.api_id
                api_hash = self.api_hash
                sess_name = self.sess_name
                self.progress.emit('Connecting...')
                client = TelegramClient(sess_name, api_id, api_hash)
                phone = self.phone
                await client.connect()
                ph_hash = await client.sign_in(phone)
                self.progress.emit('Code Sent Successfully')
                self.progress.emit(f'ph_hash {ph_hash.phone_code_hash}')
                await client.disconnect()
                try:
                    await client.disconnected
                except OSError:
                    print('Error on disconnect')
                self.progress.emit('Code Sent Successfully')
                self.finished.emit()
            except Exception as e:
                print(e)
                if 'The phone number is invalid' in str(e):
                    self.progress.emit('Invalid Phone Number. Try again')
                else:
                    self.progress.emit(
                        'Something went wrong. Please double check your API ID and API Hash')
                self.finished.emit()

        async def create():
            try:
                api_id = self.api_id
                api_hash = self.api_hash
                sess_name = self.sess_name
                tg_code = self.tg_code
                phone = self.phone
                password = self.tg_pass
                self.progress.emit('Connecting...')
                client = TelegramClient(sess_name, api_id, api_hash)
                await client.connect()
                try:
                    self.progress.emit('Logging in')
                    print(phone, tg_code, self.phone_hash)
                    await client.sign_in(phone, tg_code,
                                         phone_code_hash=self.phone_hash)
                    await client.disconnect()
                    try:
                        await client.disconnected
                    except OSError:
                        print('Error on disconnect')
                    self.progress.emit('Session Created Successfully')
                    self.progress.emit(f'add_sess {sess_name}')
                    self.finished.emit()
                    self.completed.emit()
                except Exception as e:
                    print(e)
                    if 'SessionPasswordNeededError' in str(e) or 'Two-steps verification is enabled and a password is required' in str(e):
                        self.progress.emit(
                         '2FA Password Required. Using the password provided')

                        await client.sign_in(password=password)
                        await client.disconnect()
                        try:
                            await client.disconnected
                        except OSError:
                            print('Error on disconnect')
                        self.progress.emit('Session Created Successfully')
                        self.progress.emit(f'add_sess {sess_name}')
                        self.completed.emit()

                    elif 'The phone code entered was invalid' in str(e):
                        self.progress.emit('Wrong Telegram Code. Try again')
                    else:
                        self.progress.emit(
                            'Something went wrong. Please try again')

                self.finished.emit()
                self.finished.emit()
            except Exception as e:
                print(e)
                self.progress.emit('Something went wrong. Please try again')
                self.finished.emit()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if self.func_name == 'tele_code':
            loop.run_until_complete(tele_code())

        elif self.func_name == 'create':
            loop.run_until_complete(create())
        loop.close()
        self.finished.emit()
