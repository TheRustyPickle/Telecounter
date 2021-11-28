from PyQt5.QtWidgets import QWidget
from pyqtgraph.Qt import QtGui as graphGui
from pyqtgraph.Qt import QtCore as graphCore
import pyqtgraph as pg
from PyQt5 import QtWidgets
import datetime
class create(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        
        self.plot = pg.PlotWidget()
        self.p2 = pg.ViewBox()

        self.all_data = {}
        self.kpi_data = {}
        self.user_data = {}
        self.button_colors = {}
        self.chart_used_buttons = {}
        self.user_names = {}
        self.rgb_colors = {}

        self.dates = []
        self.users_to_check = []

        self.p1 = ''
        self.cu_widget = ''
        self.last_date = ''

        self.hourly_selected = False
        self.all_selected = True
        self.kpi_selected = True

    def remove_widget(self):
        #remove existing widget so the new one can be placed
        try:
            if self.cu_widget != '':
                self.ui.verticalLayout_11.removeWidget(self.cu_widget)
                self.cu_widget.deleteLater()
                self.cu_widget = None
                verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding) 
                self.ui.verticalLayout_11.addWidget(verticalSpacer)
        except:
            pass

    def updateViews(self):
        #don't know what it does. taken from pyqtgraph examples
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)

    def create_chart(self, data={}, kpi_data={}, user_data={}, hourly=False, kpi_selected=True, 
                     all_selected=True, users_to_check=[], button_colors={}, chart_used_buttons={}, 
                     user_names={}, rgb_colors={}):
        
        self.hourly_selected = hourly
        self.all_selected = all_selected
        self.kpi_selected = kpi_selected
        self.users_to_check = users_to_check
        self.all_data = data
        self.kpi_data = kpi_data
        self.user_data = user_data
        self.button_colors = button_colors
        self.chart_used_buttons = chart_used_buttons
        self.user_names = user_names
        self.rgb_colors = rgb_colors
        
        data = dict(sorted(self.all_data.items()))
        
        if self.hourly_selected == False:
            #there might be dates missing between messages. So added the missing dates and put the values to 0
            first_key = list(data.keys())[0]
            last_key = list(data.keys())[-1]
            
            #convert the date INTs to datetime and go through from start to last dates and add all missing dates
            
            first_date = datetime.datetime(int(str(first_key)[:4]), int(str(first_key)[4:6]), int(str(first_key)[6:8]))
            last_date = datetime.datetime(int(str(last_key)[:4]), int(str(last_key)[4:6]), int(str(last_key)[6:8]))

            while first_date <= last_date:
                first_date += datetime.timedelta(days=1)
                int_first_date = int(first_date.strftime("%Y%m%d"))

                if int_first_date not in data:
                    data[int_first_date] = 0
                
                if int_first_date not in self.kpi_data:
                    self.kpi_data[int_first_date] = 0
                
                if int_first_date not in self.user_data:
                    self.user_data[int_first_date] = {}
        
        elif self.hourly_selected == True:
            first_key = list(data.keys())[0]
            last_key = list(data.keys())[-1]
            
            #same as dates but on hourly values
            
            first_date = datetime.datetime(int(str(first_key)[:4]), int(str(first_key)[4:6]), int(str(first_key)[6:8]), int(str(first_key)[8:]))
            last_date = datetime.datetime(int(str(last_key)[:4]), int(str(last_key)[4:6]), int(str(last_key)[6:8]), int(str(last_key)[8:]))
                    
            while first_date <= last_date:
                first_date += datetime.timedelta(hours=1)
                int_first_date = int(first_date.strftime("%Y%m%d%H"))

                if int_first_date not in data:
                    data[int_first_date] = 0
                
                if int_first_date not in self.kpi_data:
                    self.kpi_data[int_first_date] = 0
                
                if int_first_date not in self.user_data:
                    self.user_data[int_first_date] = {}
        
        data = dict(sorted(data.items()))
        self.all_data = data
        self.kpi_data = self.kpi_data
        self.user_data = self.user_data
        self.dates = []

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setBackground('w')
        xax = self.plot.getAxis('bottom')
        xax_2 = self.plot.getAxis('top')

        self.p1 = self.plot.plotItem
        self.p2 = pg.ViewBox()
        self.p1.showAxis('top')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('top').linkToView(self.p2)
        self.p2.setXLink(self.p1)

        
        axis_x_all = []
        axis_y_all = []
        axis_x_kpi = []
        axis_y_kpi = []
        x_labels = [[]]
        x_top_labels = [[]]
        num = 0
        cu_next = 0
        next_x_label = 0

        if len(data) > 10:
            next_x_label = int(len(data) / 10)

        for i in data:
            self.dates.append(i)
            axis_x_all.append(num)
            
            if self.all_selected == True:
                axis_y_all.append(data[i])
            else:
                axis_y_all.append(0)

            if cu_next != 0:
                cu_next -= 1
            else:
                new_lab = f'{str(i)[6:8]}-{str(i)[4:6]}'
                x_labels[0].append((num, new_lab))
                if self.hourly_selected == False:
                    x_top_labels[0].append((num, new_lab))
                else:
                    hour_time = f'{str(i)[8:10]}:00'
                    x_top_labels[0].append((num, hour_time))
                cu_next = next_x_label

            if i in self.kpi_data:
                axis_x_kpi.append(num)
                axis_y_kpi.append(self.kpi_data[i])
            else:
                axis_x_kpi.append(num)
                axis_y_kpi.append(0)
            num += 1

        self.updateViews()
        self.p1.vb.sigResized.connect(self.updateViews)
        self.draw_cursor()
        pg.setConfigOptions(antialias=True)
        self.plot.addLegend()
        xax.setTicks(x_labels)
        xax_2.setTicks(x_top_labels)

        if self.all_selected == True:
            self.plot.plot(axis_x_all, axis_y_all, name="Total Message", pen=pg.mkPen(self.button_colors[self.chart_used_buttons['All Count']]))
        else:
            self.plot.plot(axis_x_all, axis_y_all, pen='k')

        if self.kpi_selected == True:
            self.plot.plot(axis_x_kpi, axis_y_kpi, name='KPI Message', pen=pg.mkPen(self.button_colors[self.chart_used_buttons['KPI Count']]))

        if self.users_to_check != []:
            for user in self.users_to_check:
                user = int(user)
                user_x_value = []
                user_y_value = []
                num = 0
                for date in data:
                    user_x_value.append(num)
                    if user in self.user_data[date]:
                        user_y_value.append(int(self.user_data[date][user]))
                    else:
                        user_y_value.append(0)
                    num += 1
                legend_name = self.user_names[str(user)]
                if len(legend_name) > 25:
                    legend_name = f'{legend_name[:25]}...'
                self.plot.plot(user_x_value, user_y_value, name=f"{legend_name}", pen=pg.mkPen(self.button_colors[self.chart_used_buttons[f'{user}']]))

        self.cu_widget = self.plot
        self.ui.verticalLayout_11.addWidget(self.plot)

    def draw_cursor(self):
        #cross hair
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', width=1), label=None,
                                        labelOpts={'position':0.97, 'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('k', width=1), label='{value:0.1f}',
                                        labelOpts={'position':0.97, 'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})
        self.plot.addItem(self.hLine, ignoreBounds=True)
        self.plot.addItem(self.vLine, ignoreBounds=True)
        self.vb = self.plot.plotItem.vb
    
        #set mouse event
        self.plot.setMouseTracking(True)
        self.plot.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        try:
            if (event.type() == graphCore.QEvent.MouseMove and
                source is self.plot.viewport()):
                pos = event.pos()
                if self.plot.sceneBoundingRect().contains(pos):
                    mousePoint = self.vb.mapSceneToView(pos)
                    self.vLine.setPos(mousePoint.x())
                    self.hLine.setPos(mousePoint.y())
                    full_text = ''
                    try:
                        mousePoint = int(mousePoint.x())
                        date_time = self.dates[mousePoint]
                        if self.last_date == date_time:
                            pass
                        else:
                            readable_date = f'{str(date_time)[6:8]}-{str(date_time)[4:6]}-{str(date_time)[:4]}'
                            full_text = f"<span style=\"color:black;font-size:10pt\">Date: {readable_date}</span>"
                            if self.hourly_selected == True:
                                readable_time = f'{str(date_time)[8:10]}:00:00'
                                full_text += f"<br><span style=\"color:black;font-size:10pt\">Time: {readable_time}</span>"
                                
                            if self.all_selected:
                                all_color = self.rgb_colors[self.chart_used_buttons['All Count']]
                                full_text += f"<br><span style=\"color:{all_color};font-size:10pt\">🟦Message Count: {self.all_data[date_time]}</span>"
                            
                            if self.kpi_selected:
                                kpi_color = self.rgb_colors[self.chart_used_buttons['KPI Count']]
                                
                                if date_time in self.kpi_data:
                                    kpi_count = self.kpi_data[date_time]
                                else:
                                    kpi_count = 0
                                    
                                full_text += f"<br><span style=\"color:{kpi_color};font-size:10pt\">🟦KPI Count: {kpi_count}</span>"
                                    
                            for user in self.users_to_check:
                                user_name = self.user_names[str(user)]
                                if len(user_name) > 25:
                                    user_name = f'{user_name[:25]}...'
                                user_color = self.rgb_colors[self.chart_used_buttons[f'{user}']]
                                try:
                                    user_count = self.user_data[date_time][int(user)]
                                except:
                                    user_count = 0
                                    
                                full_text += f"<br><span style=\"color:{user_color};font-size:10pt\">🟦{user_name}: {user_count}</span>"
                                
                            self.plot.setToolTip(full_text)
                            self.last_date = date_time
                    except Exception as e:
                        self.plot.setToolTip(full_text)
                        #print(e)

            return graphGui.QWidget.eventFilter(self, source, event)
        except Exception as e:
            print(e)