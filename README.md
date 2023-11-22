# Telecounter
A GUI created with PyQt5 for counting messages in Telegram Groups from users with a Message Link or Date and comes with a chart. Requires Python 3.6+

[This project is currently being rewritten in Rust](https://github.com/TheRustyPickle/Talon)

<img src="https://dl.dropboxusercontent.com/s/n8ivmw6xoy54edr/Telecounter_1.png" alt="Telecounter_1" width="48%" > <img src="https://dl.dropboxusercontent.com/s/9m3r3nrk8ylhi7a/Telecounter_2.png" alt="Telecounter_2" width="48%" >

<h4> How to run</h4>

Download the executable from the latest [Release](https://github.com/Sakib0194/Telecounter/releases) for a one-click runnable file for Windows or Linux or download the source from Release and run Telecounter.py with the required library. The main branch may be unstable.

GUI Design tested only on Windows 10 and Arch Linux.

The GUI logo was taken randomly from Google. (looking for a logo if anyone wants to contribute)

<h4>What is a session in the GUI?</h4>

The GUI uses the Telethon library. It automatically creates a session file that saves the necessary data to automatically log in again each time you run it. All data are saved locally. All actions are done by Telegram API. It is asked to never share the session file/s with anyone. To create a session, only the phone number associated with the Telegram account and password, if applicable, are required.

<h4>What is KPI ID?</h4>

You can select any number of Telegram users individually to view their message numbers separately from all users. If you want to count total messages from 10 users out of 10k messages, this is the way to go.

<h4>What is Multi Session counting?</h4>

The GUI can distribute counting tasks among multiple Telegrams sessions by dividing them equally in parts if available, which will result in faster action and log placement. Especially useful if going for a long counting session. It can increase speed from 2x to indefinite based on the number of sessions available.
