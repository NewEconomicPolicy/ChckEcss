#-------------------------------------------------------------------------------
# Name:        analyse_ecosse_output.py
# Purpose:     examine two directories each with Ecosse output files and compare differences
# Author:      Mike Martin
# Created:     07/03/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'analyse_ecosse_output.py'
__version__ = '0.0.1'

# Version history
# ---------------
# 0.0.1  Wrote.
#
from glob import glob
from os.path import basename, join, split, isfile, splitext
import filecmp
from numpy import zeros, int64, float64
import common_funcs
from common_funcs import write_xlsx_row

wildCard = '/*.OUT'
no_data = -999.0
filter_files = list(['fort.6','fort.21','fort.57','INPUTS.OUT','ERROR.MSG','NOERROR.MSG','PARLIS.DAT'])

def format_out_files(form, target_flag = 'targ1', label_string_flag = True):
    """
    invoked by GUI for user feedback
    """
    ref_dir = form.w_lbl03.text()
    ref_flist = glob(ref_dir + wildCard)
    if target_flag == 'targ1':
        targ_flist = glob(form.w_lbl04.text() + wildCard)
    else:
        targ_flist = glob(form.w_lbl06.text() + wildCard)

    nref_files = len(ref_flist)
    ntarg_files = len(targ_flist)
    if label_string_flag:
        label_string = 'Number of reference files = {}, target files: {}'.format(nref_files, ntarg_files)
        return label_string
    else:
        return min(nref_files, ntarg_files)

class Analysis(object,):
    """
    methods:
          check_ecosse_files(self,form): entry
    """
    def __init__(self,form):
        """
        C
        """
        self.numInts = 0
        self.sameInts = 0
        self.diffInts = 0
        self.numFlts = 0
        self.eqlFlts = 0
        self.nteqlFlts = 0
        self.lrgstFltDiff = 0.0
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
    def check_ecosse_files(self,form):

        func_name =  __prog__ + ' check_ecosse_files'

        ref_dir = form.w_lbl03.text()
        targ_dir = form.w_lbl04.text()
        rslts_dir = form.w_lbl13.text()

        summary_fname = basename(ref_dir) + '_vs_' + basename(targ_dir) + '.sum'
        sum_fname = join(rslts_dir,  summary_fname)

        outdir_sum = common_funcs.Common_funcs(rslts_dir)
        summary_only_flag = form.w_smmry_only.isChecked()

        wrkbk = outdir_sum.open_xls_outf(sum_fname)
        out_fname = outdir_sum.outfname

        # write to Excel file
        if wrkbk == -1:
            print('Error - could not open file {} in directory {}'.format(out_fname, rslts_dir))
            return

        # grab the active worksheet
        wrksht_sum = wrkbk.active
        wrksht_sum.title = "Long Summary"

        wrksht_short = wrkbk.create_sheet()
        wrksht_short.title = "Short Summary"

        # Header line
        title1 = 'File name,Same?,RefNumLines,RefNumWords,MaxRowLen,TargNumLines,TargNumWords,IntTotal,IntSame,IntDiff,'
        title2 = 'FltsCnvrtd,Equal,Not equal,LargestDiff,LrgstDiffCoords,NaNs,Asterisks,Bad values'
        header_line = title1 + title2
        write_xlsx_row(1, 1, header_line.split(','), wrksht_short)
        row_short = 2

        # generate list of reference files
        # ================================

        ref_flist = glob(ref_dir + wildCard)

        # create two target directory lists
        targ_flist = []
        for targ_file in glob(targ_dir + wildCard):
             fpath, fname = split(targ_file)
             targ_flist.append(fname)

        if len(targ_flist) < 1:
             print ('ERROR: ' + targ_dir + ' has no OUT files.')
             return

        # step through files in reference list
        nwords = zeros(2, dtype=int64)
        nlines = zeros(2, dtype=int64)
        max_len_row = zeros(2, dtype=int64)
        num_comps = 0
        row_sum = 1
        for ref_file in ref_flist:
            fpath, fname_short = split(ref_file)
            # print('Processing {0}'.format(fname_short))
            if fname_short in filter_files:
                continue

            self.fname_short = fname_short

            if summary_only_flag:
                if fname_short != 'SUMMARY.OUT':
                    continue
            try:
                lndx = targ_flist.index(fname_short)
            except ValueError as err:
                print('Function: {}\tFile: {}\t{}'.format(func_name,fname_short,str(err)))
                continue
            targ_file = join(targ_dir,targ_flist[lndx])
            if not isfile(targ_file):
                print('Target file {} does not exist'.format(targ_file))
                continue

            # compare files and remove entries from target list
            num_comps += 1
            line_str = fname_short
            if filecmp.cmp(ref_file, targ_file):
                nlines[0], max_len_row[0], nwords[0] = self.get_num_words(ref_file)
                result = 'Identical'
                identical_line = line_str + ',' + result + ',{0},{1},{2}'.format(nlines[0],nwords[0], max_len_row[0])
                write_xlsx_row(1, row_short, identical_line.split(','), wrksht_short)
                row_short += 1
            else:
                # Differences detected
                # ====================

                # check number of words are same

                for i, fname, label in zip(range(0,2), list([targ_file,ref_file]), list(['target', 'reference'])):
                    nlines[i], max_len_row[i], nwords[i] = self.get_num_words(fname)

                # compare each entity if there is a files equivalence
                # if nwords[0] == nwords[1] and nlines[0] == nlines[1]: - too strict
                if nlines[0] == nlines[1]:
                    line_str = line_str + ',Different,{0},{1},{2},,,'.format(nlines[0], nwords[0], max_len_row[0])
                    self.diff = zeros(max_len_row[0]*nlines[0], dtype=float64)
                    self.diff.shape = (max_len_row[0], nlines[0])
                    ret_list = self.compare_files(wrksht_short, row_short, targ_file, ref_file, line_str)
                    row_short = ret_list[0]
                    title_lines = ret_list[1:]
                    # add lines to summary file and write Excel file of differences
                    result = 'Different but same shape'
                    row_sum = self.write_sum_file(title_lines, out_fname, wrkbk, wrksht_sum, row_sum)
                else:
                    different_line = line_str + ',Different,{0},{1},{2},{3},{4},{5}'\
                        .format(nlines[0], nwords[0], max_len_row[0], nlines[1], nwords[1], max_len_row[1])
                    write_xlsx_row(1, row_short, different_line.split(','), wrksht_short)
                    result = 'Different with different shape'
                    row_short += 1
            print('Processed {}\tresult: {}'.format(fname_short,result))
        print('Completed after {} comparisons'.format(num_comps))
        wrkbk.save(out_fname)
        print('Result written to file: {}\n'.format(out_fname))

        return 'dummy'

    def write_sum_file(self, title_lines, out_fname, wrkbk, wrksht_sum, row_sum):
        """
        add lines to summary file and write Excel file of differences between .OUT files
        """

        # create appropriately named worksheet
        fname = self.fname_short
        root_name, dummy = splitext(fname)
        max_len_row, nlines = self.diff.shape
        wrksht = wrkbk.create_sheet()
        wrksht.title = root_name

        # set up storage with sufficient number of elements
        max_vals = zeros(max_len_row, dtype=float64)

        # write header- expect up to two lines
        if len(title_lines) > 1:
            wrksht['A1'] = title_lines[0]
            nextrow = 2
        else:
            nextrow = 1

        # writerow_out(title_lines[-1].split())
        write_xlsx_row(1, nextrow, title_lines[-1].split(), wrksht)
        nextrow += 1

        # write to summary sheet
        write_xlsx_row(1, row_sum, ['']+ title_lines[-1].split(), wrksht_sum)
        row_sum += 1

        for iline in range(0,nlines):
            # writerow_out(self.diff[:,iline])
            write_xlsx_row(1, nextrow, self.diff[:,iline], wrksht)
            nextrow += 1

            # check each value to determine max_value for that column
            for icol in range(0,max_len_row):
                z = self.diff[icol,iline]
                if z > max_vals[icol]:
                    max_vals[icol] = z

        # write results to summary file - make sure blank row
        write_xlsx_row(1, row_sum, list([fname]) + list(max_vals), wrksht_sum)
        row_sum += 2

        # Save after each worksheet has been written
        wrkbk.save(out_fname)

        return row_sum

    # invokes def process_two_atoms
    def compare_files(self, wrksht_short, row_short, targ_file, ref_file, line_str):
        """
        C
        """

        # assumption is that both files have the same number of lines and words
        fname_short = self.fname_short
        twoLineList = list(['BIOC.OUT','BION.OUT','CROPN.OUT','CO2.OUT','DENITN.OUT','DPMC.OUT','DPMN.OUT',
                            'EVAP_SUNDIAL.OUT',
                'HUMC.OUT','HUMN.OUT','LEACHN.OUT',	'MINERN.OUT','NH4N.OUT','NITRIFN.OUT','NO3N.OUT','RPMC.OUT',
                            'RPMN.OUT','SOILN.OUT','SUMMARY.OUT','TOTC.OUT','TOTN.OUT'])
        # this is rather crude...
        feed_targ = open(targ_file, 'r').read()
        feed_targ_lines = feed_targ.splitlines()

        feed_ref = open(ref_file, 'r').read()
        feed_ref_lines = feed_ref.splitlines()

        num_words = 0

        nline = 0
        self.numInts = 0
        self.sameInts = 0
        self.diffInts = 0
        self.numFlts = 0
        self.eqlFlts = 0
        self.nteqlFlts = 0
        self.lrgstFltDiff = 0.0
        self.lrgstFltCoord = list([0,0])
        self.badVals = 0
        self.NaNs = 0
        self.asterisks = 0

        title_lines = []
        num_line_diffs = 0
        max_num_line_diffs = 10

        # step through each line
        for line_targ, line_ref in zip(feed_targ_lines,feed_ref_lines):

            # always skip header - some have two lines
            if nline == 0:
                title_lines.append(line_ref)
                nline += 1
                continue

            # some filesw have two header lines
            if nline == 1:
                try:
                    twoLineList.index(fname_short)
                    title_lines.append(line_ref)
                    nline += 1
                    continue
                except ValueError:
                    pass

            # some TOTC.OUT has 3 lines of headers and a random line 5
            if fname_short == 'TOTC.OUT':
                if nline == 2 or nline == 4:
                    nline += 1
                    continue

            line_atoms_ref = line_ref.split()
            line_atoms_targ = line_targ.split()
            nlen_ref = len(line_atoms_ref)
            nlen_targ = len(line_atoms_targ)
            if nlen_ref != nlen_targ:
                print('Number of words {0} (ref) and {1} (targ) differ on line {2} of file {3} - will skip'
                         .format(nlen_ref, nlen_targ, nline, fname_short))
                num_line_diffs += 1
                if num_line_diffs >= max_num_line_diffs:
                    break
                else:
                    continue
            else:
                # work through each atom
                for icol, atom_targ, atom_ref in zip(range(0,nlen_ref), line_atoms_targ, line_atoms_ref):
                    retcode = self.process_two_atoms(nline, icol, atom_ref, atom_targ, line_targ, line_ref)
                    # abandon processing of line if bad data
                    if retcode == -1:
                        break

            num_words += len(line_ref.split())
            nline += 1

        if num_line_diffs >= max_num_line_diffs:
            print(line_str + ' discontinued comparison due to too many line differences')
        else:
            coord = '{0} {1}'.format(self.lrgstFltCoord[0],self.lrgstFltCoord[1])
            line_str = line_str + '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}'\
                .format(self.numInts, self.sameInts, self.diffInts,\
                    self.numFlts, self.eqlFlts, self.nteqlFlts, self.lrgstFltDiff, coord,\
                        self.NaNs, self.asterisks, self.badVals)
            write_xlsx_row(1, row_short, line_str.split(','), wrksht_short)
            row_short += 1

        return [row_short] + title_lines

    def process_two_atoms (self, nline, icol, atom_ref, atom_targ, line_targ, line_ref):
        """
        C
        """
        func_name =  ' process_two_atoms'
        # =========================================

        # check that each are valid
        if atom_targ == 'NaN' or atom_ref == 'NaN':
            # self.diff[icol,nline] = float('nan')
            self.diff[icol,nline] = no_data
            self.NaNs += 1
            return 0

        if atom_targ.find('****') != -1 or atom_ref.find('****') != -1:
            # self.diff[icol,nline] = float('nan')
            self.diff[icol,nline] = no_data
            self.asterisks += 1
            return 0

        # ignore integer values
        intFlag = False
        try:
            valRef = int(atom_ref)
            try:
                valTarg = int(atom_targ)
                intFlag = True  # both values are integer
                self.numInts += 1
                if valTarg == valRef:
                    self.sameInts += 1
                else:
                    self.diffInts +=1

            except ValueError:
                pass
        except ValueError:
            pass

        if intFlag:
            return 0

        # process float values
        fltFlag = False
        try:
            valRef = float(atom_ref)
            try:
                valTarg = float(atom_targ)
                fltFlag = True
                self.numFlts += 1
            except ValueError:
                typeVal = 'reference'
                pass

        except ValueError:
            typeVal = 'target'
            pass

        if fltFlag:
            if atom_ref == atom_targ:
                diffVal = 0.0
                self.eqlFlts += 1
            else:
                denom = valRef + valTarg
                if denom == 0.0:
                    diffVal = 0.0
                else:
                    diffVal = abs((valRef - valTarg)/denom)
                    if diffVal > self.lrgstFltDiff:
                        self.lrgstFltDiff = diffVal
                        self.lrgstFltCoord = list([nline + 1, icol + 1])
                self.nteqlFlts += 1
        else:

            str1 = 'Warning in function: <{0}>\tfile name: {1}\tValueError on line {2} column {3} converting {4} value.'\
                                    .format(func_name, self.fname_short, nline + 1, icol + 1, typeVal)
            if line_ref == line_targ:
                print(str1 + '\tReference and target lines are identical - will skip:\n\t{0}'.format(line_ref))
            else:
                print(str1 + '\tValues, reference/target: {0}/{1} - will skip'.format(atom_ref, atom_targ))
            return -1

        try:
            self.diff[icol,nline] = diffVal
        except IndexError:
            print('IndexError in {0}: icol: {1}, nline: {2}, shape: {3}'
                  .format(func_name,icol,nline,self.diff.shape))
        except ValueError:
            print('ValueError in {0}: icol: {1}, nline: {2}, diffVal: {3}'
                  .format(func_name,icol,nline,diffVal))

        return 0

    def get_num_words(self, fname):
        """
        C
        """
        max_len_row = 0

        feed = open(fname, 'r').read()
        feed_lines = feed.splitlines()

        num_lines = len(feed_lines)
        num_words = 0

        for line in feed_lines:
            len_row = len(line.split())
            num_words += len_row
            if len_row > max_len_row:
                max_len_row = len_row

        return list([num_lines, max_len_row, num_words])
