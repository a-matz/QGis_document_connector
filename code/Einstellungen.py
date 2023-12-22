# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProtokolleVerknuepfen
                                 A QGIS plugin
 Werkzeuge rund um das Kanalmanagement
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-11-01
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Armin Matzl
        email                : arminmatzl@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import json
from qgis.PyQt.QtCore import  Qt, QVariant,pyqtSignal, QSignalBlocker #, QRegExp, QLine, pyqtSignal, ,
from qgis.PyQt import QtGui, QtWidgets, uic
#from qgis.utils import iface
#from qgis.gui import QgsMessageBar
from qgis.core import QgsMapLayerProxyModel,QgsExpressionContextUtils, QgsProject, QgsVectorLayer, QgsVectorFileWriter, QgsField, Qgis
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QPushButton
from osgeo import ogr
import fiona
import shutil
import sqlite3

# eigene klassen

FORM_CLASS, _ = uic.loadUiType(os.path.abspath(os.path.join(
    os.path.dirname(__file__),"../","ui", 'einstellungen.ui')))


class Einstellungen(QtWidgets.QDialog, FORM_CLASS):

    #closingPlugin = pyqtSignal()
    okpressed = pyqtSignal()
    def __init__(self,iface, parent=None):
        """Constructor."""
        super(Einstellungen, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        #self.combobox_haltungen.layerChanged.connect(self.check_input)
        #self.file_geometrie.fileChanged.connect(self.check_input)
        #self.file_sanierung.fileChanged.connect(self.check_input)

        
        self.combobox_haltungen.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.combobox_schacht.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.combobox_leitung.setFilters(QgsMapLayerProxyModel.LineLayer)

        self.combobox_haltungen.layerChanged.connect(lambda layer, typ = "haltung": self.combobox_layer_changed(layer,typ))
        self.combobox_schacht.layerChanged.connect(lambda layer, typ = "schacht": self.combobox_layer_changed(layer,typ))
        self.combobox_leitung.layerChanged.connect(lambda layer, typ = "leitung": self.combobox_layer_changed(layer,typ))

        self.h_radiobutton_1.toggled.connect(lambda: self.check_anzahl_attribute("haltung"))
        self.s_radiobutton_1.toggled.connect(lambda: self.check_anzahl_attribute("schacht"))
        self.l_radiobutton_1.toggled.connect(lambda: self.check_anzahl_attribute("leitung"))

        self.txt_trennzeichen.textChanged.connect(self.update_trennzeichen)
        

        #self.file_geometrie.setFilter("Geopackage (*.gpkg)")
        self.file_protokolle.setFilter("Geopackage (*.gpkg)")
        
        
        self.load_variables()
        
        #self.check_input()
        self.check_anzahl_attribute()

        #prevent ok button to be default
        self.buttonBox.button(QDialogButtonBox.Yes).setDefault(True)
        self.buttonBox.button(QDialogButtonBox.Yes).setVisible(False)

    def combobox_layer_changed(self,layer,typ):
        if typ == "haltung":
            with QSignalBlocker(self.combobox_haltungen_id):
                self.combobox_haltungen_id.setLayer(layer)
                if "HaltungNr" in self.combobox_haltungen_id.fields().names():
                    self.combobox_haltungen_id.setField("HaltungNr")
            #set layer combobox attribute
            self.haltung_field1.setLayer(layer)
            self.haltung_field2.setLayer(layer)
            self.combobox_haltungen_dp.setLayer(layer)
            if "ErgebnisDP" in self.combobox_haltungen_dp.fields().names():
                self.combobox_haltungen_dp.setField("ErgebnisDP")

            if "HaltungNr" in self.haltung_field1.fields().names():
                self.haltung_field1.setField("HaltungNr")
                
        elif typ == "schacht":
            with QSignalBlocker(self.combobox_schacht_id):
                self.combobox_schacht_id.setLayer(layer)
                if "SchachtNr" in self.combobox_schacht_id.fields().names():
                    self.combobox_schacht_id.setField("SchachtNr")
            #set layer combobox attribute
            self.schacht_field1.setLayer(layer)
            self.schacht_field2.setLayer(layer)
            self.combobox_schacht_dp.setLayer(layer)
            if "ErgebnisDP" in self.combobox_schacht_dp.fields().names():
                self.combobox_schacht_dp.setField("ErgebnisDP")

            if "SchachtNr" in self.schacht_field1.fields().names():
                self.schacht_field1.setField("SchachtNr")
        elif typ == "leitung":
            with QSignalBlocker(self.combobox_leitung_id):
                self.combobox_leitung_id.setLayer(layer)
                if "LeitungNr" in self.combobox_leitung_id.fields().names():
                    self.combobox_leitung_id.setField("LeitungNr")
            #set layer combobox attribute
            self.leitung_field1.setLayer(layer)
            self.leitung_field2.setLayer(layer)
            self.combobox_leitung_dp.setLayer(layer)
            if "ErgebnisDP" in self.combobox_leitung_dp.fields().names():
                self.combobox_leitung_dp.setField("ErgebnisDP")

            if "LeitungNr" in self.leitung_field1.fields().names():
                self.leitung_field1.setField("LeitungNr")

    def check_anzahl_attribute(self, typ=None):
        if typ == "haltung" or typ == None:
            #show/hide attribute and text for attribut2
            if self.h_radiobutton_1.isChecked():
                self.haltung_field2.setVisible(False)
                self.h_trenn2.setVisible(False)
                self.h_attribut2.setVisible(False)

            else:
                self.haltung_field2.setVisible(True)
                self.h_trenn2.setVisible(True)
                self.h_attribut2.setVisible(True)
        if typ == "schacht" or typ == None:
            if self.s_radiobutton_1.isChecked():
                self.schacht_field2.setVisible(False)
            else:
                self.schacht_field2.setVisible(True)
        if typ == "leitung" or typ == None:
            if self.l_radiobutton_1.isChecked():
                self.leitung_field2.setVisible(False)
            else:
                self.leitung_field2.setVisible(True)
    def set_txt_haltung(self):
        self.txt_h_typ.setText("H")
        self.txt_h_protokoll.setText("TV-Protokoll; Protokoll")
        self.txt_h_dp.setText("Druckprüfung; DP")
        self.txt_h_video.setText("Video; TV-Video")

    def set_txt_schacht(self):
        self.txt_s_typ.setText("S; BW")
        self.txt_s_protokoll.setText("Erhebungsblatt; Protokoll; Aufmassblatt")
        self.txt_s_video.setText("Video")
    
    def set_txt_leitung(self):
        self.txt_l_typ.setText("H; L")
        self.txt_l_protokoll.setText("TV-Protokoll")
        self.txt_l_video.setText("TV-Video")
    
    def set_datum(self):
        dates = [
            "%Y%m%d",
            "%d%m%Y",
            "%Y%m%d%H%M%S",
            "%d%m%Y%H%M%S"
        ]
        self.combobox_datum.addItems(dates)

    def update_trennzeichen(self):
        self.h_trenn1.setText(self.txt_trennzeichen.text())
        self.h_trenn2.setText(self.txt_trennzeichen.text())
        self.h_trenn3.setText(self.txt_trennzeichen.text())
        self.h_trenn4.setText(self.txt_trennzeichen.text())


    def load_variables(self):
        try:
            self.setup_dict = json.loads(QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('Dokumente_Setup'))
        except:
            self.setup_dict = None

        self.set_datum()
        if isinstance(self.setup_dict, dict):  
            self.txt_trennzeichen.setText(self.setup_dict["trennzeichen"])  
            self.txt_ignore.setText("; ".join(self.setup_dict["ignorieren"])) 
            self.spinbox_zoom.setValue(self.setup_dict["zoom_massstab"])
            self.file_protokolle.setFilePath(self.setup_dict["db_protokolle_path"])   
            self.checkbox_grossklein.setChecked(self.setup_dict["case_bezeichnung"])
            self.checkbox_attribut.setChecked(self.setup_dict["case_attribut"]) 
            self.checkbox_typ.setChecked(self.setup_dict["case_typ"])  
            idx_datum = self.combobox_datum.findText(self.setup_dict["datum"])
            if idx_datum != -1:
                self.combobox_datum.setCurrentIndex(idx_datum)
            else:
                self.combobox_datum.addItem(self.setup_dict["datum"])
                self.combobox_datum.setCurrentText(self.setup_dict["datum"])

            for typ in ["haltung", "schacht", "leitung"]:
                if typ in self.setup_dict.keys():
                   typ_dict = self.setup_dict[typ]
                else:
                    continue
                if typ == "haltung":
                    if typ_dict["1_attribut"]:
                        self.h_radiobutton_1.setChecked(True)
                    else:
                        self.h_radiobutton_2.setChecked(True)

                    if "layer_id" in typ_dict.keys():
                        id = typ_dict["layer_id"]

                        layer_found = False
                        for i in range(self.combobox_haltungen.count()):
                            if self.combobox_haltungen.layer(i) != None:
                                if id == self.combobox_haltungen.layer(i).id():
                                    self.combobox_haltungen.setCurrentIndex(i)
                                    layer_found = True
                                    break
                        if layer_found:
                            self.haltung_field1.setLayer(self.combobox_haltungen.currentLayer())
                            self.combobox_haltungen_id.setLayer(self.combobox_haltungen.currentLayer())
                            self.haltung_field2.setLayer(self.combobox_haltungen.currentLayer())
                            self.combobox_haltungen_dp.setLayer(self.combobox_haltungen.currentLayer())

                            self.combobox_haltungen_id.setCurrentText(typ_dict["attribut_id"])
                            if typ_dict["ergebnis_dp"] != "":
                                self.combobox_haltungen_dp.setCurrentText(typ_dict["ergebnis_dp"])
                            self.haltung_field1.setCurrentText(typ_dict["attribut1"])
                            if "attribut2" in typ_dict.keys():
                                self.haltung_field2.setCurrentText(typ_dict["attribut2"])
                            
                        else:
                            self.combobox_haltungen.setCurrentIndex(-1)
                    else:
                        self.combobox_haltungen.setCurrentIndex(-1)
                    
                    self.txt_h_protokoll.setText("; ".join(typ_dict["bezeichnung_protokoll"]))
                    self.txt_h_dp.setText("; ".join(typ_dict["bezeichnung_dp"]))
                    self.txt_h_video.setText("; ".join(typ_dict["bezeichnung_video"])) 
                    self.txt_h_typ.setText("; ".join(typ_dict["typ"]))
                elif typ == "schacht":
                    if typ_dict["1_attribut"]:
                        self.s_radiobutton_1.setChecked(True)
                    else:
                        self.s_radiobutton_2.setChecked(True)

                    if "layer_id" in typ_dict.keys():
                        id = typ_dict["layer_id"]

                        layer_found = False
                        for i in range(self.combobox_schacht.count()):
                            if self.combobox_schacht.layer(i) != None:
                                if id == self.combobox_schacht.layer(i).id():
                                    self.combobox_schacht.setCurrentIndex(i)
                                    layer_found = True
                                    break
                        if layer_found:
                            self.schacht_field1.setLayer(self.combobox_schacht.currentLayer())
                            self.combobox_schacht_id.setLayer(self.combobox_schacht.currentLayer())
                            self.schacht_field2.setLayer(self.combobox_schacht.currentLayer())
                            self.combobox_schacht_dp.setLayer(self.combobox_schacht.currentLayer())

                            self.combobox_schacht_id.setCurrentText(typ_dict["attribut_id"])
                            if typ_dict["ergebnis_dp"] != "":
                                self.combobox_schacht_dp.setCurrentText(typ_dict["ergebnis_dp"])
                            self.schacht_field1.setCurrentText(typ_dict["attribut1"])
                            if "attribut2" in typ_dict.keys():
                                self.schacht_field2.setCurrentText(typ_dict["attribut2"])
                        
                        else:
                            self.combobox_schacht.setCurrentIndex(-1)
                    else:
                        self.combobox_schacht.setCurrentIndex(-1)
                    
                    self.txt_s_protokoll.setText("; ".join(typ_dict["bezeichnung_protokoll"]))
                    self.txt_s_dp.setText("; ".join(typ_dict["bezeichnung_dp"]))
                    self.txt_s_video.setText("; ".join(typ_dict["bezeichnung_video"])) 
                    self.txt_s_typ.setText("; ".join(typ_dict["typ"]))
                elif typ == "leitung":
                    if typ_dict["1_attribut"]:
                        self.l_radiobutton_1.setChecked(True)
                    else:
                        self.l_radiobutton_2.setChecked(True)

                    if "layer_id" in typ_dict.keys():
                        id = typ_dict["layer_id"]

                        layer_found = False
                        for i in range(self.combobox_leitung.count()):
                            if self.combobox_leitung.layer(i) != None:
                                if id == self.combobox_leitung.layer(i).id():
                                    self.combobox_leitung.setCurrentIndex(i)
                                    layer_found = True
                                    break
                        if layer_found:
                            self.leitung_field1.setLayer(self.combobox_leitung.currentLayer())
                            self.combobox_leitung_id.setLayer(self.combobox_leitung.currentLayer())
                            self.combobox_leitung_dp.setLayer(self.combobox_leitung.currentLayer())
                            self.leitung_field2.setLayer(self.combobox_leitung.currentLayer())

                            self.combobox_leitung_id.setCurrentText(typ_dict["attribut_id"])
                            if typ_dict["ergebnis_dp"] != "":
                                self.combobox_leitung_dp.setCurrentText(typ_dict["ergebnis_dp"])
                            self.leitung_field1.setCurrentText(typ_dict["attribut1"])
                            if "attribut2" in typ_dict.keys():
                                self.leitung_field2.setCurrentText(typ_dict["attribut2"])
                        
                        else:
                            self.combobox_leitung.setCurrentIndex(-1)
                    else:
                        self.combobox_leitung.setCurrentIndex(-1)
                    
                    self.txt_l_protokoll.setText("; ".join(typ_dict["bezeichnung_protokoll"]))
                    self.txt_l_dp.setText("; ".join(typ_dict["bezeichnung_dp"]))
                    self.txt_l_video.setText("; ".join(typ_dict["bezeichnung_video"])) 
                    self.txt_l_typ.setText("; ".join(typ_dict["typ"]))

            
           
            
        else:
            self.reset_combobox()
            self.txt_trennzeichen.setText("_")
            self.txt_ignore.setText("txt; ipf; bak")
            self.set_txt_haltung()
            self.set_txt_schacht()
            self.set_txt_leitung()

          

    def reset_combobox(self):
        self.combobox_haltungen.setCurrentIndex(-1)
        self.combobox_schacht.setCurrentIndex(-1)
        self.combobox_leitung.setCurrentIndex(-1)

    """def check_input(self):
        if os.path.isfile(self.file_geometrie.filePath()) and os.path.isfile(self.file_sanierung.filePath()) and self.combobox_haltungen.currentText() != "":
            return True
        else:
            return False"""
    
    def accept(self):
        self.setCursor(Qt.WaitCursor)

        if not isinstance(self.setup_dict, dict):
            self.setup_dict = {}
            self.setup_dict["haltung"] = {}
            self.setup_dict["schacht"] = {}
            self.setup_dict["leitung"] = {}
        
        #settings for haltung
        if self.combobox_haltungen.currentIndex() != -1 and self.combobox_haltungen.currentLayer() != None:
            self.setup_dict["haltung"]["layer_id"] = self.combobox_haltungen.currentLayer().id()
        else:
            self.setup_dict["haltung"]["layer_id"] = None
        if self.combobox_haltungen_id.currentIndex() != -1:
            self.setup_dict["haltung"]["attribut_id"] = self.combobox_haltungen_id.currentField()
        else:
            self.setup_dict["haltung"]["attribut_id"] = None
        if self.haltung_field1.currentIndex() != -1:
            self.setup_dict["haltung"]["attribut1"] = self.haltung_field1.currentField()
        else:
            self.setup_dict["haltung"]["attribut1"] = None
        if self.haltung_field1.currentIndex() != -1 and  self.h_radiobutton_2.isChecked():
            self.setup_dict["haltung"]["attribut2"] = self.haltung_field2.currentField()
        else:
            self.setup_dict["haltung"]["attribut2"] = None
        
        self.setup_dict["haltung"]["typ"] = [txt.strip() for txt in self.txt_h_typ.text().split(";")]
        self.setup_dict["haltung"]["bezeichnung_protokoll"] = [txt.strip() for txt in self.txt_h_protokoll.text().split(";")]
        self.setup_dict["haltung"]["bezeichnung_dp"] = [txt.strip() for txt in self.txt_h_dp.text().split(";")]
        self.setup_dict["haltung"]["bezeichnung_video"] = [txt.strip() for txt in self.txt_h_video.text().split(";")]
        self.setup_dict["haltung"]["1_attribut"] = self.h_radiobutton_1.isChecked()
        self.setup_dict["haltung"]["ergebnis_dp"] = self.combobox_haltungen_dp.currentField()

        #settings for schacht
        if self.combobox_schacht.currentIndex() != -1 and self.combobox_schacht.currentLayer() != None:
            self.setup_dict["schacht"]["layer_id"] = self.combobox_schacht.currentLayer().id()
        else:
            self.setup_dict["schacht"]["layer_id"] = None
        if self.combobox_schacht_id.currentIndex() != -1:
            self.setup_dict["schacht"]["attribut_id"] = self.combobox_schacht_id.currentField()
        else:
            self.setup_dict["schacht"]["attribut_id"] = None
        if self.schacht_field1.currentIndex() != -1:
            self.setup_dict["schacht"]["attribut1"] = self.schacht_field1.currentField()
        else:
            self.setup_dict["schacht"]["attribut1"] = None
        if self.schacht_field1.currentIndex() != -1 and  self.s_radiobutton_2.isChecked():
            self.setup_dict["schacht"]["attribut2"] = self.schacht_field2.currentField()
        else:
            self.setup_dict["schacht"]["attribut2"] = None

        self.setup_dict["schacht"]["typ"] = [txt.strip() for txt in self.txt_s_typ.text().split(";")]
        self.setup_dict["schacht"]["bezeichnung_protokoll"] = [txt.strip() for txt in self.txt_s_protokoll.text().split(";")]
        self.setup_dict["schacht"]["bezeichnung_dp"] = [txt.strip() for txt in self.txt_s_dp.text().split(";")]
        self.setup_dict["schacht"]["bezeichnung_video"] = [txt.strip() for txt in self.txt_s_video.text().split(";")]
        self.setup_dict["schacht"]["1_attribut"] = self.s_radiobutton_1.isChecked()
        self.setup_dict["schacht"]["ergebnis_dp"] = self.combobox_schacht_dp.currentField()

        #settings for leitung
        if self.combobox_leitung.currentIndex() != -1 and self.combobox_leitung.currentLayer() != None:
                self.setup_dict["leitung"]["layer_id"] = self.combobox_leitung.currentLayer().id()
        else:
            self.setup_dict["leitung"]["layer_id"] = None
        if self.combobox_leitung_id.currentIndex() != -1:
            self.setup_dict["leitung"]["attribut_id"] = self.combobox_leitung_id.currentField()
        else:
            self.setup_dict["leitung"]["attribut_id"] = None
        if self.leitung_field1.currentIndex() != -1:
            self.setup_dict["leitung"]["attribut1"] = self.leitung_field1.currentField()
        else:
            self.setup_dict["leitung"]["attribut1"] = None
        if self.leitung_field1.currentIndex() != -1 and  self.l_radiobutton_2.isChecked():
            self.setup_dict["leitung"]["attribut2"] = self.leitung_field2.currentField()
        else:
            self.setup_dict["leitung"]["attribut2"] = None

        self.setup_dict["leitung"]["typ"] = [txt.strip() for txt in self.txt_l_typ.text().split(";")]
        self.setup_dict["leitung"]["bezeichnung_protokoll"] = [txt.strip() for txt in self.txt_l_protokoll.text().split(";")]
        self.setup_dict["leitung"]["bezeichnung_dp"] = [txt.strip() for txt in self.txt_l_dp.text().split(";")]
        self.setup_dict["leitung"]["bezeichnung_video"] = [txt.strip() for txt in self.txt_l_video.text().split(";")]
        self.setup_dict["leitung"]["1_attribut"] = self.l_radiobutton_1.isChecked()
        self.setup_dict["leitung"]["ergebnis_dp"] = self.combobox_leitung_dp.currentField()
        
        self.setup_dict["trennzeichen"] = self.txt_trennzeichen.text()
        self.setup_dict["datum"] = self.combobox_datum.currentText()
        self.setup_dict["case_bezeichnung"] = self.checkbox_grossklein.isChecked()
        self.setup_dict["case_attribut"] = self.checkbox_attribut.isChecked()
        self.setup_dict["case_typ"] = self.checkbox_typ.isChecked()
        self.setup_dict["zoom_massstab"] = self.spinbox_zoom.value()
        self.setup_dict["ignorieren"] = [txt.strip().lower() for txt in self.txt_ignore.text().split(";")]

        # Protokolle 
        self.setup_dict["db_protokolle_path"] = self.file_protokolle.filePath()

        dict_string = json.dumps(self.setup_dict)
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(),'Dokumente_Setup',dict_string)

        self.okpressed.emit()
        self.setCursor(Qt.ArrowCursor)
        self.close()
        self.deleteLater()

class InputChecker():
    """
    Prüft, ob die in der QGis-Projektdatei gespeicherten Variablen vorhanden und gültig sind
    Die Variablen sind als json gespeichert und werden als dictionary eingelesen.
    Für jeden Abschnitt gibt es wieder ein eigenes dictionary:
    allg_einstellungen
    detailsanierungsplanung_setup
    protokolle_setup
    Diese enthalten wiederum Variablen die auf deren Gültigkeit geprüft werden
    Für jeden Abschnitt wird True/False zurückgegeben.
    Hardcoded: KaHaltung muss in Kanal DB sein
    weitere Prüfung:
    Die Sanierungsdatenbank wird inhaltlich geprüft und Abgeglichen mit der vorlage im Ordner 'development'.
    Wenn Attribute oder Layer fehlen dann können diese erzeugt werden.
    """
    def __init__(self):
        pass
    
    def check_input(self):
        # check ob variable überhaupt vorhanden ist
        try:
            self.setup_dict = json.loads(QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('Dokumente_Setup'))
        except:
            return False, False, False, None
        
        # chek allgemeine einstellungen
        allg_einstellungen = True
        try:
            # maßstab muss > 0 sein
            if self.setup_dict["allg_einstellungen"]["zoom_massstab"] <= 0:
                allg_einstellungen = False

            # haltunglayer und schachtlayer müssen vorhanden sein
            if QgsProject.instance().mapLayer(self.setup_dict["allg_einstellungen"]["Haltung_layer_id"]) == None or \
            QgsProject.instance().mapLayer(self.setup_dict["allg_einstellungen"]["Schacht_layer_id"]) == None:
                allg_einstellungen = False
            
            #check if db is file
            if not os.path.isfile(self.setup_dict["allg_einstellungen"]["db_kanal_path"]):
                allg_einstellungen = False
            
            # ka haltung muss in datenbank vorhanden sein
            if not QgsVectorLayer(self.setup_dict["allg_einstellungen"]["db_kanal_path"]+"|layername=KaHaltung", "Haltung", "ogr").isValid():
                allg_einstellungen = False
        except:
            allg_einstellungen = False
        #check detailsanierungseinstellungen
        detailsanierungsplanung = True
        san_db = None
        #try:
        # datei muss vorhanden sein
        san_db = self.setup_dict["detailsanierungsplanung_setup"]["db_sanierung_path"]
        if not os.path.isfile(san_db):
            detailsanierungsplanung = False
        else:
            # san_db muss inhaltlich korrekt sein
            detailsanierungsplanung = self.check_san_db_aktuell(san_db)
        # variantenauswahl und sanierungsmethoden müssen definiert sein
        if not all(x in self.setup_dict["detailsanierungsplanung_setup"].keys() for x in ("variantenauswahl","sanierungsmethoden")):
            detailsanierungsplanung = False
            
        """layer_namen = ["Haltungen_Massnahmen", "Sanierungsmassnahmen","Sanierungsbibliothek",
                        "Schacht_Sanierungskonzept","Haltung_Sanierungskonzept"]
        for layer in layer_namen:
            if not QgsVectorLayer(san_db+f"|layername={layer}", layer, "ogr"):
                detailsanierungsplanung = False"""
        #except:
        #    detailsanierungsplanung = False

        # check protokolle input
        protokolle = True
        try:
            if not os.path.isfile(self.setup_dict["protokolle_setup"]["db_protokolle_path"]):
                protokolle = False

            layer_namen = ["Inspektionsdaten_Haltung", "Inspektionsdaten_Schacht"]
            for layer in layer_namen:
                if not QgsVectorLayer(self.setup_dict["protokolle_setup"]["db_protokolle_path"]+f"|layername={layer}", layer, "ogr").isValid():
                    protokolle = False
        except:
            protokolle = False

        return allg_einstellungen, protokolle, detailsanierungsplanung, san_db


    def get_layer_dict(self,db):
        if os.path.isfile(db):
            sublayers = fiona.listlayers(db)

            layers_dict = {}
            for sublayer in sublayers:
                uri = f"{db}|layername={sublayer}"
                # Create layer
                sub_vlayer = QgsVectorLayer(uri, sublayer, 'ogr')
                # add to dict
                fields = {}
                for field in sub_vlayer.fields():
                    fields[field.name()] = [field.typeName(),field.type()]
                layers_dict[sub_vlayer.name()] = fields
            return layers_dict

    def check_san_db_aktuell(self, san_db):
        original_db = os.path.abspath(os.path.join(os.path.dirname(__file__),"..","development","Sanierungsdatenbank.gpkg"))
        original_dict = self.get_layer_dict(original_db)
        san_dict = self.get_layer_dict(san_db)
        db_ok = True
        layer_fehlt = []
        for original_layer in original_dict.keys():
            if original_layer in san_dict:
                for attribute_name in original_dict[original_layer].keys():
                    #wenn attributname nicht in verknüpfter db ist
                    if not attribute_name in san_dict[original_layer]:
                        #userinput fragen
                        fortfahren =QMessageBox.warning(None,"Kanalmanagement-Plugin!",f"Das Attribut <b>{attribute_name}</b> fehlt im Layer <b>{original_layer}</b> in der Sanierungsdatenbank.<br><br>Datenbank: <b>{san_db}</b><br>Layer: <b>{original_layer}</b><br>Attribut: <b>{attribute_name}</b><br>Datentyp: <b>{original_dict[original_layer][attribute_name][0]}</b><br><br>Soll das Attribut eingefügt werden? (empfohlen)", QMessageBox.Yes|QMessageBox.No)
                        #wenn bestätigt dann neues attribut einfügen
                        if fortfahren == QMessageBox.Yes:
                            layer = QgsVectorLayer(f"{san_db}|layername={original_layer}",original_layer,"ogr")
                            pr = layer.dataProvider()
                            pr.addAttributes([QgsField(attribute_name,original_dict[original_layer][attribute_name][1])])
                            layer.updateFields()
                            print(f"Attribut fehlt! {attribute_name}")
                        else:
                            db_ok = False
                    else:
                        if original_dict[original_layer][attribute_name][0] != san_dict[original_layer][attribute_name][0]:
                            QMessageBox.warning(None,"Kanalmanagement-Plugin!",f"Das Attribut <b>{attribute_name}</b> im Layer <b>{original_layer}</b> hat den falschen Datentyp!<br><br> Um Datenverlust zu vermeiden bitte manuell korrigieren.<br><br>Layer: <b>{original_layer}</b><br>Attribut: <b>{attribute_name}</b><br>Datentyp soll: <b>{original_dict[original_layer][attribute_name][0]}</b><br>Datentyp ist: <b>{san_dict[original_layer][attribute_name][0]}", QMessageBox.Cancel)
                            return False
            else:
                layer_fehlt.append(original_layer)
            
        if len(layer_fehlt) > 0:
            if len(layer_fehlt) > 1:
                txt_fehlt = "fehlen"
                txt_falsch = "Durch die Anzahl an fehlenden Layern besteht die Möglichkeit, dass eine falsche Datenbank verknüpft ist.<br><br>"
            else:
                txt_fehlt = "fehlt"
                txt_falsch = ""
            layer_txt = "<br>".join(layer_fehlt)
            fortfahren = QMessageBox.warning(None,"Kanalmanagement-Plugin!",f"In der Sanierungsdatenbank {txt_fehlt} {len(layer_fehlt)} Layer.<br><br>Aktuell ist die Datenbank <b>{san_db}</b> mit dem Projekt verknüpft.<br><br>{txt_falsch}Sollen folgende Layer erstellt werden:<br><b>{layer_txt}</b>", QMessageBox.Yes|QMessageBox.No)
            if fortfahren == QMessageBox.Yes:
                for layer_erstellen in layer_fehlt:
                    print(layer_erstellen)
                    layer = QgsVectorLayer(f"{original_db}|layername={layer_erstellen}",layer_erstellen,"ogr")
                    options = QgsVectorFileWriter.SaveVectorOptions()
                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                    options.layerName = layer_erstellen
                    _writer = QgsVectorFileWriter.writeAsVectorFormat(layer, san_db, options)
            else:
                db_ok = False

        return db_ok
