from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
import sys
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QSplineSeries, QValueAxis, QCategoryAxis
from PyQt5.QtCore import QObject, QPointF
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
 
 
class create_chart(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.cu_widget = ''

    def remvove_widget(self):
        if self.cu_widget != '':
            self.ui.verticalLayout_3.removeWidget(self.cu_widget)
    def create_chart(self, data):

        series = QSplineSeries(self)
        chart =  QChart()
        axis_X = QValueAxis()
        axis_Y = QValueAxis()
        x_label = QCategoryAxis()
        starting_point_X = 0
        for i in reversed(data):
            starting_point_Y = data[i]
            break
        

        series.append(starting_point_X, starting_point_Y)
        x_value = 0
        y_biggest = 0

        for i in reversed(data):
            series.append(x_value, int(data[i]))
            x_label.append(i[:5], x_value)
            x_value += 1
            if int(data[i]) > y_biggest:
                y_biggest = int(data[i])

        chart.addSeries(series)
        axis_X.setTickCount(10)
        chart.addAxis(axis_X, Qt.AlignBottom)
        chart.addAxis(axis_Y, Qt.AlignLeft)

        series.attachAxis(axis_X)
        series.attachAxis(axis_Y)
        axis_X.setRange(0, len(data)-1)
        axis_Y.setRange(-y_biggest/2, y_biggest+(y_biggest*0.1))

        
        
        #chart.setAxisX(x_label, series)
        chart.setAnimationOptions(QChart.AllAnimations)
        chart.setTitle("Line Chart Example")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)
        self.cu_widget = chartview
        self.ui.verticalLayout_3.addWidget(chartview)
 