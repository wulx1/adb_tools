# -*- coding: utf-8 -*-
# @Time : 2024/3/9 19:12
# @Author : longswu
# @File : xmind2excel.py


import os
import sys
import json
import fnmatch
import copy
import xlwt
from xmindparser import xmind_to_dict, xmind_to_json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import * 


 
# 转换xmind文件名转excel文件名
def xmind_to_excel_filename(filename):
    
    excel_path = os.path.dirname(filename)
    excel_name = os.path.splitext(filename)[0]
    excel_file = os.path.join(excel_path, excel_name + '.xls')
    
    return  excel_file
 


def search_files(path, filterext = "*.xmind"):
    
    filepaths = []
    
    for dirpath, dirnames, filenames in os.walk(path): 
        for filename in filenames:
            if fnmatch.fnmatch(filename, filterext):  
                filepath = os.path.join(dirpath, filename)
                filepaths.append(filepath)
                
    return filepaths


# 禅道excel数据
class ExcelColData(object):
    
    def __init__(self, col_datas = None):
        self.col_datas = col_datas or [ 
            {
                'level': 1,
                'title': '用例名称'
            },
            {
                'level': 2,
                'title': '用例模块'
            },
            {
                'level': 3,
                'title': '用例描述'
            },
            {
                'level': 4,
                'title': '前提条件'
            },
            {
                'level': 5,
                'title': '操作步骤'
            },
            {
                'level': 6,
                'title': '预期结果'
            },
            {
                'level': 7,
                'title': '备注'
            },
            {
                'level': 8,
                'title': '测试结果'
            },
            {
                'level': 9,
                'title': '优先级'
            },
            {
                'level': 10,
                'title': '占用'
            },
            {
                'level': 11,
                'title': '占用'
            },
            {
                'level': 12,
                'title': '占用'
            }
        ]            

    def isExistLevel(self, level):
        
        for col in self.col_datas:
            if level == col['level']:
                return True
            
        return False

    def toTitles(self):
        
        titles = []
        for col in self.col_datas:
            titles.append(col['title'])
        
        return titles
    
    

# xmind转excel处理类
class XmindToExcel:
    """"""

    # 初始化
    def __init__(self, filename):
        """Constructor"""
        
        self.excel_col = ExcelColData()
        self.titles = self.excel_col.toTitles()
        
        # 读取xmind文件
        self.xmind_datas = self.readXmindData(filename)
        
        # 解析xmind数据
        self.excel_datas = self.parserXmind()
        
        # 创建表格，初始化
        self._workbook = xlwt.Workbook(encoding = 'utf-8')
        self._sheet = self._workbook.add_sheet('sheet1')
        
        
    # xmind_to_dict 将xmind转为dict
    def readXmindData(self, filename):
            
        dict_data = xmind_to_dict(filename)
        #输出topics下的子节点
        topics_data = dict_data[0]
        print(topics_data)
        
        return topics_data
        
        
    # 分析数据,该方法用于生成用例名称,格式为模块1_模块2_模块3_模块4_……，
    def parserXmind(self):
        
        case_datas = []
        col_list = []
        col_level = 0
        self.parseNode(self.xmind_datas, case_datas, col_list, col_level)
        
        return case_datas    
    
    def parseNode(self, node_lists, case_list, col_list, col_level):
        
        if len(node_lists) >= 1:
            col_level += 1
            isLevel = self.excel_col.isExistLevel(col_level)
            print(col_level)
            
            if isinstance(node_lists, dict) and 'topic' in node_lists.keys():
                # 设置根节点
                if self.excel_col.isExistLevel(col_level):
                    col_list.append(node_lists['topic']['title'])
                
                # 遍历子节点
                self.parseNode(node_lists['topic']['topics'], case_list, col_list, col_level)
                
            else:
                
                for node in node_lists:
                    temp_col_list = []
                    # 如何知道遍历的是最后一个节点
                    # 当前的node的所有的key中没有topics，那就说明是最后一个节点了
                    if 'topics' in node.keys():
                        for key in node:
                            if key == "title":
                                if isLevel:
                                    temp_col_list.append(node[key])
                            
                            #elif key == "makers":
                                #if isLevel:
                                    #temp_col_list.append(self.parserPriority(node[key]))
            
                            elif key == "topics":
                                # 遍历子节点
                                self.parseNode(node[key], case_list, col_list + temp_col_list, col_level)
            
                    else:
                        # 最后一个节点
                        if isLevel:
                            for key in node:
                                if key == "title":
                                    temp_col_list.append(node[key])
                                
                                #elif key == "makers":
                                    #temp_col_list.append(self.parserPriority(node[key]))
                                    
                        # 添加数据
                        case_list.append(col_list + temp_col_list)

    
    def parserPriority(self, makers):
        
        # 开始设置优先级
        if len(makers) != 0:
            priority = makers[0]
            if priority.startswith('priority-'):
                return priority[len('priority-'):]
   
        
        return ''
    

        
    # 用于设置插入excel的标题
    def write_header(self, titles):
        print(titles)
        for i in range(len(titles)):
            self._sheet.write(0, i, titles[i])
    
    # 写入数据    
    def write_datas(self, datas):
        
        for row in range(len(datas)):
            print(datas[row])
            for col in range(len(datas[row])):
                self._sheet.write(row + 1, col, datas[row][col])
        

    # 保存
    def save(self, filename):
        
        # 写入excel数据
        self.write_header(self.titles)
        self.write_datas(self.excel_datas)
        
        # 保存到文件
        self._workbook.save(filename)
 
 
 
class WorkThread(QThread):
    """"""

    def __init__(self, frame):
        """Constructor"""
        super().__init__()
        self._frame = frame
    
    def run(self):
        
        self._frame.runTask()
 
 
 
class MainFrame(QWidget):
    """"""

    def __init__(self):
        """Constructor"""
        self._thread = None
        
        super().__init__()
        self.initUI()
        
    def __del__(self):
        
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread = None
        
        
    def initUI(self):
        
        self.setWindowTitle("Xmind转Excel文件")
        self.resize(650, 450)

        label = QLabel("输入文件路径：", self)
        self.edit_path = QLineEdit(self)
        self.btn_open = QPushButton("选择xmind文件", self)
        self.btn_dir = QCheckBox("目录", self)
        # self.btn_dir.setStyleSheet('color: red; font-weight: bold;')
        
        group = QGroupBox("转换信息如下：", self)
        self.filelist = QListView(self)
        self.listmodel = QStringListModel()
        self.filelist.setModel(self.listmodel)
        
        glayout = QVBoxLayout()
        glayout.addWidget(self.filelist, 1)
        group.setLayout(glayout)
        
        self.btn_gen = QPushButton("执行转换", self)
        self.btn_gen.setStyleSheet('font-weight: bold;')
        self.btn_gen.setFixedSize(80, 36)
        
        layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QHBoxLayout()
        
        layout1.addWidget(label)
        layout1.addWidget(self.edit_path)
        layout1.addWidget(self.btn_open)
        layout1.addWidget(self.btn_dir)
        
        layout2.addWidget(group)
        layout3.addWidget(self.btn_gen)

        
        layout.addLayout(layout1)
        layout.addSpacing(8)
        layout.addLayout(layout2)
        layout.addLayout(layout3)
        
        self.setLayout(layout)
        
        self.btn_open.clicked.connect(self.onClickOpen)
        self.btn_gen.clicked.connect(self.onClickedGen)
        
        
    def onClickOpen(self, evt):
        
        dlg = QFileDialog(self)
        if self.btn_dir.isChecked():
            dlg.setWindowTitle("请选择目录")
            dlg.setFileMode(QFileDialog.Directory)
        else:
            dlg.setWindowTitle("请选择文件")
            dlg.setNameFilter("xmind file (*.xmind)")
        
        ret = dlg.exec_()
        if ret == QDialog.Accepted:
            self.edit_path.setText(dlg.selectedFiles()[0])
        
    def onClickedGen(self, evt):
        
        filepath = self.edit_path.text()
        if filepath:
            if os.path.exists(filepath):
                isfile = os.path.isfile(filepath)
                isdir = os.path.isdir(filepath)
                if isfile or isdir:
                    self.btn_gen.setEnabled(False)
                    self._thread = WorkThread(self)
                    self._thread.start()
                else:
                    QMessageBox.warning(self, "警告提示", "您输入的文件路径无效，请重新输入！")
            else:
                QMessageBox.warning(self, "警告提示", "您输入的文件路径不存在，请重新输入！")
        else:
            QMessageBox.warning(self, "警告提示", "请先输入文件路径！")    
            
    
    def runTask(self):
        
        self.listmodel.removeRows(0, self.listmodel.rowCount())
        filepath = self.edit_path.text()
        isfile = os.path.isfile(filepath)
        self.genToExcel(filepath, isfile)
        self._thread = None
        
    
    def genToExcel(self, filepath, isfile = True):
        
        if isfile:
            print(filepath)
            self.genToSingleExcel(filepath)
        else:
            filepaths = search_files(filepath)
            print(filepaths)
            for filename in filepaths:
                self.genToSingleExcel(filename)
        
        self.btn_gen.setEnabled(True)
        
            
    def genToSingleExcel(self, xmind_path):
        
        excel_path = xmind_to_excel_filename(xmind_path)
        excel_name = os.path.basename(excel_path)
        display_info = xmind_path + " ->>> " + excel_name
       
        row = self.listmodel.rowCount()
        self.listmodel.insertRow(row)       
        self.listmodel.setData(self.listmodel.index(row), display_info + " - 进行中...")
       
        xe = XmindToExcel(xmind_path)
        xe.save(excel_path)

        self.listmodel.setData(self.listmodel.index(row), display_info + " - 转成完成!"+"\n"+f"转换后保存在：{excel_path}")
        # self.listmodel.setData(self.listmodel.index(row), xmind_path+" -> "+"\n" + excel_path)
        # self.listmodel.setData(self.listmodel.index(row), display_info+ f" - excel文件路径为：{excel_path}")

    # def show_conversion_complete_message(output_file):
    #     message_box = QMessageBox()
    #     message_box.setIcon(QMessageBox.Information)
    #     message_box.setWindowTitle("转换完成")
    #     message_box.setText(f"转换完成！已保存到：\n{output_file}")
    #     message_box.exec_()
       
       

  
 
 
if __name__ == '__main__':
   
    app = QApplication(sys.argv)
    
    frame = MainFrame()
    frame.show()
    
    code = app.exec_()
    sys.exit(code)