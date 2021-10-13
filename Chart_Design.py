from PyQt5.QtWidgets import QWidget
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt


from pyqtgraph.Qt import QtGui as graphGui
from pyqtgraph.Qt import QtCore as graphCore
import pyqtgraph as pg
from pyqtgraph import MultiPlotWidget
from pyqtgraph.metaarray.MetaArray import axis
class create_chart(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.cu_widget = ''
        self.plot = pg.PlotWidget()
        self.p1 = ''
        self.p2 = pg.ViewBox()

    def remvove_widget(self):
        
        if self.cu_widget != '':
            self.ui.verticalLayout_3.removeWidget(self.cu_widget)
        
    def updateViews(self):
        ## view has resized; update auxiliary views to match
        self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
        
        ## need to re-update linked axes since this was called
        ## incorrectly while views had different shapes.
        ## (probably this should be handled in ViewBox.resizeEvent)
        self.p2.linkedViewChanged(self.p1.vb, self.p2.YAxis)

    def create_chart(self, data, kpi_data):
        data = dict(sorted(data.items()))
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True)
        self.plot.setBackground('w')
        xax = self.plot.getAxis('bottom')
        xax_2 = self.plot.getAxis('top')

        self.p1 = self.plot.plotItem
        self.p1.setLabels(top='axis 1')
        self.p2 = pg.ViewBox()
        self.p1.showAxis('top')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('top').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('top').setLabel('axis2', color='#0000ff')

        
        axis_x_all = []
        axis_y_all = []
        axis_x_kpi = []
        axis_y_kpi = []
        x_labels = [[]]
        num = 0
        cu_next = 0
        next_x_label = 0

        if len(data) > 12:
            next_x_label = int(len(data) / 12)

        for i in data:

            axis_x_all.append(num)
            axis_y_all.append(data[i])

            if cu_next != 0:
                cu_next -= 1
            else:
                new_lab = f'{(str(i))[6:]}-{(str(i))[4:6]}' 
                x_labels[0].append((num, new_lab))
                cu_next = next_x_label

            if i in kpi_data:
                axis_x_kpi.append(num)
                axis_y_kpi.append(kpi_data[i])
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
        xax_2.setTicks(x_labels)
        self.plot.plot(axis_x_all, axis_y_all, name="Total Message", pen='b')
        self.plot.plot(axis_x_kpi, axis_y_kpi, name='KPI Message', pen='g')
        #self.p1.plot(axis_x_all)
        #self.p1.plot(axis_x_all)
        #self.p2.addItem(pg.PlotCurveItem(axis_x_all))
        #self.p2.addItem(pg.PlotCurveItem(axis_x_all))
        self.cu_widget = self.plot
        self.ui.verticalLayout_3.addWidget(self.plot)

    def draw_cursor(self):
        #cross hair
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', width=1), label='{value:0.1f}',
                                        labelOpts={'position':0.98, 'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('k', width=1), label='{value:0.1f}',
                                        labelOpts={'position':0.98, 'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})
        self.plot.addItem(self.hLine, ignoreBounds=True)
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

            return graphGui.QWidget.eventFilter(self, source, event)
        except Exception as e:
            print(e)