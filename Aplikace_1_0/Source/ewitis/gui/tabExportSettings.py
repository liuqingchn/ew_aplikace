# -*- coding: utf-8 -*-
'''
Created on 8.12.2013

@author: Meloun
'''

from PyQt4 import QtCore
from ewitis.data.DEF_ENUM_STRINGS import *
from ewitis.gui.UiAccesories import uiAccesories
from ewitis.gui.Ui import Ui
from ewitis.data.dstore import dstore
import libs.utils.utils as utils


class ExportGroup():
    
    def __init__(self,  nr):
        '''
        Constructor
        group items as class members
        format groupCell_1, checkCell_1.. groupCell_2, checkCell_2 
        '''
        ui = Ui()
        
        self.nr = nr
        self.year = getattr(ui, "checkExportYear_" + str(nr))        
        self.sex = getattr(ui, "checkExportSex_" + str(nr))        
        self.club = getattr(ui, "checkExportClub_" + str(nr))        
        self.laps = getattr(ui, "checkExportLaps_" + str(nr))        
        self.laptime = getattr(ui, "checkExportLaptime_" + str(nr))        
        self.bestlaptime = getattr(ui, "checkExportBestLaptime_" + str(nr))
                
        self.option = [None] * NUMBER_OF.OPTIONCOLUMNS                
        for i in range(0, NUMBER_OF.OPTIONCOLUMNS):
            self.option[i] = getattr(ui, "checkExportOption_"+str(i+1)+"_" + str(nr))        
        self.optionname = getattr(ui, "lineExportOptionname_"+str(nr+1))
                                
        self.gap = getattr(ui, "checkExportGap_" + str(nr))
                
        self.points = [None] * NUMBER_OF.OPTIONCOLUMNS
        for i in range(0, NUMBER_OF.POINTS):
            self.points[i] = getattr(ui, "checkExportPoints_"+str(i+1)+"_" + str(nr))                                                   
                    
        
    def Init(self):        
        self.Update()
        self.createSlots()            

    def CreateSlots(self):                
 
        #export
        QtCore.QObject.connect(self.year, QtCore.SIGNAL("stateChanged(int)"), lambda state: uiAccesories.sGuiSetItem("export", [self.nr, "year"], state, self.Update))                                
        QtCore.QObject.connect(self.sex, QtCore.SIGNAL("stateChanged(int)"), lambda state: uiAccesories.sGuiSetItem("export", [self.nr, "sex"], state, self.Update))                                
        QtCore.QObject.connect(self.club, QtCore.SIGNAL("stateChanged(int)"), lambda state: uiAccesories.sGuiSetItem("export", [self.nr, "club"], state, self.Update))                                
        QtCore.QObject.connect(self.laps, QtCore.SIGNAL("stateChanged(int)"), lambda state: uiAccesories.sGuiSetItem("export", [self.nr, "laps"], state, self.Update))                                
        QtCore.QObject.connect(self.laptime, QtCore.SIGNAL("stateChanged(int)"), lambda state: uiAccesories.sGuiSetItem("export", [self.nr, "laptime"], state, self.Update))
        QtCore.QObject.connect(self.bestlaptime, QtCore.SIGNAL("stateChanged(int)"), lambda state: uiAccesories.sGuiSetItem("export", [self.nr, "best_laptime"], state, self.Update))
                                
        for i in range(0, NUMBER_OF.OPTIONCOLUMNS):  
            QtCore.QObject.connect(self.option[i], QtCore.SIGNAL("stateChanged(int)"), lambda state, index = i: uiAccesories.sGuiSetItem("export", [self.nr, "option", index], state, self.Update))
            QtCore.QObject.connect(self.optionname, QtCore.SIGNAL("textEdited(const QString&)"), lambda name, index = i: uiAccesories.sGuiSetItem("export", [self.nr, "optionname", index], utils.toUnicode(name)))
            

        QtCore.QObject.connect(self.gap, QtCore.SIGNAL("stateChanged(int)"), lambda state: uiAccesories.sGuiSetItem("export", [self.nr, "gap"], state, self.Update))
        for i in range(0, NUMBER_OF.POINTS):
            QtCore.QObject.connect(self.points[i], QtCore.SIGNAL("stateChanged(int)"), lambda state, index = i: uiAccesories.sGuiSetItem("export", [self.nr, "points", index], state, self.Update)) 
                
        
        
    
    def GetInfo(self):
        print self.nr
        print  dstore.Get("export") 
        return dstore.GetItem("export", [self.nr-1])          

    
    def Update(self):
        export_info = self.GetInfo()
        
        self.year.setCheckState(export_info["year"])                                
        self.sex.setCheckState(export_info["sex"])                                
        self.club.setCheckState(export_info["club"])                                
        self.laps.setCheckState(export_info["laps"])                                
        self.laptime.setCheckState(export_info["laptime"])
        self.bestlaptime.setCheckState(export_info["best_laptime"])
        for i in range(0, NUMBER_OF.OPTIONCOLUMNS):                                                                        
            self.option[i].setCheckState(export_info["option"][i])
        self.optionname.setText(export_info["optionname"][i])
        self.gap.setCheckState(export_info["gap"])
        for i in range(0, NUMBER_OF.POINTS):                
            self.points[i].setCheckState(export_info["points"][i])
        
        

class TabExportSettings():    
      
    def __init__(self):
        '''
        Constructor
        '''        
        print "tabExportSettings: constructor"        
        
    def Init(self):                     
        self.addSlots()
        
    def addSlots(self):        
               
        print "tabExportSettings: adding slots"
        
        #exportgroups - year, club, etc.
        self.exportgroups = [None] * NUMBER_OF.EXPORTS
        for i in range(0, NUMBER_OF.EXPORTS):            
            self.exportgroups[i] = ExportGroup(i+1)
            self.exportgroups[i].CreateSlots()
            
        QtCore.QObject.connect(Ui().radioExportLapsTimes,      QtCore.SIGNAL("toggled(bool)"), lambda index: uiAccesories.sGuiSetItem("export", ["lapsformat"], 0, self.Update) if index else None)
        QtCore.QObject.connect(Ui().radioExportLapsLaptimes,  QtCore.SIGNAL("toggled(bool)"), lambda index: uiAccesories.sGuiSetItem("export", ["lapsformat"], 1, self.Update) if index else None) 
        QtCore.QObject.connect(Ui().radioExportLapsPoints_1,  QtCore.SIGNAL("toggled(bool)"), lambda index: uiAccesories.sGuiSetItem("export", ["lapsformat"], 2, self.Update) if index else None) 
        QtCore.QObject.connect(Ui().radioExportLapsPoints_2,  QtCore.SIGNAL("toggled(bool)"), lambda index: uiAccesories.sGuiSetItem("export", ["lapsformat"], 3, self.Update) if index else None) 
        QtCore.QObject.connect(Ui().radioExportLapsPoints_3,  QtCore.SIGNAL("toggled(bool)"), lambda index: uiAccesories.sGuiSetItem("export", ["lapsformat"], 4, self.Update) if index else None)                                       
            
        
    def Update(self, mode = UPDATE_MODE.all):                                
                                                  
        #export        
        #exportgroups
        for i in range(0, NUMBER_OF.EXPORTS):             
            self.exportgroups[i].Update()
            
            
        if dstore.Get("export")["lapsformat"] == ExportLapsFormat.FORMAT_TIMES:
            Ui().radioExportLapsTimes.setChecked(True)            
            Ui().radioExportLapsLaptimes.setChecked(False)
            Ui().radioExportLapsPoints_1.setChecked(False)
            Ui().radioExportLapsPoints_2.setChecked(False)
            Ui().radioExportLapsPoints_3.setChecked(False)
        elif dstore.Get("export")["lapsformat"] == ExportLapsFormat.FORMAT_LAPTIMES:            
            Ui().radioExportLapsTimes.setChecked(False)            
            Ui().radioExportLapsLaptimes.setChecked(True)
            Ui().radioExportLapsPoints_1.setChecked(False)
            Ui().radioExportLapsPoints_2.setChecked(False)
            Ui().radioExportLapsPoints_3.setChecked(False)
        elif dstore.Get("export")["lapsformat"] == ExportLapsFormat.FORMAT_POINTS_1:            
            Ui().radioExportLapsTimes.setChecked(False)            
            Ui().radioExportLapsLaptimes.setChecked(False)
            Ui().radioExportLapsPoints_1.setChecked(True)                                
            Ui().radioExportLapsPoints_2.setChecked(False)
            Ui().radioExportLapsPoints_3.setChecked(False)
        elif dstore.Get("export")["lapsformat"] == ExportLapsFormat.FORMAT_POINTS_2:            
            Ui().radioExportLapsTimes.setChecked(False)            
            Ui().radioExportLapsLaptimes.setChecked(False)
            Ui().radioExportLapsPoints_1.setChecked(False)                                
            Ui().radioExportLapsPoints_2.setChecked(True)
            Ui().radioExportLapsPoints_3.setChecked(False)
        elif dstore.Get("export")["lapsformat"] == ExportLapsFormat.FORMAT_POINTS_3:            
            Ui().radioExportLapsTimes.setChecked(False)            
            Ui().radioExportLapsLaptimes.setChecked(False)
            Ui().radioExportLapsPoints_1.setChecked(False)                                
            Ui().radioExportLapsPoints_2.setChecked(False)
            Ui().radioExportLapsPoints_3.setChecked(True)
        else:
            print "error: export laptimes"
                
            dstore.ResetChangedFlag("export")
                                
        return True
    
tabExportSettings = TabExportSettings() 