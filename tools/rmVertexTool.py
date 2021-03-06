from __future__ import absolute_import

from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon, QColor

from qgis.core import QgsGeometry, QgsFeature, QgsPointXY
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker


from . import finder

class rmVertexTool(QgsMapTool):
    def __init__(self, canvas, layer, iface, action):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer
        self.iface = iface
        self.action = action
        self.rb = None
        self.vx = None
        self.threshold = float(QSettings().value('ale/threshold'))

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        if self.rb:
            self.canvas.scene().removeItem(self.rb)
        if self.vx:
            self.canvas.scene().removeItem(self.vx)
        layerPoint = self.toLayerCoordinates(self.layer, event.pos())
        (closestPointID, closestFeature) = finder.closestpoint(self.layer, layerPoint)
        polyline = closestFeature.geometry().asPolyline()
        shortestDistance = QgsGeometry.fromPointXY(polyline[closestPointID]).distance(QgsGeometry.fromPointXY(layerPoint))

        if closestPointID and shortestDistance < self.threshold:
            self.rb = QgsRubberBand(self.canvas, False)
            linePart = polyline[closestPointID-1:closestPointID+2]
            self.rb.setToGeometry(QgsGeometry.fromPolylineXY(linePart), None)
            self.rb.setColor(QColor(0, 0, 255))
            self.rb.setWidth(3)
            self.vx = QgsVertexMarker(self.canvas)
            self.vx.setCenter(QgsPointXY(polyline[closestPointID]))
            self.vx.setColor(QColor(0, 255, 0))
            self.vx.setIconSize(5)
            self.vx.setIconType(QgsVertexMarker.ICON_X)# or ICON_CROSS, ICON_BOX
            self.vx.setPenWidth(3)

    def canvasReleaseEvent(self, event):
        layerPoint = self.toLayerCoordinates(self.layer, event.pos())
        (closestPointID, closestFeature) = finder.closestpoint(self.layer, layerPoint)
        polyline = closestFeature.geometry().asPolyline()
        shortestDistance = QgsGeometry.fromPointXY(polyline[closestPointID]).distance(QgsGeometry.fromPointXY(layerPoint))
        if closestPointID and shortestDistance < self.threshold:
            ftNew = QgsFeature()
            ptsNew = polyline[closestPointID+1:]
            if len(ptsNew) > 1: # can be a linestring
                plNew = QgsGeometry.fromPolylineXY(ptsNew)
                ftNew.setGeometry(plNew)
                pr = self.layer.dataProvider()
                pr.addFeatures([ftNew])
            ptsOld = polyline[:closestPointID]
            if len(ptsOld) > 1: # can be a linestring
                plOld = QgsGeometry.fromPolylineXY(ptsOld)
                self.layer.changeGeometry(closestFeature.id(), plOld)
            else:
                self.layer.deleteFeature(closestFeature.id())

        if self.rb:
            self.canvas.scene().removeItem(self.rb)
        if self.vx:
            self.canvas.scene().removeItem(self.vx)
        self.iface.mapCanvas().refresh()

    def activate(self):
        self.action.setChecked(True)

    def deactivate(self):
        if self.rb:
            self.canvas.scene().removeItem(self.rb)
        if self.vx:
            self.canvas.scene().removeItem(self.vx)
        self.action.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True