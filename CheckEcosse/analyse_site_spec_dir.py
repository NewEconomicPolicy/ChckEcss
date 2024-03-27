#-------------------------------------------------------------------------------
# Name:        analyse_site_spec_dir.py
# Purpose:     examine files in reference directory and list shape
# Author:      Mike Martin
# Created:     07/03/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'analyse_site_spec_dir.py'
__version__ = '0.0.1'

# Version history
# ---------------
# 0.0.1  Wrote.
#
from glob import glob
from os.path import join, split, isfile, splitext, basename
from numpy import arange, dtype, zeros, int64, float64
import filecmp
import common_funcs
from analyse_ltd_data_misc_fns import check_weather, check_block, check_limited_data_compliance
from common_funcs import write_xlsx_cell, write_xlsx_row

wildCard = '/*.*'
no_data = -999.0
filter_files = list(['fort.6','fort.21','fort.57','INPUTS.OUT','ERROR.MSG','NOERROR.MSG','PARLIS.DAT'])

def _check_management_file(inp_fname):
    '''
    step through each line where the first line is zeroth index in line list
    '''

    fobj = open(inp_fname, 'r')
    lines = fobj.readlines()
    fobj.close()

    ref_dir, dummy = split(inp_fname)

    '''
    first 16 lines:
    ===============
            NSOILJ, IDRAINJ, IROCKJ, LCROP, PREYLD, ATM, IDATEFC, TIMESTEP, MODTYPE,
     &                   NYEARS, ISTHARV, ISTYR, ILAST_TS, FIXEND,LAT,WTABLE
30    FORMAT(4(I10/),2(F10.0/),8(I10/),(F10.0/),F10.0)
    '''
    val_types = ['I']*4 + ['F']*2 +['I']*8 +['F']*2
    line_indx = 0
    block_name = 'first 16 lines'
    line_indx, vals = check_block(block_name, line_indx, lines, val_types)
    if line_indx == -1:
        return

    # check weather files and read number of crops
    # ===================
    nyears = vals[9]
    line_indx = check_weather(ref_dir, line_indx, nyears, lines)
    if line_indx == -1:
        return

    block_name = 'Number of crops'
    #             ===============
    val_types = ['I']
    line_indx, vals = check_block(block_name, line_indx, lines, val_types)
    if line_indx == -1:
        return

    # for each crop, read 8 lines
    # ===========================
    ncrops = vals[0]
    val_types = {}
    val_types['crop'] = ['I']*2 + ['F'] + ['I'] + ['F'] + ['I']*3  # 8 lines
    val_types['fertiliser'] = ['F'] + ['I'] + ['F']*3 + ['I']*2    # 7 lines
    val_types['manure'] = ['F'] + ['I']*3  # 4 lines

    for ncrop in range(1,ncrops + 1):
        block_name = 'crop {}'.format(ncrop)
        line_indx, crop_vals = check_block(block_name, line_indx, lines, val_types['crop'])
        if line_indx == -1:
            break

        nfert_apps = crop_vals[6]
        for nfert in range(nfert_apps):
            block_name = 'crop {}\tfertiliser {}'.format(ncrop, nfert + 1)
            line_indx, vals = check_block(block_name, line_indx, lines, val_types['fertiliser'])
            if line_indx == -1:
                break

        norgm_apps = crop_vals[7]
        for norgm in range(norgm_apps):
            block_name = 'crop {}\tmanure {}'.format(ncrop, norgm + 1)
            line_indx, vals = check_block(block_name, line_indx, lines, val_types['manure'])
            if line_indx == -1:
                break

    # nested loop
    # ===========
    if line_indx == -1:
        return

    block_name = 'Number of cultivations'
    #             ======================
    val_types = ['I']
    line_indx, vals = check_block(block_name, line_indx, lines, val_types)
    if line_indx == -1:
        return

    ncults = vals[0]
    val_types = ['I']*2 + ['F']     # 3 lines
    for ncult in range(1, ncults + 1):
        block_name = 'cultivation {}'.format(ncult)
        line_indx, vals = check_block(block_name, line_indx, lines, val_types)
        if line_indx == -1:
            break

    return

def check_input_file_compliance(form):

    ref_dir = form.w_lbl03.text()
    print('\nWill check files in ' + ref_dir)

    # read fnames file and clean
    # ==========================
    inp_fname = join(ref_dir, 'fnames.dat')
    if not isfile(inp_fname):
        print('File ' + inp_fname + ' does not exist - will check for limited data mode compliance')
        check_limited_data_compliance(form)
        return
    with open(inp_fname, 'r') as fobj:
        first_line = fobj.readline()

    # clean line
    # ==========
    frst_line = first_line.strip('\n').replace("'","")

    # try splitting on comma, then space
    # ==================================
    file_list = frst_line.split(',')
    if len(file_list) < 3:
        file_list = frst_line.split()
        if len(file_list) < 3:
            print('Could not find 3 files from first line of file ' + inp_fname + ' line: ' + first_line)
            return

    # check each file
    # ===============
    for fname in file_list:
        short_fname = fname.strip('"')

        inp_fname = join(ref_dir, short_fname)
        if isfile(inp_fname):
            root_name, exten = splitext(short_fname)
            if root_name.lower() == 'management':
                print('Checking ' + short_fname)
                _check_management_file(inp_fname)
        else:
            print('File ' + inp_fname + ' does not exist')

    print('Finished checking files in ' + ref_dir)

    return

def check_identical_files(form, file_types = 'input' ):

    # gather directories from the GUI
    # ===============================
    ref_dir = form.w_lbl03.text()
    targ_dir = form.w_lbl04.text()
    ref_flist = glob(ref_dir + wildCard)
    print()

    # step through each file from the reference directory
    # ===================================================
    for ref_file in ref_flist:
        root_name, extn = splitext(ref_file)
        extn = extn.upper()
        if (extn == '.OUT' or extn == '.XLSX') and file_types == 'input':
            continue

        # check against equivalent in the target dir
        # ==========================================
        dummy, fname_short = split(ref_file)
        if fname_short in filter_files:
            continue

        if (extn == '.TXT' or extn == '.DAT') and file_types == 'output':
            continue

        targ_file = join(targ_dir, fname_short)
        if isfile(targ_file):
            if filecmp.cmp(ref_file, targ_file):
                print('Identical file: ' + fname_short)
            else:
                print('*** Different file: ' + fname_short)
        else:
            print('Non-existent file: ' + targ_file)

    return

class Analysis(object,):
    def __init__(self,form):
        self.numInts = 0
        self.numFlts = 0
        self.lrgstFltCoord = list([0,0])
        self.badVals = 0
        self.NaNs = 0
        self.asterisks = 0
        self.fname_short = ''

    #  entry point from GUI when user requests check files
    #       invokes:
    #        def compare_files
    #        def write_sum_file
    #        def get_num_words
    #
    def check_these_files(self, form):

        func_name =  __prog__ + ' check_ecosse_files'

        ref_dir = form.w_lbl03.text()
        rslts_dir = form.w_lbl13.text()

        summary_fname = basename(ref_dir) + '.sum'
        sum_fname = join(rslts_dir,  summary_fname)

        outdir_sum = common_funcs.Common_funcs(rslts_dir)

        wrkbk = outdir_sum.open_xls_outf(sum_fname)
        out_fname = outdir_sum.outfname

        # write to Excel file
        if wrkbk == -1:
            print('Error - could not open file {} in directory {}'.format(out_fname, rslts_dir))
            return

        # grab the active worksheet
        wrksht_short  = wrkbk.active
        wrksht_short.title = "Summary"

        # Header line
        header_line = list(['File name', 'NumLines', 'NumWords', 'MaxRowLen', 'IntTotal', 'FltsCnvrtd', 'NaNs',
                                                                                        'Asterisks', 'Bad values'])
        write_xlsx_row(1, 1, header_line, wrksht_short)
        row_short = 2

        # send abbreviated fields to screen
        # =================================
        header_str = ''
        for fld in header_line[:4]:
            header_str +=  '\t' + fld

        print(header_str)

        # generate list of reference files
        # ================================
        ref_flist = glob(ref_dir + wildCard)

        # step through files in reference list
        nwords = zeros(2, dtype=int64)
        nlines = zeros(2, dtype=int64)
        max_len_row = zeros(2, dtype=int64)
        num_exams = 0

        for ref_file in ref_flist:
            fpath, fname_short = split(ref_file)
            if fname_short in filter_files:
                continue
            self.fname_short = fname_short

            # compare files and remove entries from target list
            num_exams += 1
            line_str = fname_short
            nlines[0], max_len_row[0], nwords[0] = self.get_num_words(ref_file)
            if nlines[0] == -1:
                continue
            result = line_str + '\t{}\t{}\t{}'.format(nlines[0], nwords[0], max_len_row[0])
            write_xlsx_row(1, row_short, result.split('\t'), wrksht_short)
            row_short += 1
            print('\t' + result)

        print('Completed after {} file examined\nResults written to: {}\n'.format(num_exams, out_fname))
        wrkbk.save(out_fname)

        return 'dummy'

    def get_num_words(self, fname):

        max_len_row = 0

        try:
            feed = open(fname, 'r').read()
            feed_lines = feed.splitlines()
        except UnicodeDecodeError as err:
            print('File ' + fname + ' will be rejected due to UnicodeDecodeError')
            return list([-1, -1, -1])

        num_lines = len(feed_lines)
        num_words = 0

        for line in feed_lines:
            len_row = len(line.split())
            num_words += len_row
            if len_row > max_len_row:
                max_len_row = len_row

        return list([num_lines, max_len_row, num_words])
