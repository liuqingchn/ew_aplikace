# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys
import time
import os
from PyQt4 import QtCore, QtGui, Qt
from ewitis.data.db import db
from ewitis.gui.UiAccesories import MSGTYPE
import ewitis.gui.myModel as myModel
import ewitis.gui.UsersModel as UsersModel
import ewitis.gui.PointsModel as PointsModel
import libs.db_csv.db_csv as Db_csv
import ewitis.gui.TimesUtils as TimesUtils
import ewitis.gui.DEF_COLUMN as DEF_COLUMN
from ewitis.data.DEF_DATA import *
import ewitis.gui.TimesSlots as Slots
import libs.utils.utils as utils
import libs.timeutils.timeutils as timeutils
from ewitis.data.dstore import dstore
import time

'''
F5 - refresh
F6 - export table
F7 - export WWW
F11 - export categories 
F12 - direct WWW export
'''
class TimesParameters(myModel.myParameters):
    
    def __init__(self, source):
                
        #table and db table name
        self.name = "Times"         
        
        #TABLE
        self.tabUser = source.U        
        self.tabCategories = source.C
        self.tabCGroups = source.CG 
        self.tabPoints = source.tablePoints 
                
        
        #=======================================================================
        # KEYS
        #=======================================================================        
        self.DB_COLLUMN_DEF = DEF_COLUMN.TIMES['database']

        
        #toDo: rozlisit podle mode z datastore
        #self.TABLE_COLLUMN_DEF = DEF_COLUMN.TIMES['table_training']                                               
        self.TABLE_COLLUMN_DEF  = DEF_COLUMN.TIMES['table_race']
        
        self.EXPORT_COLLUMN_DEF  = DEF_COLUMN.TIMES['table_race']        
        
        #create MODEL and his structure
        myModel.myParameters.__init__(self, source)  
                      
                                
        #=======================================================================
        # GUI
        #=======================================================================
        self.gui = {} 
        #VIEW
        self.gui['view'] = source.ui.TimesProxyView
        
        #FILTER
        self.gui['filter'] = source.ui.TimesFilterLineEdit
        self.gui['filterclear'] = source.ui.TimesFilterClear
        
        #GROUPBOX
        self.gui['add'] = source.ui.TimesAdd
        self.gui['remove'] =  source.ui.TimesRemove
        self.gui['export'] = source.ui.TimesExport
        self.gui['export_www'] = source.ui.TimesWwwExport
        self.gui['import'] = None 
        self.gui['recalculate'] = source.ui.TimesRecalculate
        self.gui['delete'] = source.ui.TimesDelete
        self.gui['aDirectWwwExport'] = source.ui.aDirectWwwExport
        self.gui['aDirectExportCategories'] = source.ui.aDirectExportCategories 
        self.gui['aDirectExportLaptimes'] = source.ui.aDirectExportLaptimes 
        
        #SPECIAL
        #self.gui['show_all'] = source.ui.TimesShowAll
        #self.gui['show_zero'] = source.ui.timesShowZero
        #self.gui['show_additional_info'] = source.ui.timesAdditionalInfo
        
        #COUNTER
        self.gui['counter'] = source.ui.timesCounter
        
        #self.gui['add'].setEnabled = False
        
        #=======================================================================
        # classes
        #=======================================================================        
        self.classModel = TimesModel                              
        self.classProxyModel = TimesProxyModel
        
        
        
class TimesModel(myModel.myModel):
    def __init__(self, params):                        
                
        #create MODEL and his structure
        myModel.myModel.__init__(self, params)
                    
        #add utils function
        #self.utils = TimesUtils.TimesUtils()
        
        #
        self.starts = TimesUtils.TimesStarts()
        self.order = TimesUtils.TimesOrder()
        self.lap = TimesUtils.TimesLap()
        self.laptime = TimesUtils.TimesLaptime()
                                                           
        #update with first run        
        first_run = db.getFirst("runs")
        if(first_run != None):
            self.run_id = first_run['id']
        else:
            self.run_id = 0 #no times for run_id = 0 
                                
                   
    #setting flags for this model
    #first collumn is NOT editable
    def flags(self, index): 
        
        #id, name, category, addres NOT editable

        if ((index.column() == 4) or (index.column() == 5) or (index.column() == 6)):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        return myModel.myModel.flags(self, index)
    
    def getDefaultTableRow(self): 
        row = myModel.myModel.getDefaultTableRow(self)
        row['cell'] = 1                  
        row['nr'] = 0 #musi byt cislo!                                              
        row['time_raw'] = 0
        row['start_nr'] = 1               
        return row                 

    
    def db2tableRow(self, dbTime):
        """    
        ["id", "nr", "cell", "time", "name", "category", "address"]
        """
        
        #ztimeT = time.clock()
        #print "TIME", dbTime['id']                                
        
        if(dstore.Get('show')['times_with_order'] == 2):
            if(self.order.IsToShow(dbTime) == False):
                return None
                                             
        '''hide all zero time?'''                    
        if(dstore.Get('show')['starttimes'] == False):                            
            if (dbTime["cell"] == 1):                
                return None                      
        
        ''' 1to1 KEYS '''           
        tabTime = myModel.myModel.db2tableRow(self, dbTime)
         
        ''' get USER
            - user_id je id v tabulce Users(bunky) nebo tag_id(rfid) '''
        '''Test: vzal jsem rovnou tabusera, zda se to ze to chodi'''                                            
        tabUser =  self.params.tabUser.getTabUserParIdOrTagId(dbTime["user_id"])         
        #dbUser =  self.params.tabUser.getDbUserParIdOrTagId(dbTime["user_id"])        
       
        
        ''' get CATEGORY'''            
        tabCategory =  self.params.tabCategories.getTabRow(tabUser['category_id'])                                
        #tabCategory =  None                                
                                        
        ''' OTHER KEYS ''' 
        
        '''NR'''                   
        tabTime['nr'] = tabUser['nr']
                                    
        '''START NR'''
        if(tabTime['cell'] == 1) or (tabTime['nr']==0) or tabCategory==None: #start time?                           
            tabTime['start_nr'] = 1 #decrement 1.starttime
        else:                                
            tabTime['start_nr'] = tabCategory['start_nr']
                    
        '''STATUS'''        
        if (dbTime['cell'] == 1) or (dbTime["user_id"] == 0):
            tabTime['status'] = ''        
        else:                       
            tabTime['status'] = tabUser['status']
            
        '''TIME
            dbtime 2 tabletime'''                                               
        
        '''raw time'''        
        tabTime['timeraw'] = TimesUtils.TimesUtils.time2timestring(dbTime['time_raw'])
        
        '''time'''
        if(dbTime['time'] == None):
            '''cas by mel existovat'''
            print "E: neexistuje cas!!!", dbTime                            
            #self.calc_update_time(dbTime, tabTime['start_nr'])
        else:                        
            tabTime['time'] = TimesUtils.TimesUtils.time2timestring(dbTime['time'])            
                
        '''NAME'''        
        if(dbTime['cell'] == 1):
            tabTime['name'] = ''
        elif(dbTime["user_id"] == 0):
            tabTime['name'] = 'undefined'
        else:                       
            tabTime['name'] = tabUser['name'].upper() +' '+tabUser['first_name']        
        
        '''CATEGORY'''                                                                                
        tabTime['category'] = tabUser['category']                                                                                                                              

             
        tabTime['lap'] = None
        tabTime['order'] = None
        tabTime['order_cat'] = None       
        
        '''LAP'''
        #z1 = time.clock()
        #@workaround: potrebuju lap pro poradi => lap.Get() nerezohlednuje ("additional_info")['lap']                
        aux_lap = self.lap.Get(dbTime)          
        if  dstore.Get("additional_info")['lap']:           
            tabTime['lap'] = aux_lap
        #print "- Lap takes: ",(time.clock() - z1)
        
        '''LAPTIMEs'''        
        tabTime['laptime'] = TimesUtils.TimesUtils.time2timestring(self.laptime.Get(dbTime))                
        tabTime['best_laptime'] = TimesUtils.TimesUtils.time2timestring(self.laptime.GetBest(dbTime))                                            
        
        '''ORDER'''                
        #z1 = time.clock()                                                
        tabTime['order']  = self.order.Get(dbTime, aux_lap)
        #print "- order takes: ",(time.clock() - z1)                                
                
        '''ORDER IN CATEGORY'''                                    
        #z1 = time.clock()                                
        tabTime['order_cat'] = self.order.Get(dbTime, aux_lap, category_id = tabUser['category_id'])
        #print "- order in category takes: ",(time.clock() - z1)    
                                                                                          
        #print "TIME take: ",(time.clock() - ztimeT)
        
        '''POINTS'''
        if (dstore.Get("additional_info")["enabled"] == 2):        
            tabTime['points'] = self.params.tabPoints.getPoints(tabTime, PointsModel.Points.eTOTAL)        
            tabTime['points_cat'] = self.params.tabPoints.getPoints(tabTime, PointsModel.Points.eCATEGORY)
        return tabTime
                                                                                   
    def sModelChanged(self, item):
                
        if(dstore.Get("user_actions") == 0):                              
        
            #print "radek",item.row()
            tabRow = self.row_dict(item.row())
            dbRow = self.table2dbRow(tabRow, item)
            dbUser = self.params.tabUser.getDbUserParNr(tabRow['nr'])
            #get DB-USER                  
            if(dbRow == None):
                self.params.uia.showMessage("Status update error", "Cant find user with nr. "+ tabRow['nr'])                
                return None
                
            if(item.column() == self.params.TABLE_COLLUMN_DEF['nr']['index']):
               
                '''ZMĚNA ČÍSLA'''
                '''přiřazení uživatele nelze u času                
                   - startovací buňky
                   - nulového času'''                                  
                
                if(int(tabRow['cell']) == 1):                            
                    self.params.uia.showMessage(self.params.name+" Update error", "Cannot assign user to start time!")
                    self.update()       
                    return
                                                                                                
#                elif(tabRow['time'] == '00:00:00,00'):
#                   self.params.showmessage(self.params.name+" Update error", "Cannot assign user to zero time!")
#                   self.update()
#                   return
            elif(item.column() == self.params.TABLE_COLLUMN_DEF['status']['index']):
                '''ZMĚNA STATUSu'''
                '''- pro nestartovcí časy lze do času zapsat 'dns', 'dnf' nebo 'dnq'                                
                   - tento state se zapíše k danému uživately => users.state 
                '''
                
                #check rights and format
                if(int(tabRow['cell']) == 1):
                    self.params.uia.showMessage("Status update error", "Status can NOT be set to starttime")
                    return                
                elif(int(tabRow['nr']) == 0):   
                    self.params.uia.showMessage("Status update error", "Status can NOT be set to user with nr. 0")
                    return                
                elif tabRow['status'] != 'finished' and tabRow['status'] != 'race' and tabRow['status'] != 'dns' and tabRow['status'] != 'dnf' and tabRow['status'] != 'dsq':
                    self.params.uia.showMessage("Status update error", "Wrong format of status! \n\nPossible only 'race','dns', dnf' or 'dsq'!")
                    return
                                                                                                                                                                                                     
                #convert sqlite row to dict
                #dbUser2 = {}
                #for key in dbUser.keys():
                #    dbUser2[key] = dbUser[key]
                    
                dbUser = db.row2dict(dbUser)                
                dbUser['status'] = tabRow['status']
                                
                 
                #update status
                print "zapisuju novej status", dbUser                
                db.update_from_dict(self.params.tabUser.params.name, dbUser)                
                return

                                                                           
            ###################
            # MODEL CHANGED
            ###################            
            myModel.myModel.sModelChanged(self, item)        

                    
            #update status
            if self.IsFinishTime(dbRow) == True:
                                                                                                                                                                                     
                #convert sqlite row to dict                    
                dbUser = db.row2dict(dbUser)                                    
                                       
                dbUser['status'] = 'finished'
                 
                #update status                
                db.update_from_dict(self.params.tabUser.params.name, dbUser)
                #print "finishtime", dbUser 
                 
  

                
    def table2dbRow(self, tabTime, item = None): 
                                            
        #get selected id
        #try:                     
        #    rows = self.params.gui['view'].selectionModel().selectedRows()                        
        #    id = self.proxy_model.data(rows[0]).toString()
        #except:
        #    self.params.showmessage(self.params.name+" Delete error", "Cant be deleted")
            
        #1to1 keys, just copy        
        dbTime = myModel.myModel.table2dbRow(self, tabTime, item)
                
        '''RUN_ID'''
        #if(self.showall):
        if(dstore.Get('show')['alltimes'] == 2):
            '''get time['run_id'] from DB, , in showall-mode i dont know what run is it'''            
            aux_dbtime = db.getParId("times",tabTime['id'])            
            dbTime['run_id'] = aux_dbtime['run_id']            
        else:
            dbTime['run_id'] = self.run_id
                        
        '''first start time? => cant be updated
            toDo:asi by za určitých okolností měl jít'''       
#        if(int(tabTime['id']) == (self.utils.getFirstStartTime(dbTime['run_id'])['id'])):
#            self.params.showmessage(self.params.name+" Update error", "First start time cant be updated!")
#            return None        
        
        '''USER NR => USER ID'''                        
        if(int(tabTime['nr']) == 0):
            dbTime['user_id'] = 0                     
        else:                                                
            ''' get DB-USER'''
            dbUser = self.params.tabUser.getDbUserParNr(tabTime['nr'])                                                      
            if(dbUser == None):
                self.params.uia.showMessage(self.params.name+" Update error", "Cant find user with nr. "+ tabTime['nr'])                
                return None
                                      
            '''get DB-CATEGORY'''             
            dbCategory = self.params.tabCategories.getDbRow(dbUser['category_id'])
            if(dbCategory == None):
                self.params.uia.showMessage(self.params.name+" Update error", "Cant find category for this user.")                
                return None
            
            '''při změně čísla nejsou v tabTime správné user údaje'''
            '''toDo:sloučit name a first name'''
            #tabTime['category'] = dbCategory['name']
            #tabTime['name'] = dbUser['name'] +' ' + dbUser['first_name']                        
            
            '''TEST if is here enought START-TIMES'''                        
            nr_start = dbCategory['start_nr']            
            try:                                
                aux_start_time = self.starts.Get(dbTime['run_id'], nr_start)
            except IndexError:                        
                self.params.uia.showMessage(self.params.name+": Update error", str(nr_start)+".th start-time is necessary for users from this category!")
                return None
            except:
                self.params.uia.showMessage(self.params.name+": Update error", "Cant find start time for this category.")
                return None
                
            ''' get user id'''
            dbTime['user_id'] = self.params.tabUser.getIdOrTagIdParNr(tabTime['nr'])            
                        
            if(dbTime['user_id'] == None):
                '''user not found => nothing to save'''
                self.params.uia.showMessage(self.params.name+": Update error", "No user or tag with number "+str(tabTime['nr'])+"!")
                return None
            
            #in onelap race user can have ONLY 1 TIME
            #if(dstore.Get('onelap_race') == True):
            #    if(self.lap.GetLaps(dbTime) != 0):
            #        self.params.showmessage(self.params.name+": Update error", "This user has already time!")
            #        return None 
                            
        ''' TIME '''                                                            
        #try:                                                         
        #dbTime['time_raw'] = self.utils.tabtime2dbtime(dbTime['run_id'], tabTime)                        
               
        '''get start-time'''        
        if(tabTime['cell'] == 1):                            
            #toDo: je tohle nutné? start_time se nikde nepoužije
            try:                                         
                start_time = self.starts.GetFirst(dbTime['run_id'])
            except (TypeError,KeyError):            
                start_time = self.starts.GetDefault()                
        else:
            '''čas může být v tabulce None, třeba pokud nemá všechny startovací běhy k dispozici
                   potom se čas naupdatuje, nechává se současný v databázi'''
            '''toDo: nevracet string ale pravou hodnotu z getTableRow'''
            if(tabTime['time'] != None) and (tabTime['time'] != u''):
                
                ''' z categories vezmu start_nr a pak jdu do start-times pro start-time'''                
                tabUser = self.params.tabUser.getTabUserParNr(tabTime['nr'])                            
                category = self.params.tabCategories.getDbCategoryParName(tabUser['category'])                
                try:                                        
                    start_time = self.starts.Get(dbTime['run_id'], category['start_nr'])                    
                except TypeError:
                    '''žádný startovací čas => vezmi default (1.čas vůbec)'''                    
                    start_time = self.starts.GetFirst(dbTime['run_id']) 
                                
                '''table-time => db-time'''
                try:
                                        
                    if(item.column() == self.params.TABLE_COLLUMN_DEF['time']['index']):
                        '''změna času=>změna času v db'''            
                        dbTime['time_raw'] = TimesUtils.TimesUtils.timestring2time(tabTime['time']) + start_time['time_raw']
                    
                    '''počítaný čas se vždy maže a spočte se při updatu znova'''    
                    dbTime['time'] = None
                    
                except TimesUtils.TimeFormat_Error:
                    self.params.uia.showMessage(self.params.name+" Update error", "Wrong Time format!")                
                
            
        
        '''nelze přiřadit číslo nulovému/zápornému času'''
        #&if(dbTime['time_raw'] == 0)                                                                                          
                                            
        #except TimesUtils.TimeFormat_Error:
        #    self.params.showmessage(self.params.name+" Update error", "Time wrong format!")             
        

                                                                                                                                                                                                                                                                                                                             
        return dbTime    
        
    def IsFinishTime(self, dbTime):
        '''
        splňuje závodník podmínky pro "finished"?
            - (počet kol větší než X) nebo (čas větší než Y)
        '''
        if self.lap.GetLaps(dbTime) >= dstore.Get('race_info')['limit_laps']:
            return True
        return False
        
    def update_laptime(self, dbTime):
        
        if(dbTime['laptime'] == None):            
                                    
            '''vypocet spravneho casu a ulozeni do databaze pro pristi pouziti'''                                                           
            laptime = self.laptime.Get(dbTime)                                            
             
            if laptime != None:                                                        
                '''ulozeni do db'''
                #print "Times: update laptime, id:", dbTime['id'],"time:",laptime            
                dbTime['laptime'] = laptime                                                       
                db.update_from_dict(self.params.name, dbTime) #commit v update()
    def update_laptimes(self):
        """
        u časů kde 'time'=None, do počítá time z time_raw a startovacího časů pomocí funkce calc_update_time()
        
        *Ret:*
            pole čísel závodníků u kterých se nepodařilo časy updatovat   
        """
        ret_ko_times = []
        
        dbTimes = db.getAll(self.params.name)
        dbTimes = db.cursor2dicts(dbTimes)
        
        for dbTime in dbTimes:
            
            '''time'''
            if(dbTime['laptime'] == None):                                                                        
                '''vypocet spravneho casu a ulozeni do databaze pro pristi pouziti'''
                
                try:                                    
                    self.update_laptime(dbTime)
                except:                    
                    ret_ko_times.append(dbTime['id'])
                           
        return ret_ko_times
                                                       
    def calc_update_time(self, dbTime, start_nr = None):
        
        if(dbTime['time'] == None):            
                                    
            '''vypocet spravneho casu a ulozeni do databaze pro pristi pouziti'''
            try:
                '''toDo: misto try catch, Get bude vracet None'''                                   
                start_time = self.starts.Get(dbTime['run_id'], start_nr)                                
            except:                         
                print "E: Times: no starttime nr.",start_nr,", for time", dbTime 
                aux_rawtime = None
                start_time = None
                                                    
            '''odecteni startovaciho casu a ulozeni do db'''
            #print dbTime['time_raw']
            dbTime['time'] = dbTime['time_raw'] - start_time['time_raw']                                                       
            db.update_from_dict(self.params.name, dbTime) #commit v update()                                           
            
                
    def calc_update_times(self):
        """
        u časů kde 'time'=None, do počítá time z time_raw a startovacího časů pomocí funkce calc_update_time()
        
        *Ret:*
            pole časů u kterých se nepodařilo časy updatovat   
        """
        ret_ko_times = []
        
        dbTimes = db.getAll(self.params.name)
        dbTimes = db.cursor2dicts(dbTimes)
        
        for dbTime in dbTimes:
            
            '''time'''
            if(dbTime['time'] == None):
            
                ''' get USER'''            
                tabUser =  self.params.tabUser.getTabUserParIdOrTagId(dbTime["user_id"])
                ''' get CATEGORY'''            
                tabCategory =  self.params.tabCategories.getTabRow(tabUser['category_id'])                                
                                            
                '''START NR'''
                if(dbTime['cell'] == 1) or (tabUser['nr']==0): #start time?                           
                    start_nr = 1 #decrement 1.starttime
                else:                                
                    start_nr = tabCategory['start_nr']        
                                                        
                '''vypocet spravneho casu a ulozeni do databaze pro pristi pouziti'''
                try:                
                    self.calc_update_time(dbTime, start_nr)
                except:
                    ret_ko_times.append(dbTime['id'])
                           
        return ret_ko_times
    
    #UPDATE TABLE        
    def update(self, run_id = None):                  
        
        #print self.params.name+": model update (t)"
        
        if(run_id != None):                    
            self.run_id = run_id #update run_id
            
        #update start times        
        self.starts.Update()        
        
        ko_nrs = self.calc_update_times()
        if(ko_nrs != []):
            print "E:",self.params.name+" Update error", "Some times have no start times, ids: "+str(ko_nrs)
            
        ko_nrs = self.update_laptimes()        
        if(ko_nrs != []):
            print "E:",self.params.name+" Update error", "Some laptimes can not be updated"+str(ko_nrs)
            
        db.commit()
            
        
        
        #update times        
        if dstore.Get('show')['alltimes'] == 2:                        
            #get run ids
            conditions = []
            ids = self.params.tabRuns.proxy_model.ids()
                                            
            #create list of lists, [["id",2],["id",6],..]
            for id in ids:
                conditions.append(['run_id', id])                                                      
                                         
            #update all times             
            myModel.myModel.update(self, conditions = conditions, operation = 'OR')            
        else:            
            #update for selected run        
            #myModel.myModel.update(self, "run_id", self.run_id)            
            myModel.myModel.update(self, "run_id", self.run_id)
        #db.commit()            
                                                                                       

class TimesProxyModel(myModel.myProxyModel):
    def __init__(self, params):                        
        
        #create PROXYMODEL
        myModel.myProxyModel.__init__(self, params)
        
    def IsColumnAutoEditable(self, column):
        if column == 1:
            '''změna čísla'''    
            return True
        return False
           
                  
   
# view <- proxymodel <- model 
class Times(myModel.myTable):    
    def  __init__(self, params):        
        
        #create table instance (slots, etc.)
        myModel.myTable.__init__(self, params)                
                
        #special slots
        #self.slots = Slots.TimesSlots(self)                                       
       
        #TIMERs
        #self.timer1s = QtCore.QTimer(); 
        #self.timer1s.start(1000);
        
        #MODE EDIT/REFRESH        
        self.system = 0
        
        self.winner = {}
        
    def createSlots(self):
        
        #standart slots
        myModel.myTable.createSlots(self)
        
        
        #button Recalculate
        QtCore.QObject.connect(self.params.gui['recalculate'], QtCore.SIGNAL("clicked()"), lambda:self.sRecalculate(self.model.run_id))
         
        #export direct www
        QtCore.QObject.connect(self.params.gui['aDirectWwwExport'], QtCore.SIGNAL("triggered()"), self.sExport_directWWW)
        
        #export direct categories        
        if (self.params.gui['aDirectExportCategories'] != None):                                   
            QtCore.QObject.connect(self.params.gui['aDirectExportCategories'], QtCore.SIGNAL("triggered()"), lambda:self.sExportResultsDirect('col_nr_export'))
                               
        QtCore.QObject.connect(self.params.gui['aDirectExportLaptimes'], QtCore.SIGNAL("triggered()"), self.sExportLaptimesDirect)
        
                                
   
    def sRecalculate(self, run_id):
        if (self.params.uia.showmessage("Recalculate", "Are you sure you want to recalculate times and laptimes? \n (only for the current run) ", MSGTYPE.warning_dialog) != True):            
            return
        print "A: Times: Recalculating.. run id:", run_id
        query = \
                " UPDATE times" +\
                    " SET time = Null, laptime = Null" +\
                    " WHERE (times.cell != 1 ) AND (times.time != 0) AND (times.run_id = \""+str(run_id)+"\")"
                        
        res = db.query(query)
                        
        db.commit()
        print "A: Times: Recalculating.. press F5 to finish"
        return res
                 
    
    ''''''                   
    def tabRow2exportRow(self, tabRow, mode, status = 'race'):                        
                                                           
        exportRow = []
        exportHeader = []
        
        #save the winner
        #print "1:",tabRow
        if 'order' in tabRow:
            if(tabRow['order'] != ''):
                if ((mode == Times.eTOTAL) and (int(tabRow['order']) == 1)) or \
                    ((mode == Times.eCATEGORY) and (int(tabRow['order_cat']) == 1)):
                    self.winner = tabRow                    
            
        #print "tabRow: ", tabRow['id'], ":", tabRow['order']
        '''get user'''
        if(mode == Times.eTOTAL) or (mode == Times.eGROUP) or (mode == Times.eCATEGORY):
            tabHeader = self.params.tabUser.proxy_model.header()                                                  
            tabUser = self.params.tabUser.getTabUserParNr(tabRow['nr'])
            if tabUser['status'] != status:
                print "export: zahazuju radek: status", tabRow
                return None
        
        if(mode == Times.eTOTAL) or (mode == Times.eGROUP):
            exportHeader = [u"Pořadí", u"Číslo", u"Pořadí/Kategorie", u"Jméno"]                                                            
            exportRow.append(tabRow['order']+".")
            exportRow.append(tabRow['nr'])
            exportRow.append(tabRow['order_cat']+"./"+tabRow['category'])            
            exportRow.append(tabRow['name'])           
        elif(mode == Times.eCATEGORY):                                       
            exportHeader = [u"Pořadí", u"Číslo", u"Jméno"]            
            exportRow.append(tabRow['order_cat']+".")
            exportRow.append(tabRow['nr'])
            exportRow.append(tabRow['name'])           
        elif(mode == Times.eLAPS):                                                      
            #header                                       
            exportHeader = [u"Číslo", u"Jméno", u"1.Kolo", u"2.Kolo", u"3.Kolo",u"4.Kolo", u"5.Kolo", u"6.Kolo",u"7.Kolo", u"8.Kolo", u"9.Kolo", u"10.Kolo", u"11.Kolo", u"12.Kolo", u"13.Kolo", u"14.Kolo", u"15.Kolo",u"16.Kolo", u"17.Kolo", u"18.Kolo",u"19.Kolo", u"20.Kolo", u"21.Kolo", u"22.Kolo", u"23.Kolo", u"24.Kolo"]            
            #row            
            exportRow.append(tabRow[0]['nr'])
            exportRow.append(tabRow[0]['name'])            
            for t in tabRow:
                #exportRow.append(t['time'])   # mezičasy - 2:03, 4:07, 6:09, ...        
                exportRow.append(t['laptime']) # časy kol - 2:03, 2:04, 2:02, ... 
                            
            #row a header musí mít stejnou délku     
            for i in range(len(exportHeader) - len(tabRow) - 2):
                exportRow.append("")                                                                       
        
            
        if(mode == Times.eTOTAL) or (mode == Times.eGROUP) or (mode == Times.eCATEGORY):
            if dstore.GetItem("export", ["year"]) == 2:
                exportHeader.append(u"Ročník")
                exportRow.append(tabUser['birthday'])
            if dstore.GetItem("export", ["club"]) == 2:                                       
                exportHeader.append(u"Klub")
                exportRow.append(tabUser['club']) 
            # user_field_1             
            if dstore.GetItem("export", ["option_1"]) == 2:
                exportHeader.append(dstore.GetItem("export", ["option_1_name"]))
                exportRow.append(tabUser['o1'])
            # user_field_2             
            if dstore.GetItem("export", ["option_2"]) == 2:
                exportHeader.append(dstore.GetItem("export", ["option_2_name"]))
                exportRow.append(tabUser['o2'])
            # user_field_3             
            if dstore.GetItem("export", ["option_3"]) == 2:
                exportHeader.append(dstore.GetItem("export", ["option_3_name"]))
                exportRow.append(tabUser['o3'])
            # user_field_4             
            if dstore.GetItem("export", ["option_4"]) == 2:
                exportHeader.append(dstore.GetItem("export", ["option_4_name"]))
                exportRow.append(tabUser['o4'])
            # laps             
            if dstore.GetItem("export", ["laps"]) == 2:
                exportHeader.append(u"Okruhy")
                exportRow.append(tabRow['lap'])
            # laptime             
            if dstore.GetItem("export", ["laptime"]) == 2:
                exportHeader.append(u'Čas kola')
                exportRow.append(tabRow['laptime'])
            # best laptime             
            if dstore.GetItem("export", ["best_laptime"]) == 2:
                exportHeader.append(u"Top okruh")
                exportRow.append(tabRow['best_laptime'])
            
            #time
            exportHeader.append(u"Čas")    
            exportRow.append(tabRow['time'])
            
            #ztráta
            if dstore.GetItem("export", ["gap"]) == 2:
                exportHeader.append(u"Ztráta")
                ztrata = ""            
                if(self.winner != {} and tabRow['time']!=0 and tabRow['time']!=None):
                    if self.winner['lap'] == tabRow['lap']:                
                        ztrata = TimesUtils.TimesUtils.times_difference(tabRow['time'], self.winner['time'])
                    elif tabRow['lap']!='' and tabRow['lap']!=None:
                        ztrata = int(self.winner['lap']) - int(tabRow['lap'])                     
                        if ztrata == 1:
                            ztrata = str(ztrata) + " kolo"
                        elif ztrata < 5:
                            ztrata = str(ztrata) + " kola"
                        else:
                            ztrata = str(ztrata) + " kol"     
                exportRow.append(ztrata)                                 
                            
            #body - total, categories, groups
            if(mode == Times.eTOTAL) and (dstore.GetItem("export", ["points_race"]) == 2):
                exportHeader.append(u"Body")                                    
                exportRow.append(str(tabRow['points']))                
            elif(mode == Times.eCATEGORY) and (dstore.GetItem("export", ["points_categories"]) == 2):
                exportHeader.append(u"Body")                                    
                exportRow.append(str(tabRow['points_cat']))                 
            elif(mode == Times.eGROUP) and (dstore.GetItem("export", ["points_groups"]) == 2):
                exportHeader.append(u"Body")                                    
                exportRow.append(str(tabRow['points']))                
        
        '''vracim dve pole, tim si drzim poradi(oproti slovniku)'''
        #print "exportRow: ", exportRow
        #print "2:",exportRow                         
        return (exportHeader, exportRow)

                    
    
    def ExportMerge(self, rows, header, headerdata = ["",""]):
            aux_rows = rows[:]
            #aux_rows.insert(0, [dstore.Get('race_name'),] + (len(header)-1) * ["",])
            #aux_rows.insert(1, len(header)*["",])
            #aux_rows.insert(2, header)            
            aux_rows.insert(0, [headerdata[0],] + ["",]*(len(header)-2) + [headerdata[1],])
            aux_rows.insert(1, [dstore.Get('race_name'),] + (len(header)-1) * ["",])    
            aux_rows.insert(2, header)            
            return aux_rows
    #=======================================================================
    # SLOTS
    #=======================================================================
    
    # F11 - konečné výsledky, 1 čas na řádek
    def sExportResultsDirect(self, col_nr_export):
        
        ret = self.params.uia.showMessage("Results Export", "Choose format of results", MSGTYPE.question_dialog, "NOT finally results", "Finally results")        
                
        if ret == False: #cancel button
            return
                               
        #title
        title = "Table '"+self.params.name + "' CSV Export Categories" 
        
        #get filename, gui dialog         
        #dirname = self.params.myQFileDialog.getExistingDirectory(self.params.gui['view'], title)
        dirname = utils.get_filename("export/"+timeutils.getUnderlinedDatetime()+"_"+dstore.Get('race_name')+"/")
        try:
            os.makedirs(dirname)
        except OSError:
            dirname = "export/"
                                         
        if(dirname == ""):
            return                              

        exportRows = []
        exportRows_Alltimes = []
        
        exported = {}
        self.winner = {}        

        '''EXPORT TOTAL'''                                       
        for tabRow in self.proxy_model.dicts():
            dbTime = self.getDbRow(tabRow['id'])
            #d print "id:", tabRow['id'],
            
            if(dbTime['user_id'] == 0) or (dbTime['cell'] <= 1):
                continue
            
            #                        
            exportRow = self.tabRow2exportRow(tabRow, Times.eTOTAL)
            
            if exportRow == None:
                continue
            
            #all times export - add all
            exportRows_Alltimes.append(exportRow[1])
            exportHeader_Alltimes = exportRow[0] 
            
            #times export - add last/best (race/slalom)                                                                                                                                       
            #if(dstore.Get('order_evaluation') == OrderEvaluation.RACE and self.model.order.IsLastUsertime(dbTime)) or \
            #        (dstore.Get('order_evaluation') == OrderEvaluation.SLALOM and self.model.order.IsBestUsertime(dbTime)):
            if self.order.IsToShow(dbTime) == True:                                                    
                exportRows.append(exportRow[1])
                exportHeader = exportRow[0]                         
                    
            
        '''natvrdo pred girem'''        
        #exportHeader = ["Pořadí", "Pořadí K", "Kategorie" , "Číslo", "Jméno", "Ročník", "Klub", "Čas"]  
            
        '''write to csv file'''
        if(exportRows != []):
            #print "export total, ", len(exportRows),"times"
            exported["total"] =  len(exportRows)
            exportRows =  self.ExportMerge(exportRows, exportHeader)            
            filename = utils.get_filename("_"+dstore.Get('race_name')+".csv")            
            aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class
            try:                
                aux_csv.save(exportRows)
            except IOError:
                self.params.uia.showmessage(self.params.name+" Export warning", "File "+dstore.Get('race_name')+".csv"+"\nPermission denied!")
                        
        '''Alltimes - write to csv file'''
        if(exportRows_Alltimes != []):
            #print "export total alltimes, ", len(exportRows_Alltimes),"times"
            exported["(at) total"] =  len(exportRows_Alltimes)                       
            #exportRows_Alltimes.insert(0, [dstore.Get('race_name'),] + (len(exportHeader_Alltimes)-1) * ["",])
            #exportRows_Alltimes.insert(1, len(exportHeader_Alltimes)*["",])
            #exportRows_Alltimes.insert(2, exportHeader_Alltimes)
            exportRows_Alltimes =  self.ExportMerge(exportRows_Alltimes, exportHeader_Alltimes)
            filename = utils.get_filename("at_"+dstore.Get('race_name')+".csv")            
            aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class
            try:                
                aux_csv.save(exportRows_Alltimes)
            except IOError:
                self.params.uia.showmessage(self.params.name+" Export warning", "File "+dstore.Get('race_name')+".csv"+"\nPermission denied!")
                
                                             
        '''EXPORT CATEGORIES'''                        
        dbCategories = self.params.tabCategories.getDbRows()                      
        for dbCategory in dbCategories:
            exportRows = []             
            exportRows_Alltimes = []
            self.winner = {}                                     
            for tabRow in self.proxy_model.dicts():
                dbTime = self.getDbRow(tabRow['id'])
                
                if(dbTime['user_id'] == 0) or (dbTime['cell'] <= 1):
                    continue
                                            
                if (tabRow['category'] != dbCategory['name']):
                    continue
                                
                #
                exportRow = self.tabRow2exportRow(tabRow, Times.eCATEGORY)
                if exportRow == None:
                    continue
                
                #all times export - add all                
                exportRows_Alltimes.append(exportRow[1])
                exportHeader_Alltimes = exportRow[0] 
            
                #times export - add last/best (race/slalom)            
                #if(dstore.Get('order_evaluation') == OrderEvaluation.RACE and self.model.order.IsLastUsertime(dbTime)) or \
                #    (dstore.Get('order_evaluation') == OrderEvaluation.SLALOM and self.model.order.IsBestUsertime(dbTime)):
                if self.order.IsToShow(dbTime) == True:  
                    if (tabRow['category'] == dbCategory['name']):                                                                                                                                                               
                        exportRows.append(exportRow[1])
                        exportHeader = exportRow[0]                                                                                                                                                                                           
                        
            
            '''write to csv file'''
            if(exportRows != []):                
                exported["(c_) " + dbCategory['name']] = len(exportRows)                                                                     
                exportRows =  self.ExportMerge(exportRows, exportHeader, ["Kategorie: "+dbCategory['name'], dbCategory['description']])                
                
                filename = utils.get_filename("c_"+dbCategory['name']+".csv")
                aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class                
                try:                                                                                             
                    aux_csv.save(exportRows)
                except IOError:
                    self.params.uia.showmessage(self.params.name+" Export warning", "File "+filename+"\nPermission denied!")
                                                      
            '''Alltimes - write to csv file'''
            if(exportRows_Alltimes != []):                
                exported["(c_at_) " + dbCategory['name']] = len(exportRows_Alltimes)                                                     
                exportRows_Alltimes =  self.ExportMerge(exportRows_Alltimes, exportHeader_Alltimes, ["Kategorie: "+dbCategory['name'], dbCategory['description']])               
                                
                filename = utils.get_filename("c_at_"+dbCategory['name']+".csv")
                aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class                
                try:                                                                                             
                    aux_csv.save(exportRows_Alltimes)
                except IOError:
                    self.params.uia.showmessage(self.params.name+" Export warning", "File "+filename+"\nPermission denied!")                                  
                                   
                    
        '''EXPORT GROUPS'''
        dbCGroups = self.params.tabCGroups.getDbRows()
                              
        index_category = self.params.TABLE_COLLUMN_DEF["category"]["index"]                
        dbCategories = self.params.tabCategories.getDbRows()
        for dbCGroup in dbCGroups:                                              
            exportRows = []
            exportRows_Alltimes = []
            self.winner = {}                        
            for tabRow in self.proxy_model.dicts():
                dbTime = self.getDbRow(tabRow['id'])
                
                if(dbTime['user_id'] == 0) or (dbTime['cell'] <= 1):
                    continue

                tabCategory = self.params.tabCategories.getTabCategoryParName(tabRow['category'])
                if (tabCategory[dbCGroup['label']] != 1):
                    continue
                                            
                #all times export - add all
                exportRow = self.tabRow2exportRow(tabRow, Times.eGROUP)
                if exportRow == None:
                    continue
                
                exportRows_Alltimes.append(exportRow[1])
                exportHeader_Alltimes = exportRow[0] 
                
                if(dstore.Get('order_evaluation') == OrderEvaluation.RACE and self.model.order.IsLastUsertime(dbTime)) or \
                    (dstore.Get('order_evaluation') == OrderEvaluation.SLALOM and self.model.order.IsBestUsertime(dbTime)):                    
                     
                    tabCategory = self.params.tabCategories.getTabCategoryParName(tabRow['category'])                 
                    if (tabCategory[dbCGroup['label']] == 1):
                        exportRow = self.tabRow2exportRow(tabRow, Times.eGROUP)                                                                                                                                       
                        exportRows.append(exportRow[1])
                        exportHeader = exportRow[0]                                                                                                                  

            
                    
            '''write to csv file'''
            if(exportRows != []):                
                exported["(g_) "+dbCGroup['label']] = len(exportRows)                
                
                #exportRows.insert(0, [dstore.Get('race_name'),time.strftime("%d.%m.%Y", time.localtime()), time.strftime("%H:%M:%S", time.localtime())])                
                exportRows =  self.ExportMerge(exportRows, exportHeader, ["Skupina: "+dbCGroup['name'], dbCGroup['description']])                                                
                filename = utils.get_filename(dbCGroup['label']+"_"+dbCGroup['name']+".csv")
                aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class                
                try:                                                                                             
                    aux_csv.save(exportRows)
                except IOError:
                    self.params.uia.showMessage(self.params.name+" Export warning", "File "+filename+"\nPermission denied!")
                    
            '''Alltimes - write to csv file'''
            if(exportRows_Alltimes != []):                
                exported["(g_at_) "+dbCGroup['label']] = len(exportRows_Alltimes)                                                
                exportRows_Alltimes =  self.ExportMerge(exportRows_Alltimes, exportHeader_Alltimes, ["Skupina: "+dbCGroup['name'], dbCGroup['description']])                                                
                filename = utils.get_filename(dbCGroup['label']+"_at_"+dbCGroup['name']+".csv")
                aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class                
                try:                                                                                             
                    aux_csv.save(exportRows_Alltimes)
                except IOError:
                    self.params.uia.showMessage(self.params.name+" Export warning", "File "+filename+"\nPermission denied!")

        
        exported_string = ""
        for key in sorted(exported.keys()):
            exported_string += key + " : " + str(exported[key])+" times\n"        
        self.params.uia.showMessage(self.params.name+" Exported", exported_string, MSGTYPE.info)                                        
        return         

                
    def sExportLaptimesDirect(self):
        #get filename, gui dialog
        #title = "Table '"+self.params.name + "' CSV Export Laptimes"                 
        #dirname = self.params.myQFileDialog.getExistingDirectory(self.params.gui['view'], title)
        dirname = utils.get_filename("export/"+timeutils.getUnderlinedDatetime()+"_"+dstore.Get('race_name')+"_laptimes/")
        try:
            os.makedirs(dirname)
        except OSError:
            dirname = "export/"
                             
        if(dirname == ""):
            return  
        
        self.sExportLaptimesCategories(dirname)
        self.sExportLaptimesGroups(dirname)
        
    def sExportLaptimesCategories(self, dirname):            
                                  
        if(dirname == ""):
            return                
        
        '''LAPS PAR CATEGORY'''                        
        dbCategories = self.params.tabCategories.getDbRows()  
        tableRows = self.proxy_model.dicts()                            
        for dbCategory in dbCategories:
            """ 
            - přes všechny kategorie
                - přes každé číslo #loop A
                    - vyberu číslo/závodníka, jehož časy budou na novém řádku    #loop A1
                    - přes všechny časy, ukládám časy s tímto číslem (exportRow) #loop A2                    
                - všechny uložené časy transponuju do řádku (exportRow)
                - transponovaný řádek ukládám (exportRows)
            - řádky uložím do csv a jdu na další kategorii                                 
            """
            
            #rows for csv export 
            exportRows = []
            self.winner = {}
                                                                                                                                   
            for nr in range(len(tableRows)): #loop A                                                              
                '''pro každou kategorii přes všechny zbylé časy'''
                if(len(tableRows) == 0):                    
                    break                
                    
                exportRow = []
                
                #první číslo
                nr_user = None
                for t in tableRows: #loop A1
                    if (t['nr'] != None) and (int(t['nr']) != 0) and (t['category'] == dbCategory['name']):                 
                        nr_user = t['nr']                        
                        break #mam číslo
                                        
                if(nr_user == None):
                    break #no user for this category
                                
                
                '''mám číslo, hledám jeho další časy'''                    
                for i in range(len(tableRows)): #A2                                                                                 
                    if (tableRows[i]['category'] == dbCategory['name']) and (tableRows[i]['nr'] == nr_user):
                        exportRow.append(tableRows[i])                        
                                                
                '''pokud jsem našel exportuji a mažu z tabulky'''                
                if(exportRow != []):                    
                    for t in exportRow:
                        tableRows.remove(t)                         
                    exportRow = self.tabRow2exportRow(exportRow, Times.eLAPS)                    
                    exportRows.append(exportRow[1])
                    exportHeader = exportRow[0]
                    
            if(exportRows != []):
                print "Export: laps par category:", dbCategory['name'], ":", len(exportRows),"times"
                
                #srovnat podle čísla                
                from operator import itemgetter
                exportRows = sorted(exportRows, key = itemgetter(0))
                
                #save to csv file                
                exportRows.insert(0, ["Kategorie: "+dbCategory['name'],] + ["",]*(len(exportHeader)-2) + [dbCategory['description'],])
                exportRows.insert(1, [dstore.Get('race_name'),] + (len(exportHeader)-1) * ["",])
                exportRows.insert(2, exportHeader)    
                filename = utils.get_filename("c_laps_"+dbCategory['name']+".csv")
                aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class                
                try:                                                                                             
                    aux_csv.save(exportRows)
                except IOError:
                    self.params.uia.showMessage(self.params.name+" Export warning", "File "+filename+"\nPermission denied!")
                                                         
        return  
    
    #GROUPS
    def sExportLaptimesGroups(self, dirname):
                             
        if(dirname == ""):
            return                      
        
        '''LAPS PAR GROUPS'''                        
        dbGroups = self.params.tabCGroups.getDbRows()  
        tableRows = self.proxy_model.dicts()                            
        for dbGroup in dbGroups:            
            """ 
            - přes všechny kategorie
                - přes každé číslo #loop A
                    - vyberu číslo/závodníka, jehož časy budou na novém řádku    #loop A1
                    - přes všechny časy, ukládám časy s tímto číslem (exportRow) #loop A2                    
                - všechny uložené časy transponuju do řádku (exportRow)
                - transponovaný řádek ukládám (exportRows)
            - řádky uložím do csv a jdu na další kategorii                                 
            """
            
            #rows for csv export 
            exportRows = []
            self.winner = {}
                                                                                                                                   
            for nr in range(len(tableRows)): #loop A                                                              
                '''pro každou kategorii přes všechny zbylé časy'''
                if(len(tableRows) == 0):                    
                    break                
                    
                exportRow = []
                              
                #první číslo
                nr_user = None
                for t in tableRows: #loop A1
                    
                    dbTime = self.getDbRow(t['id'])
                    if(dbTime['user_id'] == 0) or (dbTime['cell'] <= 1):                        
                        continue
                    
                    if (t['nr'] == None) or (int(t['nr']) == 0):                        
                        continue
                    
                    tabCategory = self.params.tabCategories.getTabCategoryParName(t['category'])
                    if (tabCategory[dbGroup['label']] != 1):                        
                        continue
                    
                    #mam číslo                                  
                    nr_user = t['nr']                                                                
                    break 
                                        
                if(nr_user == None):                    
                    break #no user for this group
                                
                
                '''mám číslo, hledám jeho další časy'''
                for tabRow in tableRows: #A2
                    tabCategory = self.params.tabCategories.getTabCategoryParName(tabRow['category'])
                    if (tabCategory[dbGroup['label']] != 1):                        
                        continue
                                                                                                     
                    if(tabRow['nr'] != nr_user):                        
                        continue
                   
                    #add row
                    exportRow.append(tabRow) 
                        
                                            
                #for i in range(len(tableRows)): #A2                                                                                 
                #    if (tableRows[i]['category'] == dbGroup['name']) and (tableRows[i]['nr'] == nr_user):
                #        exportRow.append(tableRows[i])                        
                                                
                '''pokud jsem našel exportuji a mažu z tabulky'''                
                if(exportRow != []):                    
                    for t in exportRow:
                        tableRows.remove(t)                         
                    exportRow = self.tabRow2exportRow(exportRow, Times.eLAPS)                    
                    exportRows.append(exportRow[1])
                    exportHeader = exportRow[0]
                    
            if(exportRows != []):
                print "Export: laps par group:", dbGroup['name'], ":", len(exportRows),"times"
                
                #srovnat podle čísla                
                #from operator import itemgetter
                #exportRows = sorted(exportRows, key = itemgetter(0))
                
                #save to csv file                
                exportRows.insert(0, ["Skupina: "+dbGroup['name'],] + ["",]*(len(exportHeader)-2) + [dbGroup['description'],])
                exportRows.insert(1, [dstore.Get('race_name'),] + (len(exportHeader)-1) * ["",])
                exportRows.insert(2, exportHeader)    
                filename = utils.get_filename("g_laps_"+dbGroup['name']+".csv")
                aux_csv = Db_csv.Db_csv(dirname+"/"+filename) #create csv class                
                try:                                                                                             
                    aux_csv.save(exportRows)
                except IOError:
                    self.params.uia.showMessage(self.params.name+" Export warning", "File "+filename+"\nPermission denied!")
                                                         
        return  
        
        
        
        
    def sExport(self):                      
        import os        
        
        col_nr_export = 'col_nr_export_raw'
        
        '''get filename, gui dialog, save path to datastore'''        
        #filename =  self.params.myQFileDialog.getSaveFileName(self.params.gui['view'],"Export table "+self.params.name+" to CSV","dir_export_csv","Csv Files (*.csv)", self.params.name+".csv") 
        filename =  self.params.uia.myQFileDialog.getSaveFileName("Export table "+self.params.name+" to CSV","dir_export_csv","Csv Files (*.csv)", self.params.name+".csv") 
                                 
        if(filename == ""):
            return                            

        title = "Table '"+self.params.name + "' CSV Export Categories" 
        exportRows = []        

        '''EXPORT ALL TIMES'''                                                        
        for tabRow in self.proxy_model.dicts():
            exportRow = self.tabRow2exportRow(tabRow, Times.eTOTAL)[1]                                    
            if exportRow != []:                            
                exportRows.append(exportRow)
            exportHeader = self.tabRow2exportRow(tabRow, Times.eTOTAL)[0]                                        
             
        '''write to csv file'''
        if(exportRows != []):
            print "export race", dstore.Get('race_name'), ":",len(exportRows),"times"
            first_header = [dstore.Get('race_name'), time.strftime("%d.%m.%Y", time.localtime()), time.strftime("%H:%M:%S", time.localtime())]
            exportRows.insert(0, exportHeader)
            aux_csv = Db_csv.Db_csv(filename) #create csv class
            try:                                     
                aux_csv.save(exportRows)
            except IOError:
                self.params.uia.showmessage(self.params.name+" Export warning", "Permission denied!")
                               
                    
    #toDo: sloucit s myModel konstruktorem        
    def update(self, run_id = None):
        ztime = time.clock()                      
        self.model.update(run_id = run_id)                        
        print "I: Times: update:",time.clock() - ztime,"s"
        #myModel.myTable.update(self)
        self.setColumnWidth()
        self.updateTabCounter()
        self.updateDbCounter()
            

    # REMOVE ROW      
    # first starttime cant be deleted          
    def sDelete(self):        
        
        #get selected id
        try:                     
            rows = self.params.gui['view'].selectionModel().selectedRows()                        
            id = self.proxy_model.data(rows[0]).toString()
        except:
            self.params.uia.showMessage(self.params.name+" Delete error", "Cant be deleted")
            return
            
        #first start time? => cant be updated               
        #if(int(id) == (self.model.utils.getFirstStartTime(self.model.run_id)['id'])):
        if(int(id) == (self.model.starts.GetFirst(self.model.run_id)['id'])):
            self.params.uia.showMessage(self.params.name+" Delete warning", "First start time cant be deleted!")
            return  
        
        #delete run with additional message
        myModel.myTable.sDelete(self)
                                                                                                                                  
    #
    def getCount(self, run_id, dbCategory = None, minimal_laps = None):
        run_id_esc = str(run_id)                                       
        
        query = "SELECT COUNT(*) FROM(\
                    SELECT COUNT(times.id) from times"
        
        if(dstore.Get('rfid') == 2):
            query = query + \
                    " INNER JOIN tags ON times.user_id = tags.tag_id"+\
                    " INNER JOIN users ON tags.user_nr = users.nr "
        else:
            query = query + \
                    " INNER JOIN users ON times.user_id = users.id"
            
        query = query + \
                    " WHERE (times.run_id = "+run_id_esc+")"\
                        " AND (users.state != \"dns\")"\
                        " AND (users.state != \"dnf\")"\
                        " AND (users.state != \"dnq\")"
        if dbCategory:
            category_id_esc = str(dbCategory["id"])                        
            query = query + \
                        " AND (users.category_id = "+category_id_esc+")"
        query = query + \
                    " GROUP by times.user_id"
                    
        if minimal_laps:
            query = query + \
                    " HAVING count(*) >= " + str(minimal_laps)
                    
        query = query + ")"     
        
        #print query
        res = db.query(query)
        return res.fetchone()[0]                                                            
        
                                    
                                                                                            
    

            
            

        
        
    