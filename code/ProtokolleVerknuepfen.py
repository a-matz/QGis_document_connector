# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KanalManagementDockWidget
                                 A QGIS plugin
 Werkzeuge rund um das Kanalmanagement
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-12-10
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Armin Matzl
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
import glob
import pandas as pd
from osgeo import ogr
from datetime import datetime
import sqlite3
from qgis.PyQt.QtCore import Qt, QVariant, pyqtSignal #,QRegExp, QLine, , QSignalBlocker
from qgis.PyQt import QtGui, QtWidgets, uic
#from qgis.utils import iface
from qgis.core import QgsExpressionContextUtils, QgsProject, QgsVectorFileWriter,QgsProcessing, QgsField, QgsVectorLayer
from qgis.PyQt.QtWidgets import QDialog,QMessageBox, QProgressDialog
import processing
# eigene klassen

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__),"../","ui", 'protokolle_verknuepfen.ui'))


class Link(QtWidgets.QDialog, FORM_CLASS):

    #closingPlugin = pyqtSignal()
    okpressed = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(Link, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        #self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.directory_outputDB.fileChanged.connect(self.check_input)
        self.directory_files.fileChanged.connect(self.check_input)
        self.directory_outputDB.setFilter("Geopackage (*.gpkg)")
        
        self.check_input()
        try:
            self.setup_dict = json.loads(QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('Dokumente_Setup'))
            self.load_variables()
        except:
            self.setup_dict = None

        
        #self.check_input()

    def check_input(self):
        if os.path.isdir(self.directory_files.filePath()) and os.path.isdir(os.path.dirname(self.directory_outputDB.filePath())):
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def load_variables(self):
        if isinstance(self.setup_dict,dict):
            if "protokolle_setup" in self.setup_dict:
                if os.path.isfile(self.setup_dict["db_protokolle_path"]):
                    self.directory_outputDB.setFilePath(self.setup_dict["db_protokolle_path"])

    def write_path(self):
        self.setup_dict["db_protokolle_path"] = self.directory_outputDB.filePath()
        
        dict_string = json.dumps(self.setup_dict)
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(),'Dokumente_Setup',dict_string)
        
    def remove_duplicates(self, tabelle):
        db = self.directory_outputDB.filePath()
        alg_params = {
            'FIELDS': ['pfad'],
            'INPUT' : db + f"|layername={tabelle}",
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }

        out = processing.run('native:removeduplicatesbyattribute', alg_params)
        out_layer = out["OUTPUT"]

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer 
        options.layerName = tabelle
        _writer = QgsVectorFileWriter.writeAsVectorFormat(out_layer, db, options)

    
    def accept(self):        
        self.setCursor(Qt.WaitCursor)

        if self.checkbox_subdir.isChecked():
            files = glob.glob(self.directory_files.filePath() + '/**/*', recursive=True)
        else:
            files = glob.glob(self.directory_files.filePath() + "/*")

        #prog.setMaximum(len(files)-1)

        datei = [d for d in files if os.path.isfile(d)]
        objekt = {
        "pfad" : [],
        "attribut1" : [],
        "attribut2" : [],
        "typ" : [],
        "bezeichnung" : [],
        "datum" : [],
        "zusatz" : [],
        "endung" : []
        }

        for i,f in enumerate(datei):
            
            #if prog.wasCanceled():
            #    break
            name, extension = os.path.splitext(f)
            #name = name.lower()
            text_glieder = os.path.basename(name).split(self.setup_dict["trennzeichen"])
            #prüfen ob aktuelle datei relevant ist und ob durch 1 oder 2 attribute definiert
            # irrelevant: typ nicht in dateiname
            # 1 attribut: typ an 2.stelle
            # 2 attribute: typ an 3.stelle
            typ_liste = self.setup_dict["haltung"]["typ"] + self.setup_dict["schacht"]["typ"] + self.setup_dict["leitung"]["typ"]
            try:
                if text_glieder[1] in typ_liste: #typ passt an 2. stelle
                    attribute = 1
                elif text_glieder[2] in typ_liste: #typ passt an 3. stelle
                    attribute = 2
                else:
                    continue #datei nicht relevant
            except:
                continue #datei nicht relevant

            if len(text_glieder) > 2 + attribute:
                objekt["pfad"].append(f)
                objekt["attribut1"].append(text_glieder[0])
                if attribute == 2:
                    objekt["attribut2"].append(text_glieder[1])
                else:
                    objekt["attribut2"].append(None)
                objekt["typ"].append(text_glieder[attribute])
                objekt["bezeichnung"].append(text_glieder[attribute+1])
                try:
                    objekt["datum"].append(datetime.strptime(text_glieder[attribute+2].strip(), self.setup_dict["datum"]))
                except:
                    objekt["datum"].append(datetime.strptime("19800101".strip(), "%Y%m%d"))
                objekt["endung"].append(extension.replace(".","").lower())
                if len(text_glieder) > 3+attribute:
                    objekt["zusatz"].append("-".join(text_glieder[attribute+3:]))
                else:
                    objekt["zusatz"].append(None)
            # wenn eine Datei kein Datum hat dann trotzdem übernehmen - Anlass:Schachterhebungsblätter teilweise ohne Datum
            elif len(text_glieder) == 2 + attribute:
                objekt["pfad"].append(f)
                objekt["attribut1"].append(text_glieder[0])
                if attribute == 2:
                    objekt["attribut2"].append(text_glieder[1])
                else:
                    objekt["attribut2"].append(None)
                objekt["typ"].append(text_glieder[attribute])
                objekt["bezeichnung"].append(text_glieder[attribute+1])
                objekt["datum"].append(datetime.strptime("19800101".strip(), "%Y%m%d"))
                objekt["endung"].append(extension.replace(".","").lower())
                objekt["zusatz"].append(None)
                
            #prog.setValue(i)
                    
        print(objekt)
        df = pd.DataFrame.from_dict(objekt)
        df = df[~df.endung.isin(self.setup_dict["ignorieren"])]
        schacht_daten = df.loc[df["typ"].isin(self.setup_dict["schacht"]["typ"])]
        haltung_daten = df.loc[df["typ"].isin(self.setup_dict["haltung"]["typ"])]
        leitung_daten = df.loc[df["typ"].isin(self.setup_dict["leitung"]["typ"])]

        fin_db = self.directory_outputDB.filePath().replace("/","\\")

        if self.checkbox_append.isChecked() and os.path.isfile(fin_db):
            methode = "append"
        else:
            methode = "replace"
            # create new dbase
            gpkg_driver = ogr.GetDriverByName("GPKG")
            source = gpkg_driver.CreateDataSource(fin_db)
            attribute_list = [
                QgsField("pfad", QVariant.String),
                QgsField("attribut1",  QVariant.String),
                QgsField("attribut2",  QVariant.String),
                QgsField("typ", QVariant.String),
                QgsField("bezeichnung", QVariant.String),
                QgsField("datum", QVariant.Date),
                QgsField("zusatz", QVariant.String),
                QgsField("endung", QVariant.String)
                ]

            layer = QgsVectorLayer("None", "Inspektionsdaten", "memory")
            pr = layer.dataProvider()
            pr.addAttributes(attribute_list)
            layer.updateFields()
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            #options.layerName = "Dateien"
            #_writer = QgsVectorFileWriter.writeAsVectorFormat(layer, fin_db, options)
            options.layerName = "Dateien_Schacht"
            _writer = QgsVectorFileWriter.writeAsVectorFormat(layer, fin_db, options)
            options.layerName = "Dateien_Haltung"
            _writer = QgsVectorFileWriter.writeAsVectorFormat(layer, fin_db, options)
            options.layerName = "Dateien_Leitung"
            _writer = QgsVectorFileWriter.writeAsVectorFormat(layer, fin_db, options)


        con = sqlite3.connect(fin_db)
        #df.to_sql('Dateien', con, if_exists="append", index = False)
        if len(schacht_daten.index) > 0:
            schacht_daten.to_sql('Dateien_Schacht', con, if_exists="append", index = False)
        if len(haltung_daten.index) > 0:
            haltung_daten.to_sql('Dateien_Haltung', con, if_exists="append", index = False)
        if len(leitung_daten.index) > 0:
            leitung_daten.to_sql('Dateien_Leitung', con, if_exists="append", index = False)
        con.close()

        if self.checkbox_useInCurrentProject.isChecked():
            self.write_path()
        
        if self.checkbox_removeDuplicates.isChecked():
            self.remove_duplicates("Dateien_Schacht")
            self.remove_duplicates("Dateien_Haltung")

        self.close()
        self.setCursor(Qt.ArrowCursor)
        self.okpressed.emit()
        self.deleteLater()
        QMessageBox.information(self,"Information", "Protokolle erfolgreich eingelesen.")
    """   
    def reject(self):
        self.close()
    """