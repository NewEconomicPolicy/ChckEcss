#-------------------------------------------------------------------------------
# Name:
# Purpose:     GUI front end to enable checking of Ecosse outputs
# Author:      Mike Martin
# Created:     8/3/2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'CheckEcosseGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from os.path import normpath, join, isfile
from time import sleep
import sys
from subprocess import Popen, DEVNULL
from glob import glob
from copy import copy

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, \
                                QPushButton, QCheckBox, QFileDialog, QTextEdit

from analyse_site_spec_dir import Analysis, check_identical_files, check_input_file_compliance
import analyse_ecosse_output
from analyse_ecosse_output import format_out_files
from initialise_check_ecosse import read_config_file, write_config_file, initiation
from generate_charts_funcs import generate_charts
from common_funcs import run_site_specific
from set_up_logging import OutLog

EXCEL_EXE1 = join('C:\\Program Files\\Microsoft Office\\root\\Office16', 'EXCEL.EXE')
EXCEL_EXE2 = join('C:\\Program Files (x86)\\Microsoft Office\\root\\Office16', 'EXCEL.EXE')

WDGT_WDTH_60 = 60
WDGT_WDTH_95 = 95
WDGT_WDTH_120 = 120
sleepTime= 3

class Form(QWidget):

    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        initiation(self)
        font = QFont(self.font())
        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)	# set spacing between widgets

        # directory containing reference outputs
        # ======================================
        irow = 1
        w_ref_dir = QPushButton("Reference dir")
        helpText = 'Directory with verified Ecosse output'
        w_ref_dir.setToolTip(helpText)
        grid.addWidget(w_ref_dir, irow, 0)
        w_ref_dir.clicked.connect(self.fetchRefDir)

        w_lbl03 = QLabel('')
        grid.addWidget(w_lbl03, irow, 1, 1, 5)
        self.w_lbl03 = w_lbl03

        # ======
        irow += 1
        lbl01 = QLabel('Reference identifier:')
        grid.addWidget(lbl01, irow, 0)
        lbl01.setAlignment(Qt.AlignRight)

        w_ref_id = QLineEdit()
        helpText = 'Identifier used for reference outputs on chart'
        w_ref_id.setToolTip(helpText)
        w_ref_id.setFixedWidth(WDGT_WDTH_120)
        grid.addWidget(w_ref_id, irow, 1)
        self.w_ref_id = w_ref_id

        # spacer
        irow += 1
        grid.addWidget(QLabel(' '), irow, 1)

        # widget set for first Target dir
        # ===============================
        irow += 1
        w_targ1_dir = QPushButton("Target 1 dir")
        helpText = 'First directory consisting of ECOSSE outputs against which reference outputs will be compared'
        w_targ1_dir.setToolTip(helpText)
        grid.addWidget(w_targ1_dir, irow, 0)
        w_targ1_dir.clicked.connect(self.fetchTarg1Dir)

        w_lbl04 = QLabel()
        grid.addWidget(w_lbl04, irow, 1, 1, 5)
        self.w_lbl04 = w_lbl04

        # ======
        irow += 1
        lbl02 = QLabel('Target 1 identifier:')
        grid.addWidget(lbl02, irow, 0)
        lbl02.setAlignment(Qt.AlignRight)

        w_targ1_id = QLineEdit()
        helpText = 'Identifier used for target 1 outputs on chart'
        w_targ1_id.setToolTip(helpText)
        w_targ1_id.setFixedWidth(WDGT_WDTH_120)
        grid.addWidget(w_targ1_id, irow, 1)
        self.w_targ1_id = w_targ1_id

        # report on numbers of .OUT files
        # ===============================
        irow += 1
        self.w_lbl05 = QLabel()
        grid.addWidget(self.w_lbl05, irow, 1, 1, 5)

        # spacer
        irow += 1
        grid.addWidget(QLabel(' '), irow, 1)

        # ======
        irow += 1
        w_targ2_also = QCheckBox('Use target 2 also')
        w_targ2_also.setChecked(True)
        grid.addWidget(w_targ2_also, irow, 0, 1, 2)
        w_targ2_also.clicked.connect(self.adjustWdgts)
        self.w_targ2_also = w_targ2_also

        # second target directory of output files to be compared
        # ======================================================
        irow += 1
        w_targ2_dir = QPushButton("Target 2 dir")
        helpText = 'Second directory consisting of ECOSSE outputs against which reference outputs will be compared'
        w_targ2_dir.setToolTip(helpText)
        grid.addWidget(w_targ2_dir, irow, 0)
        w_targ2_dir.clicked.connect(self.fetchTarg2Dir)
        self.w_targ2_dir = w_targ2_dir

        w_lbl06 = QLabel()
        grid.addWidget(w_lbl06, irow, 1, 1, 5)
        self.w_lbl06 = w_lbl06

        # ======
        irow += 1
        lbl08 = QLabel('Target 2 identifier:')
        grid.addWidget(lbl08, irow, 0)
        lbl08.setAlignment(Qt.AlignRight)

        w_targ2_id = QLineEdit()
        helpText = 'Identifier used for target 2 outputs on chart'
        w_targ2_id.setToolTip(helpText)
        w_targ2_id.setFixedWidth(WDGT_WDTH_120)
        grid.addWidget(w_targ2_id, irow, 1)
        self.w_targ2_id = w_targ2_id

        # report on numbers of .OUT files
        # ===============================
        irow += 1
        self.w_lbl07 = QLabel()
        grid.addWidget(self.w_lbl07, irow, 1, 1, 5)

        # spacer
        irow += 1
        grid.addWidget(QLabel(' '), irow, 1)

        # =======
        irow += 1
        w_smmry_only = QCheckBox('Compare SUMMARY.OUT only')
        w_smmry_only.setChecked(True)
        # w_smmry_only.setEnabled(False)
        grid.addWidget(w_smmry_only, irow, 0, 1, 2)
        self.w_smmry_only = w_smmry_only

        # ========
        lbl16 = QLabel('Water depth (cms):')
        grid.addWidget(lbl16, irow, 4)
        lbl16.setAlignment(Qt.AlignRight)

        w_water_dep = QLineEdit()
        helpText = 'Depth for soil water chart [cm] e.g. 50, 100, 300 (max)'
        w_water_dep.setToolTip(helpText)
        w_water_dep.setFixedWidth(WDGT_WDTH_60)
        grid.addWidget(w_water_dep, irow, 5)
        self.w_water_dep = w_water_dep

        # spacer
        irow += 1
        grid.addWidget(QLabel(' '), irow, 1)

        # widget set for Results dir
        # ==========================
        irow += 1
        w_rslts_dir = QPushButton("Results file dir")
        helpText = 'Directory to which results, i.e. the Excel file will be written'
        w_rslts_dir.setToolTip(helpText)
        grid.addWidget(w_rslts_dir, irow, 0)
        w_rslts_dir.clicked.connect(self.fetchRsltsDir)

        w_lbl13 = QLabel()
        grid.addWidget(w_lbl13, irow, 1, 1, 5)
        self.w_lbl13 = w_lbl13

        w_view_res = QPushButton("View results")
        helpText = 'View results'
        w_view_res.setToolTip(helpText)
        w_view_res.setMinimumWidth(WDGT_WDTH_95)
        w_view_res.clicked.connect(self.viewChartsClicked)  # signal/slot
        grid.addWidget(w_view_res, irow, 5)

        # spacer
        irow += 1
        grid.addWidget(QLabel(' '), irow, 1)

        # actions
        # =======
        irow += 1
        w_check_carbon = QPushButton("Chart OUT files")
        helpText = 'Perform comparison of reference, target 1 and target 2 Carbon and Nitrogen related *.OUT files\n' + \
            '- generates charts of carbon and nitrogen metric sets'
        w_check_carbon.setToolTip(helpText)
        w_check_carbon.clicked.connect(self.chartOutFilesClicked)  # signal/slot
        grid.addWidget(w_check_carbon, irow, 0)

        w_indentical_files = QPushButton("Diff input files")
        helpText = 'Report whether all .dat and .txt files for reference and target 1 directories are identical or different'
        w_indentical_files.setToolTip(helpText)
        w_indentical_files.clicked.connect(self.diffInputFilesClicked)
        grid.addWidget(w_indentical_files, irow, 1)

        w_compliance = QPushButton("Check input files")
        helpText = 'Check necessary input files are present and compliant: fnames.dat, management.txt, site.txt and soil.txt'
        w_compliance.setToolTip(helpText)
        w_compliance.setFixedWidth(WDGT_WDTH_120)
        w_compliance.clicked.connect(self.checkInputFileComplianceClicked)
        grid.addWidget(w_compliance, irow, 1)

        w_lite_check = QPushButton("Diff output files")
        helpText = 'Perform comparison of reference and target 1 *.OUT files' + \
                   '- only reports whether same or different'
        w_lite_check.setToolTip(helpText)
        w_lite_check.clicked.connect(self.diffOutputFilesClicked)  # signal/slot
        grid.addWidget(w_lite_check, irow, 2)

        w_check_files = QPushButton("Compare OUT files")
        helpText = 'Perform comparison of reference and target 1 *.OUT files' + \
                   '- generates Excel spreadsheet of differences'
        w_check_files.setEnabled(False)
        w_check_files.setToolTip(helpText)
        w_check_files.clicked.connect(self.compareOutFilesClicked)  # signal/slot
        grid.addWidget(w_check_files, irow, 3)

        icol = 5
        w_clear = QPushButton("Clear window", self)
        helpText = 'Clear reporting window'
        w_clear.setToolTip(helpText)
        w_clear.clicked.connect(self.clearReporting)
        grid.addWidget(w_clear, irow, icol)

        icol += 1
        w_save = QPushButton("Save")
        helpText = 'Save configuration file without exiting program'
        w_save.setToolTip(helpText)
        w_save.setFixedWidth(WDGT_WDTH_60)
        grid.addWidget(w_save, irow, icol)
        w_save.clicked.connect(self.saveClicked)

        icol += 1
        w_cancel = QPushButton("Cancel")
        helpText = 'Leaves GUI without saving the configuration file'
        w_cancel.setToolTip(helpText)
        w_cancel.setFixedWidth(WDGT_WDTH_60)
        grid.addWidget(w_cancel, irow, icol)
        w_cancel.clicked.connect(self.cancelClicked)

        icol += 1
        w_exit = QPushButton("Exit", self)
        w_exit.setFixedWidth(WDGT_WDTH_60)
        grid.addWidget(w_exit, irow, icol)
        w_exit.clicked.connect(self.exitClicked)

        # more actions
        # ============
        irow += 1
        w_run_ss = QPushButton("Run SS", self)
        helpText = 'runs site specific mode only for 30 years with vigour'
        w_run_ss.setToolTip(helpText)
        w_run_ss.setEnabled(False)
        w_run_ss.clicked.connect(self.runSiteSpecificClicked)
        grid.addWidget(w_run_ss , irow, 5)



        run_tests = QPushButton("Directory scan")
        helpText = 'Summarises files in reference directory'
        run_tests.setToolTip(helpText)
        run_tests.clicked.connect(self.directoryScanClicked)
        grid.addWidget(run_tests, irow, 1)

        # LH vertical box consists of png image
        # =====================================
        lh_vbox = QVBoxLayout()

        lbl20 = QLabel()
        lbl20.setPixmap(QPixmap(self.settings['fname_png']))
        lh_vbox.addWidget(lbl20)

        # add grid consisting of combo boxes, labels and buttons to RH vertical box
        # =========================================================================
        rh_vbox = QVBoxLayout()
        rh_vbox.addLayout(grid)

        # add reporting
        # =============
        bot_hbox = QHBoxLayout()
        w_report = QTextEdit()
        w_report.verticalScrollBar().minimum()
        w_report.setMinimumHeight(300)
        w_report.setMinimumWidth(1000)
        w_report.setStyleSheet('font: bold 10.5pt Courier')  # big jump to 11pt
        ''' 
        w_report.setStyleSheet('font: 9pt Courier')
        w_report.setStyleSheet('font: normal 12px Calabri; color: blue;'
                               'background-color: yellow;'
                               'selection-color: yellow;'
                               'selection-background-color: blue;')
        '''
        bot_hbox.addWidget(w_report, 1)
        self.w_report = w_report
        sys.stdout = OutLog(self.w_report, sys.stdout)
        # sys.stderr = OutLog(self.w_report, sys.stderr, QColor(255, 0, 0))

        # add LH and RH vertical boxes to main horizontal box
        # ===================================================
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(10)
        main_hbox.addLayout(lh_vbox)
        main_hbox.addLayout(rh_vbox, stretch = 1)

        # feed horizontal boxes into the window
        # =====================================
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_hbox)
        outer_layout.addLayout(bot_hbox)
        self.setLayout(outer_layout)

        # posx, posy, width, height
        self.setGeometry(125, 125, 690, 250)
        self.setWindowTitle('Check and compare Ecosse inputs and outputs')

        read_config_file(self)

    # =======================================
    def viewChartsClicked(self):
        '''
        view Excel charts
        chdir('E:\\temp')
        system('start excel.exe parms.xlsx')
        '''
        if isfile(EXCEL_EXE1):
            excel_exe = copy(EXCEL_EXE1)
        else:
            excel_exe = copy(EXCEL_EXE2)

        rslts_dir = self.w_lbl13.text()
        xls_flist = glob(rslts_dir + '/*.xlsx')
        if len(xls_flist) > 0:
            fname = xls_flist[0]
        else:
            fname = ''

        xls_fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'Excel files (*.xlsx)')
        if xls_fname != '':
            try:
                Popen(list([excel_exe, normpath(xls_fname)]), stdout=DEVNULL)
            except PermissionError as err:
                print(str(err))

    def adjustWdgts(self):
        #
        if self.w_targ2_also.isChecked():
            self.w_targ2_dir.setEnabled(True)
            self.w_targ2_id.setEnabled(True)
        else:
            self.w_targ2_dir.setEnabled(False)
            self.w_targ2_id.setEnabled(False)

    def clearReporting(self):
        #
        self.w_report.clear()

    def checkInputFileComplianceClicked(self):
        # check compliance of input files: fnames.dat, management.txt, site.txt and soil.txt
        check_input_file_compliance(self)

    def diffInputFilesClicked(self):
        # report whether .dat and .txt files for reference and target 1 directories are identical or different
        check_identical_files(self)    

    def diffOutputFilesClicked(self):
        # perform shallow comparison of reference and target 1 *.OUT files
        check_identical_files(self, file_types = 'output')

    def chartOutFilesClicked(self):
        # generates charts of carbon and nitrogen metric sets
        generate_charts(self)

    def compareOutFilesClicked(self):
        # generate Excel spreadsheet of differences between reference and target 1 *.OUT files
        analysis = analyse_ecosse_output.Analysis(self)   # initialises object
        analysis.check_ecosse_files(self)  # creates a summary file

    def directoryScanClicked(self):
        # summarises files in reference directory
        analysis = Analysis(self)           # initialises object
        analysis.check_these_files(self)    # creates summary file

    def runSiteSpecificClicked(self):
        # runs site specific mode only for 30 years with vigour
        run_site_specific(self)

    def fetchRefDir(self):
        #
        fname = self.w_lbl03.text()
        fname = QFileDialog.getExistingDirectory(self, 'Select directory', fname)
        if fname != '':
            fname = normpath(fname)
            self.w_lbl03.setText(fname)
            self.w_lbl05.setText(format_out_files(self))

    def fetchTarg1Dir(self):
        #
        fname = self.w_lbl04.text()
        fname = QFileDialog.getExistingDirectory(self, 'Select directory', fname)
        if fname != '':
            fname = normpath(fname)
            self.w_lbl04.setText(fname)
            self.w_lbl05.setText(format_out_files(self))

    def fetchTarg2Dir(self):
        #
        fname = self.w_lbl06.text()
        fname = QFileDialog.getExistingDirectory(self, 'Select directory', fname)
        if fname != '':
            fname = normpath(fname)
            self.w_lbl06.setText(fname)
            self.w_lbl07.setText(format_out_files(self, target_flag = 'targ2'))

    def fetchRsltsDir(self):
        #
        fname = self.w_lbl13.text()
        fname = QFileDialog.getExistingDirectory(self, 'Select directory', fname)
        if fname != '':
            fname = normpath(fname)
            self.w_lbl13.setText(fname)

    def cancelClicked(self):

        func_name = __prog__ + ' cancelClicked'

        print('Terminating program without saving configuration file')
        QApplication.processEvents()
        sleep(sleepTime)
        self.close()

    def saveClicked(self):
        # write last path selections
        write_config_file(self)
        print('Wrote configuration file')
        QApplication.processEvents()

    def exitClicked(self):
        # write last path selections
        write_config_file(self)
        self.close()

def main():

    app = QApplication(sys.argv)  # create QApplication object
    form = Form()     # instantiate form
    form.show()       # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
