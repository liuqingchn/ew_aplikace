# -*- coding: utf-8 -*-
'''
Created on 28.12.2013

@author: Meloun
'''
import time
from PyQt4 import Qt, QtCore, QtGui
from ewitis.gui.Ui import Ui
from ewitis.gui.UiAccesories import uiAccesories, MSGTYPE
import ewitis.gui.DEF_COLUMN as DEF_COLUMN
import libs.utils.utils as utils
import libs.sqlite.sqlite_utils as db_utils
from ewitis.data.db import db  
from ewitis.data.dstore import dstore
from ewitis.gui.aTableModel import * 

import libs.db_csv.db_csv as Db_csv
import ewitis.exports.ewitis_html as ew_html
import libs.utils.utils as utils 

      
class myTable():
    """
    
    """
    def  __init__(self, name):                                                                
        self.name = name
        self.InitCollumns()
        self.db_con = db.getDb()
        
    def InitCollumns(self):                        
        self.DB_COLLUMN_DEF = getattr(DEF_COLUMN, self.name.upper())['database']
        self.TABLE_COLLUMN_DEF = getattr(DEF_COLUMN,  self.name.upper())['table']  
        self.EXPORT_COLLUMN_DEF  = getattr(DEF_COLUMN,  self.name.upper())['table']
    def GetTableProperty(self, key, property_key):
        try:
            property = self.TABLE_COLLUMN_DEF[key][property_key]
        except:
            property = None
        return property
    
               
        
    def InitGui(self, sImport = True):
        
        #============        
        # GUI
        #============
        #VIEW   
        self.gui = {}     
        self.gui['view'] = getattr(Ui(), self.name+"ProxyView") #self.gui['view'] = Ui().PointsProxyView
        
        #FILTER
        try:
            self.gui['filter'] = getattr(Ui(), self.name+"FilterLineEdit") #Ui().PointsFilterLineEdit
            self.gui['filter_column'] = None
            self.gui['filterclear'] = getattr(Ui(), self.name+"FilterClear") #Ui().PointsFilterClear
        except AttributeError:
            self.gui['filter'] = None
            self.gui['filter_column'] = None
            self.gui['filterclear'] = None
        
        #GROUPBOX
        self.gui['add'] = getattr(Ui(), self.name+"Add") #Ui().PointsAdd
        self.gui['remove'] = getattr(Ui(), self.name+"Remove")# Ui().PointsRemove
        try:
            self.gui['export'] = getattr(Ui(), self.name+"Export") #Ui().PointsExport
        except AttributeError:
            self.gui['export'] = None
        self.gui['export_www'] = None        
        try:
            self.gui['import'] = getattr(Ui(), self.name+"Import") #Ui().PointsImport
        except AttributeError:
            self.gui['import'] = None         
        self.gui['delete'] = getattr(Ui(), self.name+"Delete") #Ui().PointsDelete
        
        #COUNTER
        self.gui['counter'] = getattr(Ui(), self.name+"Counter") #Ui().PointsCounter
    
    def InitModels(self):
        module = __import__("table"+self.name, globals=globals())                          
        
        #create PROXY MODEL               
        self.proxy_model = getattr(module, self.name+"ProxyModel")(self) #self.params.classProxyModel(self.gui)        
        
        #create MODEL        
        self.model = getattr(module, self.name+"Model")(self) #self.params.classModel(self.gui)                                                        
        
        #vazba na proxy model kvuli focusu / edit
        self.proxy_model.model = self.model
        
        #assign MODEL to PROXY MODEL
        self.proxy_model.setSourceModel(self.model)
           
    def Init(self):              
                
        #list of hidden collumns
        self.hiddenCollumns = []
        
        # init Gui
        self.InitGui()
        
        # init Models                                
        self.InitModels()
        
        #nastaveni proxy modelu
        self.gui['view'].setModel(self.proxy_model)
        
        #set default sorting
        self.gui['view'].sortByColumn(0, QtCore.Qt.DescendingOrder)
        
        
        #parametry        
        self.gui['view'].setRootIsDecorated(False)
        self.gui['view'].setAlternatingRowColors(True)        
        self.gui['view'].setSortingEnabled(True)
                
        #setColumnWidth()
        #self.update()
        
        QtCore.QObject.connect(self.gui['view'].selectionModel(), QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"), self.sSelectionChanged)
                         
        #TIMERs
        #self.timer1s = QtCore.QTimer(); 
        #self.timer1s.start(1000);                        
                
        self.createSlots()
        
        #update "Counter"
        if(self.gui['filter']  != None):
            self.sFilterRegExp()        
        
    def sSelectionChanged(self, selected, deselected):
        #if selected:
        #print "selection changed"
        pass                                               
        
    def setColumnWidth(self):
        
        for col in range(self.proxy_model.columnCount()):
            self.gui['view'].resizeColumnToContents(col)
              
        #nastaveni sirky sloupcu        
        for key in self.TABLE_COLLUMN_DEF:
            index = self.TABLE_COLLUMN_DEF[key]["index"]
            width = self.TABLE_COLLUMN_DEF[key]["width"]
            if(width):            
                self.gui['view'].setColumnWidth(index,width)
                #print index, key, width                        
        
    def createSlots(self):
        print "I: SLOTS: ",self.name
        
        #TIMEOUT
        #QtCore.QObject.connect(self.timer1s, QtCore.SIGNAL("timeout()"), self.slot_Timer1s)
        
        
        # FILTER CHANGE -> CHANGE TABLE
        try:
            QtCore.QObject.connect(self.gui['filter'], QtCore.SIGNAL("textChanged (const QString & )"), self.sFilterRegExp)
        except TypeError:
            self.gui['filter'] = None
        
        # FILTER SPIN BOX CHANGED        
        try:
            QtCore.QObject.connect(self.gui['filter_column'], QtCore.SIGNAL("valueChanged(int)"), self.sFilterColumn)
        except TypeError:
            self.gui['filter_column'] = None
    
        
        # CLEAR FILTER BUTTON -> CLEAR FILTER
        try:
            QtCore.QObject.connect(self.gui['filterclear'], QtCore.SIGNAL("clicked()"), self.sFilterClear)
        except TypeError:
            self.gui['filterclear'] = None
          
        
        # ADD ROW BUTTON
        try:
            QtCore.QObject.connect(self.gui['add'], QtCore.SIGNAL("clicked()"), self.sAdd)
        except TypeError:
            self.gui['add'] = None
        
        # REMOVE ROW BUTTON
        try:
            QtCore.QObject.connect(self.gui['remove'], QtCore.SIGNAL("clicked()"), self.sDelete)
        except TypeError:
            self.gui['remove'] = None
        
        # IMPORT BUTTON -> CHANGE TABLE
        try:
            QtCore.QObject.connect(self.gui['import'], QtCore.SIGNAL("clicked()"), self.sImport)   
        except TypeError:
            self.gui['import'] = None
            
        # EXPORT BUTTON
        try:
            QtCore.QObject.connect(self.gui['export'], QtCore.SIGNAL("clicked()"), lambda: myTable.sExport(self, myModel.eTABLE, True))        
        except TypeError:
            self.gui['export'] = None
        
        # EXPORT WWW BUTTON        
        try:
            QtCore.QObject.connect(self.gui['export_www'], QtCore.SIGNAL("clicked()"), lambda: myTable.sExport(myTable.eWWW, True))
        except TypeError:
            self.gui['export_www'] = None
        
        # DELETE BUTTON -> EMPTY TABLE
        try:
            QtCore.QObject.connect(self.gui['delete'], QtCore.SIGNAL("clicked()"), self.sDeleteAll)
        except TypeError:
            self.gui['delete'] = None
        
        #self.sFilterRegExp(filter, table, label_counter)        
                             
    #=======================================================================
    # SLOTS
    #=======================================================================
        
    #UPDATE TIMER    
    def slot_Timer1s(self):                 
        pass 
        #self.update()    #update table            
    
                            
    # FILTER COLLUMN CHANGED
    def sFilterColumn(self, nr):
        self.proxy_model.setFilterKeyColumn(nr)
        
    # CLEAR FILTER BUTTON -> CLEAR FILTER        
    def sFilterClear(self):    
        self.gui['filter'].setText("")
        if self.gui['filter_column']:
            self.proxy_model.setFilterKeyColumn(-1)
            self.gui['filter_column'].setValue(-1) 
                        
    # FILTER CHANGE -> CHANGE TABLE
    def sFilterRegExp(self):    
        regExp = QtCore.QRegExp(self.gui['filter'].text(), QtCore.Qt.CaseInsensitive, QtCore.QRegExp.RegExp)
        self.proxy_model.setFilterRegExp(regExp)
        self.updateTabCounter()
        #self.params['counter'].setText(str(self.proxy_model.rowCount())+"/"+str(self.model.rowCount()))
              
                 
    # ADD ROW               
    def sAdd(self):
        title = "Table "+self.name+" Add"                
        
        #get ID for default record
        #row = self.model.getDefaultTableRow()
        dbRow = self.model.getDefaultDbRow()    
        #print row                        
        dbRow['id'] = uiAccesories.showMessage(title,"ID: ", MSGTYPE.get_integer, dbRow['id'])                
        if dbRow['id'] == None:
            return

        #this ID exist?                
        res = db.getParId(self.name, dbRow['id'])            
        if(res):
            uiAccesories.showMessage(title,"Record with this ID already exist!")
            return
                     
                    
        #dstore.Set("user_actions", False)  
                                              
        if(dbRow != None):        
            db.insert_from_dict(self.name, dbRow)            
            uiAccesories.showMessage(title,"succesfully (id="+str(dbRow['id'])+")", MSGTYPE.statusbar)

        self.Update()                    
        #dstore.Set("user_actions", True)  
        
    # REMOVE ROW               
    def sDelete(self, label=""):                
        
        #title
        title = "Table '"+self.name + "' Delete"
                        
        #get selected id
        try:                     
            rows = self.gui['view'].selectionModel().selectedRows()                        
            id = self.proxy_model.data(rows[0]).toString()
        except:
            uiAccesories.showMessage(title, "Nelze smazat")
            return
            
        #confirm dialog and delete
        if (label != ""):
            label="\n\n("+label+")"        
        if (uiAccesories.showMessage(title, "Are you sure you want to delete 1 record from table '"+self.name+"' ? \n (id="+str(id)+")"+label, MSGTYPE.warning_dialog)):                        
            self.delete(id)
            uiAccesories.showMessage(title, "succesfully (id="+str(id)+")", MSGTYPE.statusbar)                                                                                            
                            
    def sImport(self):
        """import"""                                         
                                           
        #gui dialog                        
        filename = uiAccesories.getOpenFileName("Import CSV to table "+self.name,"dir_import_csv","Csv Files (*.csv)", self.name+".csv")                
        
        #cancel or close window
        if(filename == ""):                        
            return        
                  
        #IMPORT CSV TO DATABASE
        #try:
        #print "collumns", db.getCollumnNames("times")            
            
        #get sorted keys
        keys = []
        for list in sorted(self.DB_COLLUMN_DEF.items(), key = lambda (k,v): (v["index"])):
            keys.append(list[0])
        #print "keys", keys
            
        #load csv        
        aux_csv = Db_csv.Db_csv(filename)
        rows =  aux_csv.load()
                    
        #check csv file format - emty file
        if(rows==[]):                
            uiAccesories.showMessage(self.name+" CSV Import", "NOT Succesfully imported\n wrong file format")
            return
        
        #check csv file format - wrong format                                
        header = rows.pop(0)
        #header = aux_csv.header()
#         for i in range(3): 
#             if not(header[i] in keys):
#                 uiAccesories.showMessage(self.name+" CSV Import", "NOT Succesfully imported\n wrong file format")
#                 print header[i], keys
#                 #return

        #counters
        state = {'ko':0, 'ok':0}
        
        #adding records to DB                        
        for row in rows:                                                                                                                                    
            #try:
                #add 1 record
            #print "row", row
            importRow = dict(zip(keys, row))
                        
            dbRow = self.model.importRow2dbRow(importRow)            
                                                         
            if(db.insert_from_dict(self.name, dbRow, commit = False) == True):                                      
                state['ok'] += 1
            else:            
                state['ko'] += 1 #increment errors for error message
            #except:
            #    state['ko'] += 1 #increment errors for error message

        db.commit()                        
        self.model.Update()
        self.sImportDialog(state)
        #except:
        #    uiAccesories.showMessage(self.params.name+" CSV Import", "Error")
                                                    
                
                                
    def sImportDialog(self, state):                            
        #title
        title = "Table '"+self.name + "' CSV Import"
        
        if(state['ko'] != 0) :
            uiAccesories.showMessage(title, "NOT Succesfully"+"\n\n" +str(state['ok'])+" record(s) imported.\n"+str(state['ko'])+" record(s) NOT imported.\n\n Probably already exist.")                                                            
        else:
            uiAccesories.showMessage(title,"Succesfully"+"\n\n" +str(state['ok'])+" record(s) imported.", MSGTYPE.info)                                                       
    
    def GetExportKeys(self, mode):        
        #get sorted table keys 
        if mode == myModel.eDB:
            #get sorted keys
            keys = []
            for list in sorted(self.DB_COLLUMN_DEF.items(), key = lambda (k,v): (v["index"])):
                keys.append(list[0])                                    
        else: #total
            keys = [item[1]["name"] for item in sorted(self.TABLE_COLLUMN_DEF.items(), key = lambda (k,v): (v["index"]))]
            
        return keys
            
        
    '''
    ExportTable()     
     - z tabulky vytvoří dva listy - header(list) a rows(lists of lists) 
    '''
    def ExportTable(self, mode):
        exportRows = []                   
        
        '''table to 2 lists - header and rows(list of lists)'''        
        keys = self.GetExportKeys(mode)                
                                                                        
        for tabRow in self.proxy_model.dicts():                                        
            exportRow = self.model.tabRow2exportRow(tabRow, keys, mode)            
            exportRowList = [(exportRow[key]) for key in keys]                                            
            if (exportRowList == None):
                continue
                                                                  
            exportRows.append(exportRowList)                                 
                            
        return (keys, exportRows)  
        
    '''
    sExport()    
     - standartní slot pro export
     - export aktuálního zobrazení tabulky, co vidíš to dostaneš
     - 1.řádek header
    '''
    '''
    sExport()    
     - standartní slot pro export
     - export aktuálního zobrazení tabulky, co vidíš to dostaneš
     - 1.řádek header
    '''      
    def sExport(self, mode, dialog):
        
        print "I: ", self.name, ": export"
        if (mode == myModel.eTABLE):                
            format = "Csv"
            prefix = ""
        elif (mode == myModel.eDB):
            format = "Csv"
            prefix = "db_"
        elif mode == myModel.eWWW:
            format = "Htm"
            prefix = ""
            
                
        '''get filename, gui dialog, save path to datastore'''                                 
        #filename = uiAccesories.getSaveFileName("Export table "+self.name+" to CSV", "dir_export_csv","Csv Files (*.csv)", self.name+".csv")                        
        if dialog:
            print "as", "dir_export_"+format.lower()         
            filename = uiAccesories.getSaveFileName("Export table "+self.name+" to "+format.upper(),"dir_export_"+format.lower(), format.upper()+" Files (*."+format.lower()+")", self.name+"."+format.lower())
        else:
            filename = utils.get_filename("export/"+format.lower()+"/"+self.name+"_"+dstore.GetItem("racesettings-app",['race_name'])+"."+format.lower())
                     
        if(filename == ""):
            return                
                
        title = "Table '"+self.name + "'"+format.upper()+" Export"
        
        '''table to 2 lists - header and rows(list of lists)'''
        (exportHeader, exportRows) = self.ExportTable(mode)
                
        '''Write to the file'''
        if format == "Csv":                                    
            '''Write to CSV file'''            
            if(exportRows != []) or (exportHeader!= []):
                print "export race", dstore.GetItem("racesettings-app",['race_name']), ":",len(exportRows),"rows"            
                first_header = [dstore.GetItem("racesettings-app", ['race_name']), time.strftime("%d.%m.%Y", time.localtime()), time.strftime("%H:%M:%S", time.localtime())]
                exportRows.insert(0, exportHeader)
                aux_csv = Db_csv.Db_csv(filename)
                try:                                     
                    aux_csv.save(exportRows)
                except IOError:
                    uiAccesories.showMessage(self.name+" Export warning", "Permission denied!")
        elif format == "Htm":                    
            '''Write to HTML file'''            
            try:                                                                
                html_page = ew_html.Page_table(filename, title = dstore.GetItem("racesettings-app", ['race_name']), styles= ["css/results.css",], lists = exportRows, keys = exportHeader)
                html_page.save()                             
                uiAccesories.showMessage(title, "Succesfully ("+filename+") : "+ time.strftime("%H:%M:%S", time.localtime()), msgtype = MSGTYPE.statusbar)            
            except IOError:            
                uiAccesories.showMessage(title, "NOT succesfully \n\nCannot write into the file ("+filename+")")                                           
                                         
                        
    # DELETE BUTTON          
    def sDeleteAll(self):
        
        #title
        title = "Table '"+self.name + "' Delete"
        
        #confirm dialog and delete
        if (uiAccesories.showMessage(title, "Are you sure you want to delete table '"+self.name+"' ?", msgtype = MSGTYPE.warning_dialog)):
            self.deleteAll()                                                                      
                                                             
            
            
    def Update(self, parameter = None, value = None, selectionback = True):                        
        
        print "update table", self.name
                                    
        #get row-selection
        if(selectionback==True):
            try:
                rows = self.gui['view'].selectionModel().selectedRows()         
                model_index = rows[0] #selected row index #row = rows[0].row() if rows else 0         
            except:
                pass 
        
        #update model
        self.model.Update(parameter=parameter, value=value)
        
        
        #resize collumns to contents        
        #for col in range(self.proxy_model.columnCount()):
        #    self.params.gui['view'].resizeColumnToContents(col)        
        self.setColumnWidth()        

            
        #row-selection back
        if(selectionback==True):                           
            try:                
                self.params.gui['view'].selectionModel().setCurrentIndex(model_index, QtGui.QItemSelectionModel.Rows | QtGui.QItemSelectionModel.SelectCurrent)            
            except:
                pass            
        
        self.updateHideColumns()
        
        #update gui counter        
        self.updateTabCounter()
       
        #
        #update db couner
        self.updateDbCounter()
        #print "db counter:",self.params.name, dstore.Get("count")
        return True
          
                
        
    def updateHideColumns(self):              
        for key,column in self.TABLE_COLLUMN_DEF.items():  
            if key in self.hiddenCollumns:
                self.gui['view'].hideColumn(column['index'])
            else:
                self.gui['view'].showColumn(column['index'])
            
            
    def updateTabCounter(self):
        if  self.gui['counter'] != None:         
            self.gui['counter'].setText(str(self.proxy_model.rowCount())+"/"+str(self.model.rowCount()))
        
    def updateDbCounter(self):        
        dstore.SetItem("count", [self.name,], self.getDbCount())
            

    def getTabRow(self, id, db_con = None):
        if db_con == None:
            db_con = self.db_con                            
        #get db row
        dbRow = self.getDbRow(id, db_con)        
        tabRow = self.model.db2tableRow(dbRow)              
        return tabRow
    
    
    """ database functions """
                             
    def getDbCollumns(self, db_con = None):
        if db_con == None:
            db_con = self.db_con
        return db_utils.getCollumnNames(db_con, self.name)
    
    def getDbRow(self, id, db_con = None):
        if db_con == None:
            db_con = self.db_con
                 
        #dbRow = db.getParX(self.name, "id", id).fetchone()        
        dbRow = db_utils.getParId(db_con, self.name, id)                            
        return dbRow
        
    def getDbRows(self, db_con = None):                                 
        if db_con == None:
            db_con = self.db_con
        #dbRows = db.getAll(self.name)                      
        dbRows = db_utils.getAll(db_con, self.name)                      
        return dbRows
            
    def getDbCount(self, db_con = None):                                 
        if db_con == None:
            db_con = self.db_con
        #count = db.getCount(self.name)                              
        count = db_utils.getCount(db_con, self.name)                                                    
        return count        
    
    def delete(self, id, db_con = None):
        if db_con == None:
            db_con = self.db_con
        #db.delete(self.name, id)                          
        db_utils.delete(db_con, self.name, id)                                                    
        self.model.Update()
        
    def deleteAll(self, db_con = None):        
        if db_con == None:
            db_con = self.db_con
        #db.deleteAll(self.name)
        db_utils.deleteAll(db_con, self.name)                                                    
        self.model.Update()        

if __name__ == "__main__":
    import sys
    from PyQt4 import QtGui
    from Ui_App import Ui_MainWindow
    from ewitis.gui.Ui import appWindow
    app = QtGui.QApplication(sys.argv)
    appWindow.Init()
    uiAccesories.Init()
    
    tableTest =  myTable("Points")
    tableTest.Init()
        
    appWindow.show()    
    sys.exit(app.exec_())
    