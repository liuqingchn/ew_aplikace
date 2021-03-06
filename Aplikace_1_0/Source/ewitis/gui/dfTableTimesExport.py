# -*- coding: utf-8 -*-
'''
Created on 16. 1. 2016

@author: Meloun
'''
import time, os
import libs.pandas.df_utils as df_utils
from ewitis.data.dstore import dstore
import pandas as pd
from ewitis.data.DEF_DATA import *
from ewitis.gui.tabExportSettings import tabExportSettings
from ewitis.gui.dfTableUsers import tableUsers
from ewitis.gui.dfTableCategories import tableCategories
from ewitis.gui.dfTableCGroups import tableCGroups
import libs.utils.utils as utils
import libs.timeutils.timeutils as timeutils
import ewitis.exports.ewitis_html as ew_html


(eCSV_EXPORT, eCSV_EXPORT_DNF, eHTM_EXPORT, eHTM_EXPORT_LOGO) = range(0,4)
    
'''
 F11, F12 - final results
 - prepare DFs for export (according to filter, sort, etc.)
 - call ExportToXXXFiles with these 3 DFs
'''  
def Export(utDf, export_type = eCSV_EXPORT):             
    
       
    # 3DFs for 3 exports
    exportDf = [pd.DataFrame()] * NUMBER_OF.EXPORTS
    
    if len(utDf) != 0:                      
        
        #update export df
        for i in range(0, NUMBER_OF.EXPORTS):
                          
            aux_df = utDf.copy()
            
            if (tabExportSettings.IsEnabled(i) == False):
                continue
            
            #get export filtersort
            filtersort = dstore.GetItem('export_filtersort', [i])
                                      
            filter = filtersort['filter']
            sort1 = filtersort['sort1'].lower()  
            sort2 = filtersort['sort2'].lower()
            sortorder1 = True if(filtersort['sortorder1'].lower() == "asc") else False
            sortorder2 = True if(filtersort['sortorder2'].lower() == "asc") else False
            
            #filter                 
            aux_df = df_utils.FilterEmptyColumns(aux_df, filter.split(" "))
                            
            #aux_df = self.joinedDf[(aux_df[column1].notnull()) & (self.joinedDf['user_id']!=0)]                
                        
            #last time from each user?                    
            aux_df = aux_df.sort("timeraw")                        
            if("last" in filter):                                                                
                aux_df = aux_df.groupby("nr", as_index = False).last()
                
            #beautify
            aux_df = aux_df.where(pd.notnull(aux_df), None)
            aux_df.set_index('id',  drop=False, inplace = True)
            
            #sort
            if(sort2 in aux_df.columns):
                aux_df = aux_df.sort([sort1, sort2], ascending = [sortorder1, sortorder2])
            else:
                aux_df = aux_df.sort(sort1, ascending = sortorder1)
                        
            #add "order in category" -> "3./Kategorie XY"
            for oc in range(0, NUMBER_OF.EXPORTS):
                ordercatX = 'ordercat'+str(oc+1)
                orderX = 'order'+str(oc+1)                
                aux_df[ordercatX] = aux_df[orderX].astype(str)+"./"+aux_df.category                                
            
            #lapsexport
            if (dstore.GetItem('export_filtersort', [i, "onerow"]) != 0):                       
                aux_df = ToLapsExport(aux_df)
            
            #print "PRED",i, aux_df.head(2), aux_df.dtypes
            ConvertToInt(aux_df)
            #print "PO",i, aux_df.head(2), aux_df.dtypes                                                
            
            #add missing users with DNF status
            if export_type == eCSV_EXPORT_DNF:
                aux_df = AddMissingUsers(aux_df)
            
            exportDf[i] = aux_df
    
    #export complete/ category and group results from export DFs        
    exported = {}
    if (export_type == eCSV_EXPORT) or (export_type == eCSV_EXPORT_DNF):
        exported = ExportToCsvFiles(exportDf)            
    elif (export_type == eHTM_EXPORT) or (export_type == eHTM_EXPORT_LOGO):
        exported = ExportToHtmFiles(exportDf, export_type)    
    else:
        print  "Error: This export is not defined!"
        
    return exported                                  
      
'''
ExportToCsvFiles
- from prepared DFs export complete, category and group export    
- prepare header and df and call ExportToCsvFile()
'''
# def ExportToCsvFiles(self, df, i):
def ExportToCsvFiles(dfs):               
    
    #ret = uiAccesories.showMessage("Results Export", "Choose format of results", MSGTYPE.question_dialog, "NOT finally results", "Finally results")                        
    #if ret == False: #cancel button
    #    return         
    
    #return info
    exported = {}
    
    #get dirname
    racename = dstore.GetItem("racesettings-app", ['race_name'])      
    dirname = utils.get_filename("export/"+timeutils.getUnderlinedDatetime()+"_"+racename+"/")
    os.makedirs(dirname)                                                                                       
            
    for i in range(0, NUMBER_OF.EXPORTS): 
        
        if (tabExportSettings.IsEnabled(i, "csv") == False):
            continue
        
        #get df
        df =  dfs[i]                        
        filtersort = dstore.GetItem('export_filtersort', [i])
        
        #get firstline (racename, time)
        header = dstore.GetItem("export_header", [i])             
        racename =  header["racename"].replace("%race%", dstore.GetItem("racesettings-app", ['race_name']))
        headertext = header["headertext"].replace("%time%", timeutils.getCurrentDateTime())
        firstline = [racename, headertext]            
                    
        #filter to checked columns            
        columns = GetExportCollumns(df, i)                                    
        
        #workarround
        #replace time with DNF for long times
        #df = self.DNF_workarround(df)          
                    
        #total export
        if "total" in filtersort["type"]:
            #print i, "TOTAL"
            if(len(df) != 0):
                filename = utils.get_filename("e"+str(i+1)+"_t_"+racename)                                                         
                ExportToCsvFile(dirname+filename+".csv", Columns2Cz(df[columns]), firstline)                                
                exported[filename] = len(df) 
                    
        #category export    
        elif "categories" in filtersort["type"]:
            #print i, "CATEGORIES"            
            c_df = dfs[i]           
            c_df = c_df.set_index("category", drop = False)
            category_groupby = c_df.groupby(c_df.index)
            for c_name, c_df in category_groupby:                
                if(len(c_df) != 0):
                    category = tableCategories.model.getCategoryParName(c_name)
                    category = category.to_dict()
                     
                    #get secondline (!!c_name used also for filename!!)
                    c_name = header["categoryname"].replace("%category%", c_name)
                    secondline = [c_name, header["description"].replace("%description%", category["description"])]
                    
                    #write to file
                    filename = utils.get_filename("e"+str(i+1)+"_c_"+c_name)
                    ExportToCsvFile(dirname+filename+".csv",  Columns2Cz(c_df[columns]), firstline, secondline)                                                                                                                                                
                    
                    exported[filename] = len(c_df) 
                 
        #group export 
        elif "groups" in filtersort["type"]: 
            #print i, "GROUPS"          
            g_df = dfs[i]
            for x in range(1,11):                
                g_label = "g"+str(x)
                categories = tableCategories.model.getCategoriesParGroupLabel(g_label)
                                                                 
                aux_df = g_df[g_df["category"].isin(categories["name"])]                                                                           
                if(aux_df.empty == False):                                 
                    group = tableCGroups.model.getCGrouptParLabel(g_label)
                    filename = utils.get_filename("e"+str(i+1)+"_"+g_label+"__"+group["name"])                        
                    ExportToCsvFile(dirname+filename+".csv", Columns2Cz(aux_df[columns]), firstline, [group["name"], group["description"]])                                       
                    exported[filename] = len(aux_df)                                        
    return exported

"""
ExportToCsvFile
- export dataframe to csv file
"""
def ExportToCsvFile(filename, df, firstline = ['',''], secondline = ['','']):                                                          
    try:
        df_utils.WriteToCsvFile(filename, df, firstline, secondline)                                      
    except IOError:
        uiAccesories.showMessage(self.name+" Export warning", "File "+filename+"\nPermission denied!")
        
def ExportToHtmFiles(dfs, type):       

    print "ExportToHtmFiles"
    #return info
    exported = {}
                            
    #get filename, gui dialog  
    racename = dstore.GetItem("racesettings-app", ['race_name'])      
    dirname = utils.get_filename("export/www/")
    
                
    for i in range(0, NUMBER_OF.EXPORTS): 
        
        if (tabExportSettings.IsEnabled(i, "htm") == False):
            continue        
        
        #filter to checked columns
        columns = tabExportSettings.exportgroups[i].GetCheckedColumns() 
        
        df = pd.DataFrame()
        if(type == eHTM_EXPORT):            
            df =  dfs[i]
            if(len(df) != 0):
                df = df[columns]
            css_filename = dstore.GetItem("export_www", [i, "css_filename"])
            js_filename = dstore.GetItem("export_www", [i, "js_filename"])
            title = dstore.GetItem("racesettings-app", ['race_name']) 
        elif(type == eHTM_EXPORT_LOGO):
            df =  pd.DataFrame()                      
            css_filename = u"css/logo.css"
            js_filename = u""
            title = "Časomíra Ewitis - <i>Vy závodíte, my měříme..</i>"
        else:
            print  "Error: This export is not defined!", type 
            return
        #complete export            
        #if(len(df) != 0) or (type == self.eHTM_EXPORT_LOGO):
        filename =  utils.get_filename(dirname+"e"+str(i+1)+"_"+racename+".htm")
        
        #convert header EN => CZ            
        tocz_dict = dstore.GetItem("export", ["names"])                                               
        df = df.rename(columns = tocz_dict)

        #firsttimes
        nr = dstore.GetItem("export_www", [i, "firsttimes"])
        if nr != 0:
            df = df.head(nr)    
        #lasttimes
        nr = dstore.GetItem("export_www", [i, "lasttimes"])
        if nr != 0:
            df = df.tail(nr)
            
        #transpose
        if dstore.GetItem("export_www", [i, "transpose"]):    
            aux_columns = df.columns
            df = df.T
            df.insert(0,"", aux_columns)
        
        ExportToHtmFile(filename, df, css_filename, js_filename, title)            
        exported["total"] = len(df)
         
    return exported 

'''
export jednoho souboru s výsledky
'''    
def ExportToHtmFile(filename, df, css_filename = "", js_filename = "", title = ""):    
                                                                                           
    html_page = ew_html.Page_table(filename, title, styles= [css_filename,], scripts=[js_filename],lists = df.values, keys = df.columns)                                                                            
    html_page.save()                                                                                                         
                    

'''
'''
def ToLapsExport(self, df):        
                    
    # http://stackoverflow.com/questions/32051676/how-to-transpose-dataframe/32052086        
    df['colnum'] = df.groupby('nr').cumcount()+1
    
    columns_to_transpose =  [s for s in df.columns if "time" in s] + [s for s in df.columns if "points" in s]        
            
    aux_df = df[columns_to_transpose + ["nr", "colnum"]]
    aux_df = aux_df.pivot(index='nr', columns='colnum')
    aux_df.columns = ['{}{}'.format(col, num) for col,num in aux_df.columns]
    aux_df = aux_df.reset_index()
    
    cols_to_use = df.columns.difference(aux_df.columns)
    cols_to_use = list(cols_to_use) + ["nr"]  
    
    df = pd.merge(aux_df, df[cols_to_use].drop_duplicates(subset = "nr", take_last = True), on="nr", how = "left")
    
    for c in [s for s in df.columns if "points" in s]:
        if c in df:
            df[c] = df[c].astype(float)                                                
    return df    
def GetExportCollumns(df, i):
    
    
    #filter to checked columns
    columns = tabExportSettings.exportgroups[i].GetCheckedColumns()
                 
    #export filter-sort settings
    filtersort = dstore.GetItem('export_filtersort', [i])
    
    #add onerow-columns to filtered columns            
    if(filtersort["onerow"] != 0):
        for x in range(0, NUMBER_OF.TIMESCOLUMNS):
            timeX = "time"+str(x+1) 
            if timeX in columns:
                for y in range(0,50):
                    timeXY = timeX+str(y+1)
                    if timeXY in df.columns:                            
                        columns.insert(columns.index(timeX), timeXY)
                columns.remove(timeX)            
        for x in range(0, NUMBER_OF.POINTSCOLUMNS):
            pointsX = "points"+str(x+1)                                        
            if pointsX in columns:                        
                for y in range(0,50):
                    pointsXY = pointsX+str(y+1)
                    if pointsXY in df.columns:                           
                        columns.insert(columns.index(pointsX), pointsXY)
                columns.remove(pointsX)
    return columns 
"""
Add users to dataframe
"""
def AddMissingUsers(self, tDf):        
    
    #get missing users
    df_dnf_users =  tableUsers.model.df[~tableUsers.model.df["nr"].isin(tDf["nr"])].copy()    
                        
    # add "DNF" to timeX (and also timeraw)
    for c in [s for s in tDf.columns if "time" in s]:
        df_dnf_users[c] = "DNF"
        
    # order = lastorder + 1 (for all DNF users same order)
    for c in [s for s in tDf.columns if "order" in s]:
        try:
            last_order = tDf.iloc[-1][c]  
            df_dnf_users[c] = int(last_order) + 1
        except (ValueError, IndexError):
            pass                                 
    tDf = tDf.append(df_dnf_users)
    return tDf      
def DNF_workarround(df):
    if(dstore.GetItem("racesettings-app", ['rfid']) == 0):
        if "time1" in df:
            if(dstore.GetItem("additional_info", ["time", 0, "minute_timeformat"])):
                df.time1[df.time1>"30:00,00"] = "DNF"
            else:
                df.time1[df.time1>"00:30:00,00"] = "DNF" 
                     
        if "time2" in df:
            if(dstore.GetItem("additional_info", ["time", 1, "minute_timeformat"])):
                df.time2[df.time2>"30:00,00"] = "DNF"
            else:
                df.time2[df.time2>"00:30:00,00"] = "DNF" 
                     
        if "time3" in df:
            if(dstore.GetItem("additional_info", ["time", 2, "minute_timeformat"])):
                df.time3[df.time3>"30:00,00"] = "DNF"
            else:
                df.time3[df.time3>"00:30:00,00"] = "DNF" 
    return df             

        
'''
ConvertToInt()
- sloupce kde se vyskytuje i něco jiného než číslo jsou reprezentovány jako object
- to_csv() čísla exportuje jako float ve formátu 2.00
- přetypuju je na float a formátem %g nastavím že nuly se přidávají jen když je třeba
'''
def ConvertToInt(df):
      
    #nr
    df["nr"]  = df["nr"].astype(int)
    
    #format a convert na string (kvůli 3.0 => 3)
    for i in range(0, NUMBER_OF.THREECOLUMNS):
        orderX = "order"+str(i+1)
        #try:
        if orderX in df:
            df[orderX] = df[orderX].astype(float).map('{:,g}'.format)            
        #except:
        #    print "W: not succesfully converted: ", orderX

    #lapX         
    for i in range(0, NUMBER_OF.TIMESCOLUMNS):
        lapX = "lap"+str(i+1)
        if lapX in df:
            df[lapX]  = df[lapX].astype(float).map('{:,g}'.format)
#                 
#         for i in range(0, NUMBER_OF.THREECOLUMNS):
#             if "order"+str(i+1) in df:
#                 df["order"+str(i+1)]  = df["order"+str(i+1)].astype(float)
            
    #pointsX
    for i in range(0, NUMBER_OF.POINTSCOLUMNS):
        if "points"+str(i+1) in df:
            df["points"+str(i+1)]  = df["points"+str(i+1)].astype(float)
            
            #aux_df["points21"] = aux_df["points21"].astype(float)
            #aux_df["points22"] = aux_df["points22"].astype(float)
            #aux_df["points23"] = aux_df["points23"].astype(float)                
    return df

def Columns2Cz(df):
    #convert header EN => CZ
    tocz_dict = dstore.GetItem("export", ["names"])                                                 
    df = df.rename(columns = tocz_dict)     
    
    #onerow columns to CZ                                        
    for x in range(0, NUMBER_OF.TIMESCOLUMNS):
        timeX = "time"+str(x+1) 
        df.columns = df.columns.str.replace(timeX, tocz_dict[timeX])          
    for x in range(0, NUMBER_OF.POINTSCOLUMNS):
        pointsX = "points"+str(x+1)                                        
        df.columns = df.columns.str.replace(pointsX, tocz_dict[pointsX])  
    return df

