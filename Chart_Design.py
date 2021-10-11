from PyQt5.QtWidgets import QWidget
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt
 
 
class create_chart(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.cu_widget = ''

    def remvove_widget(self):
        
        if self.cu_widget != '':
            self.ui.verticalLayout_3.removeWidget(self.cu_widget)

    def create_chart(self, data, kpi_data):

        series = QLineSeries(self)
        series_2 = QLineSeries(self)
        chart =  QChart()
        axis_X = QValueAxis()
        axis_Y = QValueAxis()
        x_label = QCategoryAxis()
        blue_col = QPen(Qt.blue)
        blue_col.setWidth(1)

        green_col = QPen(Qt.green)
        green_col.setWidth(1)

        starting_point_X = 0
        kpi_point_X = 0
        for i in data:
            starting_point_Y = data[i]
            break

        series.append(starting_point_X, starting_point_Y)
        x_value = 0
        y_biggest = 0
        

        for i in data:
            series.append(x_value, int(data[i]))
            x_label.append(' ', x_value)    #to keep x axis lable hidden

            if x_value == 0:
                if i in kpi_data:
                    kpi_point_Y = int(kpi_data[i])
                else:
                    kpi_point_Y = 0 #add starting point to series_2 on the first loop round
                series_2.append(kpi_point_X, kpi_point_Y)

            if i in kpi_data:
                series_2.append(x_value, int(kpi_data[i]))
            else:
                series_2.append(x_value, 0)

            x_value += 1
            if int(data[i]) > y_biggest:
                y_biggest = int(data[i])
            
        chart.addSeries(series_2)
        chart.addSeries(series)
        series.setPen(blue_col)
        series_2.setPen(green_col)
        axis_X.setTickCount(10)
        axis_Y.setTickCount(8)
        chart.addAxis(axis_X, Qt.AlignBottom)
        chart.addAxis(axis_Y, Qt.AlignLeft)

        series.attachAxis(axis_X)
        series.attachAxis(axis_Y)
        series_2.attachAxis(axis_X)
        series_2.attachAxis(axis_Y)
        axis_X.setRange(0, len(data)-1)
        axis_Y.setRange(0, y_biggest+(y_biggest*0.1))

        chart.legend().setVisible(False)
        chart.setAxisX(x_label, series)
        chart.setAnimationOptions(QChart.AllAnimations)
        chart.setTitle("Message Count Comparison Chart")
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)
        self.cu_widget = chartview
        self.ui.verticalLayout_3.addWidget(chartview)
 