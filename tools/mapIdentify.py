from qgis.gui import QgsMapToolIdentifyFeature, QgsMapToolIdentify
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsFeature
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import QPoint
from PyQt5.QtCore import pyqtSignal

class selectTool(QgsMapToolIdentifyFeature):
    objectFound = pyqtSignal('QgsFeature')

    def __init__(self, iface, name_shown, selection_layer):
        """
        name_shown: Name der bei Mehrfachauswahl angezeigt wird
        selection_layer: layer von dem selektiert wird
        """
        
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.layer = selection_layer
        self.name_shown = name_shown
        QgsMapToolIdentifyFeature.__init__(self, self.canvas, self.layer)
        #self.iface.currentLayerChanged.connect(self.active_changed)
        
    #def active_changed(self, layer):
    #    self.layer.removeSelection()
    #    if isinstance(layer, QgsVectorLayer) and layer.isSpatial():
    #        self.layer = layer
    #        self.setLayer(self.layer)

    def toolName(self):
        return "Kanalmanagement Objekt abfragen"
            
    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.found_features = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
            if len(self.found_features) > 1:
                menu = QMenu()
                actionList = []
                for index,f in enumerate(self.found_features):
                    action_element = QAction(text =  str(f.mFeature.attribute(self.name_shown)))
                    action_element.triggered.connect(lambda checked, index=index: self.action_clicked(index))
                    menu.addAction(action_element)
                    actionList.append(action_element)
                action_click = menu.exec_(self.canvas.mapToGlobal(QPoint(event.pos().x()+5, event.pos().y())))
            elif len(self.found_features) == 1:
                feat = self.found_features[0].mFeature
                self.layer.selectByIds([feat.attribute("fid")], QgsVectorLayer.SetSelection)
                self.objectFound.emit(feat)
            
            #self.layer.selectByIds([f.mFeature.id() for f in self.found_features], QgsVectorLayer.AddToSelection)
    def action_clicked(self, index):
        feat = self.found_features[index].mFeature
        self.layer.selectByIds([feat.attribute("fid")], QgsVectorLayer.SetSelection)
        self.objectFound.emit(feat)