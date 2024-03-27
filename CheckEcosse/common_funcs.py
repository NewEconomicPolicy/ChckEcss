#-------------------------------------------------------------------------------
# Name:        common_funcs.py
# Purpose:     script to read Astley's file and create new one with just MU_GLOBALS and Lat Longs
# Author:      Mike Martin
# Created:     31/07/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'common_funcs.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import join, splitext, isdir, exists
from os import chdir, getcwd, remove
from openpyxl import Workbook
import subprocess

val702 = 26*27
val26  = 26

def run_site_specific(form):

    # runs site specific mode only for 30 years with vigour
    # =====================================================
    func_name = 'run_site_specifc'

    retcode = 1
    exe_path = 'C:\\Freeware\\UnxUtils\\usr\\local\\wbin\\EcosseAgile.exe'
    exe_path = 'C:\\Freeware\\UnxUtils\\usr\\local\\wbin\\ecosse_mohamed_old.exe'

    sim_dir = form.w_lbl03.text()
    if not isdir(sim_dir):
        print('Path ' + sim_dir + ' does not exist')
        return

    # Set the working directory for the ECOSSE exe
    old_dir = getcwd()
    chdir(sim_dir)
    cmd = '1\n\n\n'

    nvigs = 30
    cmd = '1\n\n'
    for ivig in range(nvigs):
        cmd += '0.1\n'
    cmd += '\n'

    try:
        stdout_path = join(sim_dir, 'stdout.txt')
        new_inst = subprocess.Popen(
            exe_path,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=open(stdout_path, 'w'),
            stderr=subprocess.STDOUT,  # stdout=subprocess.PIPE
        )

        # Provide the user input to ECOSSE
        if new_inst.stdin is not None:
            new_inst.stdin.write(bytes(cmd,"ascii"))
            new_inst.stdin.close()
        else:
            print('Instance is None')
    except OSError as err:
        print(exe_path + ' could not be launched due to error: ' + err)
        retcode = 0  # non-fatal error
    else:
        print('started process with PID {}'.format(new_inst.pid))

    chdir(old_dir)
    return retcode


def write_xlsx_row(icol_start, irow, val_list, work_sheet):

    # func_name = __prog__ + ' write_xlsx_row'
    func_name = ' write_xlsx_row'

    for icol, val in zip(range(0,len(val_list)), val_list):
        write_xlsx_cell(icol + icol_start,irow,val,work_sheet)

    return

def write_xlsx_cell(icol, irow, sval, work_sheet):

    func_name = ' _write_cell'

    # convert integer column to Excel format using byte strings
    # =========================================================
    #                NB icol_limit = 26*26*26; val702 = 26*27; val26 = 26
    if icol > val702:
        print('column index {0} exceeds maximum {1} in function {2}'.format(icol,val702,func_name))
        return
    elif icol <= 0:
        print('column index {0} must exceed 0 in function {1}'.format(icol,func_name))
        return

    # column with up to two letters permitted
    # =======================================
    remain = icol % val26
    res = int(icol/val26)

    if remain == 0:
        remain = 26
        res -= 1

    if res == 0:
        col2val = ''
    else:
        col2val = bytes([res + 64]).decode()

    col3val = bytes([remain + 64]).decode()
    location = col2val + col3val + str(irow)    # typical location = 'A1'

    try:
        val = float(sval)
    except ValueError:
        if sval.isdigit():
            val = int(sval)
        else:
            val = sval

    work_sheet[location].value = val

    return

class Common_funcs(object,):

    def __init__(self,outputs_dir):

        self.outputs_dir = outputs_dir

    def open_csv_outf(self, outfname):

        # function returns a file object or -1 for failure
        outfile = join(self.outputs_dir, outfname)
        if exists(outfile):
            try:
                remove(outfile)
            except (OSError, IOError) as err:
                print('Failed to delete output file. {}'.format(err))
                return -1

        fout = open(outfile,'w')
        return fout

    def open_xls_outf(self, fname):

        # function returns a file object or -1 for failure
        # make sure we have xlsx extension
        root_name, extn = splitext(fname)
        outfname = root_name + '.xlsx'
        self.outfname = outfname

        # outfile = join(self.outputs_dir, outfname)
        if exists(outfname):
            try:
                remove(outfname)
            except (OSError, IOError) as err:
                print('Failed to delete output file. {}'.format(err))
                return -1

        wrkbk = Workbook()
        return wrkbk

