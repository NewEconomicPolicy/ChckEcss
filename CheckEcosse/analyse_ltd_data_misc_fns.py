#-------------------------------------------------------------------------------
# Name:        analyse_ltd_data_misc_fns.py
# Purpose:     examine files in reference directory and list shape
# Author:      Mike Martin
# Created:     07/03/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'analyse_ltd_data_misc_fns.py'
__version__ = '0.0.1'

# Version history
# ---------------
# 0.0.1  Wrote.
#
from glob import glob
from os.path import join, isfile
from numpy import arange, dtype, zeros, int64, float64
import filecmp
import common_funcs
from common_funcs import write_xlsx_cell, write_xlsx_row

wildCard = '/*.*'
no_data = -999.0
filter_files = list(['fort.6','fort.21','fort.57','INPUTS.OUT','ERROR.MSG','NOERROR.MSG','PARLIS.DAT'])

def check_weather(ref_dir, nl_strt, nyears, lines):

    prev_fname = ''
    nl_end = nl_strt + nyears
    for rec in lines[nl_strt:nl_end]:
        fname = rec.split()[0]
        fname = fname.strip("'") # get rid of unnecessary quotes
        met_file = join(ref_dir, fname)
        if isfile(met_file):
            mess = 'Met file ' + met_file + ' exists'
        else:
            mess ='*** Warning *** met file ' + met_file + ' does not exist'

        if prev_fname != fname:
                print(mess)

        prev_fname = fname

    return nl_end

def check_block(block_name, nl_strt, lines, val_types):

    n_lines = len(val_types)
    vals = []
    nbad_lines = 0
    nl_end = nl_strt + n_lines
    if nl_end > len(lines):
        print('No lines for block: {}\tat line {}\t# lines in file: {}'.format(block_name, nl_end, len(lines)))
        return -1, vals

    lines_block = lines[nl_strt:nl_end]

    for indx, rec in enumerate(lines_block):
        sval = rec[:10]
        try:
            if val_types[indx] == 'I':
                val = int(sval)
            else:
                val = float(sval)
            vals.append(val)
        except ValueError as err:
            print('Error at line {}: {}'.format(nl_strt + indx + 1, err))
            nbad_lines += 1

    if nbad_lines == 0:
        if block_name.startswith('Number of '):
            print(block_name + ': {}'.format(vals[0]))
        else:
            print('\tblock: ' + block_name + ' - OK')
        return nl_end, vals
    else:
        print('Block: ' + block_name + ' failed with {} errors'.format(nbad_lines))
        return -1, vals

def check_limited_data_compliance(form):

    ref_dir = form.w_lbl03.text()
    print('\nWill check files in ' + ref_dir)

    # read fnames file and clean
    # ==========================
    inp_fname = join(ref_dir, 'input.txt')
    if not isfile(inp_fname):
        print('Limited data mode input file ' + inp_fname + ' does not exist')
        return
    with open(inp_fname, 'r') as fobj:
        lines = fobj.readlines()

    # first 16 lines:
    # ===============
    val_types = ['F'] + ['I']
    line_indx = 0
    block_name = 'first 2 lines: mode of equilibrium run and number of soil layers (max 10)'
    line_indx, vals = check_block(block_name, line_indx, lines, val_types)
    if line_indx == -1:
        return

    # soil for each layer and landuse
    # ===============================
    mode_of_equilib, nlayers = vals
    val_types = ['F']*nlayers
    block_name = 'depths to bottom of SOM layers'.format(nlayers)
    line_indx, vals = check_block(block_name, line_indx, lines, val_types)
    if line_indx == -1:
        return

    # read blocks of 6 metrics comprising carbon content, bulk density [g/cm3], pH, % clay,  % silt, % sand
    # =====================================================================================================
    nmetrics = 6
    val_types = ['F']*nmetrics
    n_land_uses = 6
    for lu in range(n_land_uses):
        for ilyr in range(nlayers):
            block_name = 'soil definition for layer: {}\tlanduse: {}'.format(ilyr + 1,lu + 1)
            line_indx, vals = check_block(block_name, line_indx, lines, val_types)
            if line_indx == -1:
                return

    print('skipped {} obsolete lines'.format(n_land_uses))
    line_indx += n_land_uses

    val_types = ['F']*24
    block_name = 'Long term average monthly precipitation [mm] and temperature [degC]'
    line_indx, vals = check_block(block_name, line_indx, lines, val_types)
    if line_indx == -1:
        return

    # ======= determine whether V6.3 or later =====================
    mx_stnd_flag = False
    for line in lines[line_indx:line_indx + 4]:
        if line.lower().find('max standing') >= 0:
            mx_stnd_flag = True
            break

    if mx_stnd_flag:
        val_types = ['F']*3 + ['I']
        block_name = 'Latitude, water table depth, max standing, Drainage class'
        line_indx, vals = check_block(block_name, line_indx, lines, val_types)
        if line_indx == -1:
            return
    else:
        val_types = ['F'] * 2 + ['I']
        block_name = 'Latitude, water table depth, Drainage class'
        line_indx, vals = check_block(block_name, line_indx, lines, val_types)
        if line_indx == -1:
            return
    # ===============================
    nskip = 4
    print('skipped {} obsolete lines'.format(nskip))
    line_indx += nskip

    val_types = ['I']
    block_name = 'Number of growing seasons'
    line_indx, vals = check_block(block_name, line_indx, lines, val_types)
    if line_indx == -1:
        return

    ngrow_seasons = vals[0]
    print('skipped {} growing seasons'.format(ngrow_seasons))
    line_indx += ngrow_seasons

    # check weather files
    #  ==================
    line_indx = check_weather(ref_dir, line_indx, ngrow_seasons, lines)
    if line_indx == -1:
        return

    print('Finished checking files in ' + ref_dir)

    return
