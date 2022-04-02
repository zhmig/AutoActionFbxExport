#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Author        : zhenghaoming
Date          : 2022-02-08 09:51:02
FilePath      : \AutoActionFbxExport\AutoActionFbxExport.py
version       : 
LastEditors   : zhenghaoming
LastEditTime  : 2022-04-02 13:27:23
'''
import os,sys

try:
    from PySide.QtGui import *
    from PySide.QtCore import *
except ImportError:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *

from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import pymel.core as pm
import maya.cmds as cmds
import subprocess


reload(sys)
sys.setdefaultencoding('utf8')

def load_plugin(plugin_name):
    '''
    '''
    if not cmds.pluginInfo(plugin_name, q=True, l=True):
        try:
            cmds.loadPlugin(plugin_name)
            print ("Load The Plugins: %s" % plugin_name)
        except:
            pass

#设置maya界面为父级窗口
def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr),QWidget)

ws = [120, 200, 200]
class Table(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)
        self.setColumnCount(3)
        # self.setRowCount(50)
        self.setHorizontalHeaderLabels([u"File Name", u"File Full Path", u"File Save Path"])
        for i, w in enumerate(ws):
            self.setColumnWidth(i, w)
        '''
        #设置表头为粗体
        # font = self.horizontalHeader().font()
        # font.setBold(True)
        # self.horizontalHeader().setFont(font)
        '''
        # self.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)

    def refresh_table(self):
        print ("\nclean table item")
        self.setRowCount(0)

    def add_table_line(self):
        self.setRowCount(self.rowCount()+1)
        print ("\nadd a new row")
        print ("\nrow count num: %s" % (self.rowCount()+1))

    def del_table_line(self):

        selected_items = self.selectedItems()
        if len(selected_items) == 0:
            print ("\nselect 0")
            self.removeRow(self.rowCount()-1)
            print ("\ndel a row")
        selected_items = [selected_items[i] for i in range(len(selected_items)-1, -1, -2)]
        print (selected_items)
        for items in selected_items:
            self.removeRow(self.indexFromItem(items).row())
            
#程序主要布局
class Main(QDialog):
    def __init__(self, parent = maya_main_window()):#可关联到maya 主窗口，这样就可以保持一直在前面 parent= none则是独立窗口
        super(Main, self).__init__(parent)         

        self.setWindowTitle("Auto Exp Fbx Tools")
        self.setMinimumSize(900,600)

        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)#隐藏界面问号按钮

        # 1、提供 .css 或者 .qss 样式文件路径
        style_file = "D:/ScriptProjs/BooBoo/Diffnes.qss"
        if os.path.isfile(style_file):
            # 2、读取样式文件内容
            with open(style_file, "r") as file:
                style_sheet = file.read()
                
                # 3、加载读取的样式内容
                self.setStyleSheet(style_sheet)


        self.imp_widgets()
        self.save_widgets()
        self.autobatch_widgets()
        self.exp_obj_widgets()
        self.add_opt_widgets()
        self.mark_seg_widgets()
        self.fbx_exp_opt_widgets()
        self.table_btn()
        self.create_layout()

        load_plugin('fbxmaya.mll')

    def imp_widgets(self):
        self.imp_grpbox = QGroupBox("Target Folder")
        self.imp_mainlayout = QVBoxLayout(self.imp_grpbox)
        self.imp_tx = QLabel("Imp: ", self.imp_grpbox)
        self.imp_lineTx = QLineEdit(self.imp_grpbox)
        self.imp_lineTx.setObjectName("imp_line_tx")
        self.imp_folder_btn = QPushButton("<<<", self.imp_grpbox)
        self.imp_folder_btn.setMaximumWidth(50)
        self.cuttent_file_btn = QPushButton("M", self.imp_grpbox)
        self.cuttent_file_btn.setMaximumWidth(25)

        self.con_lay = QHBoxLayout()
        self.con_lay.addWidget(self.imp_tx)
        self.con_lay.addWidget(self.imp_lineTx)
        self.con_lay.addWidget(self.imp_folder_btn)
        self.con_lay.addWidget(self.cuttent_file_btn)

        self.sub_dir_chbox = QCheckBox(u"Scan Subfolders", self.imp_grpbox)

        self.imp_mainlayout.addLayout(self.con_lay)
        self.imp_mainlayout.addWidget(self.sub_dir_chbox)

        self.imp_folder_btn.clicked.connect(self.file_path)
        self.cuttent_file_btn.clicked.connect(self.current_file)
        self.cuttent_file_btn.clicked.connect(self.table_element)

    def save_widgets(self):
        self.save_grpbox = QGroupBox("Save Folder")
        self.save_mainlayout = QHBoxLayout(self.save_grpbox)
        self.save_tx = QLabel("Out: ", self.save_grpbox)
        self.save_lintTx = QLineEdit(self.save_grpbox)
        self.save_lintTx.setObjectName("save_line_tx")
        self.save_folder_btn = QPushButton("<<<", self.save_grpbox)
        
        self.save_con_lay = QHBoxLayout()
        self.save_con_lay.addWidget(self.save_tx)
        self.save_con_lay.addWidget(self.save_lintTx)
        self.save_con_lay.addWidget(self.save_folder_btn)

        self.save_mainlayout.addLayout(self.save_con_lay)

        self.save_folder_btn.clicked.connect(self.save_file_path)

    def autobatch_widgets(self):
        self.autobatch_mainlayout = QVBoxLayout()
        self.autobatch_btn = QPushButton("Auto Batch Export")
        self.autobatch_btn.setMinimumHeight(40)
        self.autobatch_mainlayout.addWidget(self.autobatch_btn)

        self.autobatch_btn.clicked.connect(self._run_exp)

    def exp_obj_widgets(self):
        self.expObj_grpbox = QGroupBox("Exp Objects")
        self.expObj_mainLayout = QVBoxLayout(self.expObj_grpbox)
        self.sets_chbox = QCheckBox("Select Sets")
        self.sets_chbox.setMinimumWidth(125)
        self.sets_chbox.setChecked(True)
        self.sets_lineTx = QLineEdit("Allbone")


        self.sets_chbox.clicked['bool'].connect(self.sets_lineTx.setEnabled)

        self.sets_layout = QHBoxLayout()
        self.sets_layout.addWidget(self.sets_chbox)
        self.sets_layout.addWidget(self.sets_lineTx)

        self.mu_sels_chbox = QCheckBox("Manual Selection")
        self.mu_sels_chbox.setMinimumWidth(125)
        self.mu_sels_chbox.setChecked(False)
        self.mu_sels_lineTx = QLineEdit()
        self.mu_sels_lineTx.setEnabled(False)

        self.mu_sels_chbox.clicked['bool'].connect(self.mu_sels_lineTx.setEnabled)

        self.mu_sels_layout = QHBoxLayout()
        self.mu_sels_layout.addWidget(self.mu_sels_chbox)
        self.mu_sels_layout.addWidget(self.mu_sels_lineTx)

        self.reset_chbox = QCheckBox("Reset Z\"0")
        self.reset_chbox.setMinimumWidth(125)
        self.reset_chbox.setChecked(True)    
        self.reset_lineTx = QLineEdit()
        self.reset_lineTx.setText("UnrealRoot")

        self.reset_chbox.clicked['bool'].connect(self.reset_lineTx.setEnabled)

        self.reset_layout = QHBoxLayout()
        self.reset_layout.addWidget(self.reset_chbox)
        self.reset_layout.addWidget(self.reset_lineTx)

        self.expObj_mainLayout.addLayout(self.sets_layout)
        self.expObj_mainLayout.addLayout(self.mu_sels_layout)
        self.expObj_mainLayout.addLayout(self.reset_layout)

    def add_opt_widgets(self):
        self.addOpt_grpbox = QGroupBox("Additional Options")
        self.addOpt_grpbox.setEnabled(False)
        self.addOpt_mainLayout = QVBoxLayout(self.addOpt_grpbox)

        self.loadFile_chbox = QCheckBox(u"Load File:")
        self.loadFile_chbox.setChecked(False) 
        self.loadFile_chbox.setMinimumWidth(125)    
        self.loadFile_lineTx = QLineEdit()
        self.loadFile_lineTx.setEnabled(False)

        self.loadFile_chbox.clicked['bool'].connect(self.loadFile_lineTx.setEnabled)

        self.loadFile_layout = QHBoxLayout()
        self.loadFile_layout.addWidget(self.loadFile_chbox)
        self.loadFile_layout.addWidget(self.loadFile_lineTx)

        self.endOfExp_chbox = QCheckBox(u"End Of Exp:")
        self.endOfExp_chbox.setChecked(False) 
        self.endOfExp_chbox.setMinimumWidth(125)   
        self.endOfExp_lineTx = QLineEdit() 
        self.endOfExp_lineTx.setEnabled(False)

        self.endOfExp_chbox.clicked['bool'].connect(self.endOfExp_lineTx.setEnabled)

        self.endOfExp_layout = QHBoxLayout()
        self.endOfExp_layout.addWidget(self.endOfExp_chbox)
        self.endOfExp_layout.addWidget(self.endOfExp_lineTx)

        self.delExtFrame_chbox = QCheckBox("Delete extra key frame")
        self.delExtFrame_chbox.setObjectName("delExtFrame_chbox")
        self.delNonIntFrame_chbox = QCheckBox("Delete non-integer frame")
        self.delNonIntFrame_chbox.setObjectName("delNonIntFrame_chbox")
        
        self.addOpt_mainLayout.addLayout(self.loadFile_layout)
        self.addOpt_mainLayout.addLayout(self.endOfExp_layout)
        self.addOpt_mainLayout.addWidget(self.delExtFrame_chbox)
        self.addOpt_mainLayout.addWidget(self.delNonIntFrame_chbox)

    def mark_seg_widgets(self):
        self.markSeg_grpbox = QGroupBox("Mark Segment")
        self.markSeg_grpbox.setEnabled(False)
        self.markSeg_mainLayout = QHBoxLayout(self.markSeg_grpbox)

        self.markSeg_chbox = QCheckBox("Segment Mark Obj: ")
        self.markSeg_chbox.setChecked(False)
        self.markSeg_lineTx = QLineEdit()
        self.markSeg_lineTx.setEnabled(False)
        self.markSeg_btn = QPushButton("Selection Tool")
        self.markSeg_btn.setEnabled(False)

        self.markSeg_chbox.clicked['bool'].connect(self.markSeg_lineTx.setEnabled)
        self.markSeg_chbox.clicked['bool'].connect(self.markSeg_btn.setEnabled)

        self.markSeg_mainLayout.addWidget(self.markSeg_chbox)
        self.markSeg_mainLayout.addWidget(self.markSeg_lineTx)
        self.markSeg_mainLayout.addWidget(self.markSeg_btn)

    def fbx_exp_opt_widgets(self):
        self.fbxExpOpt_grpbox = QGroupBox("Fbx Exp Opt")
        self.fbxExpOpt_mainLayout = QVBoxLayout(self.fbxExpOpt_grpbox)

        self.mod_spac1 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        self.mode_radioBtn = QRadioButton("Model    ")
        self.mod_spac2 = QSpacerItem(30,20,QSizePolicy.Minimum,QSizePolicy.Minimum)
        self.ani_radioBtn = QRadioButton("Animation")
        self.ani_radioBtn.setChecked(True)
        self.mod_spac3 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)

        self.modRadio_BtnGrp = QButtonGroup()#添加一个按键组把多个radiobutton包在一起
        self.modRadio_BtnGrp.addButton(self.mode_radioBtn,1)
        self.modRadio_BtnGrp.addButton(self.ani_radioBtn,2)
        
        self.mode_Layout = QHBoxLayout()
        self.mode_Layout.addItem(self.mod_spac1)
        self.mode_Layout.addWidget(self.mode_radioBtn)
        self.mode_Layout.addItem(self.mod_spac2)
        self.mode_Layout.addWidget(self.ani_radioBtn)
        self.mode_Layout.addItem(self.mod_spac3)

        self.mod_spac4 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        self.embedtex_chbox = QCheckBox("Embed Textures")
        self.bakeAni_chbox = QCheckBox("Bake Animation")
        self.bakeAni_chbox.setChecked(True)
        self.reasmaleAll_chbox = QCheckBox("Reasamle All")
        self.curFilters_chbox = QCheckBox("CurveFilters")
        self.mod_spac5 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)

        self.expmethod_layout = QHBoxLayout()
        self.expmethod_layout.addItem(self.mod_spac4)
        self.expmethod_layout.addWidget(self.embedtex_chbox)
        self.expmethod_layout.addWidget(self.bakeAni_chbox)
        self.expmethod_layout.addWidget(self.reasmaleAll_chbox)
        self.expmethod_layout.addWidget(self.curFilters_chbox)
        self.expmethod_layout.addItem(self.mod_spac5)

        self.mod_spac8 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        self.playback_radioBtn = QRadioButton("Playback Range")
        self.playback_radioBtn.setChecked(True)
        self.mod_spac9 = QSpacerItem(30,20,QSizePolicy.Minimum,QSizePolicy.Minimum)
        self.anim_radioBtn = QRadioButton("Animation Range")
        self.mod_spac10 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)

        self.timnerange_RadioBtnGrp = QButtonGroup()
        self.timnerange_RadioBtnGrp.addButton(self.playback_radioBtn,1)
        self.timnerange_RadioBtnGrp.addButton(self.anim_radioBtn,2)

        self.timnerange_Layout = QHBoxLayout()
        self.timnerange_Layout.addItem(self.mod_spac8)
        self.timnerange_Layout.addWidget(self.playback_radioBtn)
        self.timnerange_Layout.addItem(self.mod_spac9)
        self.timnerange_Layout.addWidget(self.anim_radioBtn)
        self.timnerange_Layout.addItem(self.mod_spac10)

        self.mod_spac6 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        self.yUp_radioBtn = QRadioButton("Y-up")
        self.yUp_radioBtn.setChecked(True)
        self.mod_spac7 = QSpacerItem(30,20,QSizePolicy.Minimum,QSizePolicy.Minimum)
        self.zUp_radioBtn = QRadioButton("Z-up")
        self.mod_spac8 = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum)

        self.upMode_RadioBtnGrp = QButtonGroup()
        self.upMode_RadioBtnGrp.addButton(self.yUp_radioBtn,1)
        self.upMode_RadioBtnGrp.addButton(self.zUp_radioBtn,2)
        
        self.upMod_Layout = QHBoxLayout()
        self.upMod_Layout.addItem(self.mod_spac6)
        self.upMod_Layout.addWidget(self.yUp_radioBtn)
        self.upMod_Layout.addItem(self.mod_spac7)
        self.upMod_Layout.addWidget(self.zUp_radioBtn)
        self.upMod_Layout.addItem(self.mod_spac8)

        self.fbxExpOpt_mainLayout.addLayout(self.mode_Layout)
        self.fbxExpOpt_mainLayout.addLayout(self.expmethod_layout)
        self.fbxExpOpt_mainLayout.addLayout(self.upMod_Layout)
        self.fbxExpOpt_mainLayout.addLayout(self.timnerange_Layout)

    def table_btn(self):
        self.table = Table()

        self.table_btn_lay = QHBoxLayout()
        self.refresh_btn = QPushButton()
        self.refresh_btn.setText("Refresh")
        self.add_btn = QPushButton()
        self.add_btn.setText("Add Line")
        self.del_btn = QPushButton()
        self.del_btn.setText("Del Line")
        self.table_btn_lay.addWidget(self.refresh_btn)
        self.table_btn_lay.addWidget(self.add_btn)
        self.table_btn_lay.addWidget(self.del_btn)

        self.refresh_btn.clicked.connect(self.table.refresh_table)
        self.add_btn.clicked.connect(self.table.add_table_line)
        self.del_btn.clicked.connect(self.table.del_table_line)

    def create_layout(self):
        mainlay = QVBoxLayout(self)
        self.main_splitter = QSplitter(self)
        self.main_splitter.setOrientation(Qt.Horizontal)
        self.vLayoutWidget = QWidget(self.main_splitter)
        set_par_mainlay = QVBoxLayout(self.vLayoutWidget)

        set_par_mainlay.addWidget(self.imp_grpbox)
        set_par_mainlay.addWidget(self.save_grpbox)
        set_par_mainlay.addLayout(self.autobatch_mainlayout)
        set_par_mainlay.addWidget(self.expObj_grpbox)
        set_par_mainlay.addWidget(self.addOpt_grpbox)
        set_par_mainlay.addWidget(self.markSeg_grpbox)
        set_par_mainlay.addWidget(self.fbxExpOpt_grpbox)

        self.vLayoutWidget2 = QWidget(self.main_splitter)
        table_mainlay = QVBoxLayout(self.vLayoutWidget2)
        table_mainlay.addWidget(self.table)
        table_mainlay.addLayout(self.table_btn_lay)
        
        mainlay.addWidget(self.main_splitter)

    def file_path(self):
        dir_choose = QFileDialog.getExistingDirectory(self, u"Choose File Folder")
        if dir_choose:
            list_files = []
            self.imp_lineTx.setText("%s/" % dir_choose)
            self.save_lintTx.setText("%s/fbx/" % dir_choose)
            if not os.path.exists("%s/fbx/" % dir_choose):
                fbx_path = ("%s/fbx/" % dir_choose)
                os.makedirs(fbx_path)
            print(u"\nYou Choose File Folder:%s" % dir_choose)
            print(u"\nSave File Path:%s/fbx/" % dir_choose)
            if self.sub_dir_chbox.isChecked():
                for root, dirs, files in os.walk(dir_choose):
                    for f in files:
                        list_files.append(os.path.join(root, f))
            else:
                list_files = os.listdir(dir_choose)
                list_files = list(filter(self.file_filter, list_files))
            for f in range(0,len(list_files)):
                print (f)
                list_files[f] = [(list_files[f]),
                            ("%s/%s" % (dir_choose,list_files[f])),
                            ("%s%s.fbx" % (self.save_lintTx.text(),os.path.splitext(list_files[f])[0]))]
            # print (list_files)
            
            for i in range(len(list_files)):
                item = list_files[i]
                row = self.table.rowCount()
                self.table.insertRow(row)
                # print (item)
                for j in range(len(item)):
                    str_item = QTableWidgetItem(str(list_files[i][j]))
                    self.table.setItem(row,j,str_item)
                    
    def file_filter(self,file_name):
        mayaFilters = ['.ma','.mb','.MA','.MB']
        fbxFilters = ['.fbx','.FBX']
        if file_name[-3:] in mayaFilters or file_name[-4:] in fbxFilters :
            return True
        else:
            return False

    def current_file(self):
        self.imp_lineTx.setText(cmds.file(q=True,sn=True))
        fbx_file_name = os.path.split(cmds.file(q=True,sn=True))[1]
        fbx_file_name = "%s.fbx" % os.path.splitext(fbx_file_name)[0]
        self.save_lintTx.setText("%s/fbx/"% os.path.split(cmds.file(q=True,sn=True))[0])
        self.table.insertRow(self.table.rowCount())
        self.table.setItem(self.table.rowCount()-1,0,
                        QTableWidgetItem(os.path.split(cmds.file(q=True,sn=True))[1]))
        self.table.setItem(self.table.rowCount()-1,1,
                        QTableWidgetItem(cmds.file(q=True,sn=True)))
        self.table.setItem(self.table.rowCount()-1,2,
                        QTableWidgetItem("%s%s" % (self.save_lintTx.text(),fbx_file_name)))
        
        if not os.path.exists(self.save_lintTx.text()):
            fbx_path = (self.save_lintTx.text())
            os.makedirs(fbx_path)

    def save_file_path(self):
        save_dir_choose = QFileDialog.getExistingDirectory(self, u"Choose Save Path") 
        if save_dir_choose:
            self.save_lintTx.setText("%s/fbx/" % save_dir_choose)
            print(u"\nSave File Path:%s/fbx/" % save_dir_choose)
            if not os.path.exists("%s/fbx/" % save_dir_choose):
                fbx_path = ("%s/fbx/" % save_dir_choose)
                os.makedirs(fbx_path)

    def table_element(self):
        rowCount = self.table.rowCount()
        print (u"Row Count %s Line \n"% rowCount)
        return True

    def reset_zero(self,reset_obj):
        if cmds.objExists(("|%s" % reset_obj)) == 1:
            reset_obj = ("|%s" % reset_obj)
            tran = ["X","Y","Z"]
            for t in range(len(tran)):
                connode = cmds.findKeyframe(reset_obj, curve=True, at=("translate%s"%tran[t]) )
                all_keyframes = cmds.keyframe(connode[0], q=True)
                start_v = cmds.keyframe(connode[0], q=True, eval=True, time=(all_keyframes[0],all_keyframes[0]))[0]
                
                v = cmds.keyframe(reset_obj,q=True, vc=True, at=("translate%s"%tran[t]) )
                for i in range(len(v)):
                    value = v[i]-start_v
                    cmds.keyframe( connode[0],e=True, index=(i, (i)), a=True, vc = value)
    
    def remove_namespaces(self,node):
        try:
            namespace, name = node.rsplit(":", 1)
        except:
            namespace, name = None, node
        if namespace:
            try:
                cmds.rename(node, name)
            except RuntimeError:
                pass

    def export_ani_assets(self,save_filePath):
        save_data = {}
        if cmds.ls(type ='timeSliderBookmark'):
            for mark in cmds.ls(type='timeSliderBookmark'):
                save_data[(cmds.getAttr('%s.name' % mark))] = ( (cmds.getAttr('%s.timeRangeStart' % mark)),
                                            (cmds.getAttr('%s.timeRangeStop' % mark)))
        else:
            time_id = self.timnerange_RadioBtnGrp.checkedId()
            if time_id == 1:
                save_data['default'] = (int(cmds.playbackOptions(q=True, min=True)),
                                        int(cmds.playbackOptions(q=True, max=True)))
            else:
                save_data['default'] = (int(cmds.playbackOptions(q=True, ast=True)),
                                        int(cmds.playbackOptions(q=True, aet=True)))

        #sets是否存在，获取他行里名字
        if self.sets_lineTx.text():
            sets = self.sets_lineTx.text()# cmds.sets(self.sets_lineTx.text(),q=True)

            #去除前缀
            list1 = cmds.ls(typ = "objectSet")
            data = [x for i,x in enumerate(list1) if x.find(sets) != -1]#Search All Bone
            if len(data) == 1:
                if len(data[0].split(':'))>1:
                    if cmds.referenceQuery(data[0],inr=True):
                        bone_file_path = cmds.referenceQuery( data[0], f=True )
                        cmds.file(bone_file_path,ir=True)

                    for node in cmds.sets(data[0],q=True):
                        self.remove_namespaces(node)
            
        #烘焙sets内物体得动画
        allbone = cmds.sets(data[0],q=True)
        pm.bakeResults(allbone,sm=True,
                        t=(int(cmds.playbackOptions(q=True, ast=True)),
                            int(cmds.playbackOptions(q=True, aet=True))),
                        sb=1,osr=1,dic=True,pok=True,sac=False,ral=False,
                        rba=False,bol=False,mr=True,cp=True,s=True)

        #去除关联

        #设置归0
        if self.reset_chbox.isChecked() and self.reset_lineTx.text() != "":
            self.reset_zero(self.reset_lineTx.text())

        for name,frame in save_data.items():
            if name is not "default":
                SaveFilePath = "%s_%s.fbx" %(os.path.splitext(save_filePath)[0],name)
            StartFrame,EndFrame = frame
            StartFrame = int(StartFrame)
            EndFrame = int(EndFrame)
            #导出设置
            pm.mel.FBXResetExport()
            pm.mel.eval('FBXExportSplitAnimationIntoTakes -c')
            pm.mel.FBXExportSmoothingGroups(v=True)
            pm.mel.FBXExportSmoothMesh(v=True)
            pm.mel.FBXExportReferencedAssetsContent(v=True)
            pm.mel.FBXExportBakeComplexAnimation(v=True)
            pm.mel.FBXExportBakeComplexStart(v=StartFrame)
            pm.mel.FBXExportBakeComplexEnd(v=EndFrame)
            # pm.mel.FBXExportSkins(v=True)
            # pm.mel.FBXExportShapes(v=True)
            pm.mel.FBXExportInputConnections(v=False)
            pm.mel.FBXExportConstraints(v=False)
            pm.mel.FBXExportUpAxis('y')
            pm.mel.FBXExportFileVersion(v='FBX201300')
            pm.mel.FBXExportInAscii(v=True)
            pm.mel.FBXExportEmbeddedTextures(v=False)

            #导出
            cmds.select(cl = True)
            cmds.select(allbone,add=True)
            pm.mel.eval('FBXExportSplitAnimationIntoTakes -v \"tata\" %d %d'%(int(StartFrame), int(EndFrame)))
            cmds.FBXExport('-file', SaveFilePath, '-s')
            # pm.mel.FBXExport(s=True, f=SaveFilePath)
            # cmds.file(save_filePath.decode('utf8'), options='v=0;', typ='FBX export', pr=True, es=True, force=True)
        
    # 遍历所有表单内容，然后按列表得形式保存    
    def table_items(self):
        items = []
        for row in range(self.table.rowCount()):
            itemsCount = []
            for col in range(self.table.columnCount()):
                if self.table.item(row,col).text() != None: 
                    itemsCount.append(self.table.item(row,col).text())
            
            items.append(itemsCount)
        return items
        
    def _run_exp(self):
        items = self.table_items()
        for item in range(len(items)):
            name,FilePath,SavePath = items[item]
            # print ("\nThe Maya File Path: %s " % FilePath)
            cmds.file(FilePath,f=True,op="v=0",iv=True,o=True)
            self.export_ani_assets(SavePath)

if __name__ == "__main__":
    try:
        ui.close()
        ui.deleteLater()
    except:
        pass

    ui = Main()
    ui.show()