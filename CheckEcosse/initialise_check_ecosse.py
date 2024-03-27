# -------------------------------------------------------------------------------
# Name:        initialise_check_ecosse.py
# Purpose:     script to read setup and configuration files and write user selections back to the configuration file
# Author:      Mike Martin
# Created:     31/03/2020
# Licence:     <your licence>
# -------------------------------------------------------------------------------

__prog__ = 'initialise_check_ecosse.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import normpath, join, exists, lexists, split
from os import getcwd, makedirs, name as name_os

from analyse_ecosse_output import format_out_files
import json
from time import sleep

ERROR_STR = '*** Error *** '
sleepTime = 5

def initiation(form):
    """
    this function is called to initiate the programme to process non-GUI settings
    """
    # retrieve settings
    # =================
    chk_ecsse_str = 'check_ecosse'
    form.settings = _read_setup_file(chk_ecsse_str)
    form.settings['config_file'] = normpath(form.settings['config_dir'] + '/' + chk_ecsse_str + '_config.json')
    read_config_file(form, check_attribs_only=True)

    return

def _read_setup_file(chk_ecsse_str):
    """
    read settings used for programme from the setup file, if it exists,
    or create setup file using default values if file does not exist
    """
    func_name = __prog__ + ' _read_setup_file'

    # validate setup file
    # ===================
    fname_setup = chk_ecsse_str + '_setup.json'

    setup_file = join(getcwd(), fname_setup)
    if exists(setup_file):
        try:
            with open(setup_file, 'r') as fsetup:
                setup = json.load(fsetup)

        except (OSError, IOError) as err:
            sleep(sleepTime)
            exit(0)
    else:
        setup = _write_default_setup_file(setup_file)
        print('Read default setup file ' + setup_file)

    # initialise vars
    # ===============
    settings = setup['setup']
    settings_list = ['config_dir', 'fname_png']
    for key in settings_list:
        if key not in settings:
            print(ERROR_STR + 'setting {} is required in setup file {} '.format(key, setup_file))
            sleep(sleepTime)
            exit(0)
    settings['chk_ecsse_str'] = chk_ecsse_str

    # make sure directories exist for configuration file
    # ==================================================
    config_dir = settings['config_dir']
    if not lexists(config_dir):
        makedirs(config_dir)

    # report settings
    # ===============
    print('Resource locations:')
    print('\tconfiguration file: ' + config_dir)
    print('')

    return settings

def _write_default_setup_file(setup_file):
    """
    stanza if setup_file needs to be created
    """
    root_dir, dummy = split(getcwd())
    _default_setup = {
        'setup': {
            'config_dir': join(root_dir, 'config'),
            'fname_png': join(root_dir, 'Images', 'Tree_of_life.PNG')
        }
    }
    # create setup file
    # =================
    with open(setup_file, 'w') as fsetup:
        json.dump(_default_setup, fsetup, indent=2, sort_keys=True)

    return _default_setup

def read_config_file(form, check_attribs_only=False):
    """
    check config file exists and create default if not
    then validate attributes
    if read flag set then read attribute-value pairs from the prechecked config file
    """
    # read settings from the config file if it exists and create default if not
    # =========================================================================
    config_file = form.settings['config_file']
    if exists(config_file):
        try:
            with open(config_file, 'r') as fconfig:
                config = json.load(fconfig)
        except (OSError, IOError) as err:
            print(err)
            return False
    else:
        # stanza if config_file needs to be created
        # =========================================
        out_res_dir = ''
        ref_dir = ''  # directory containing reference outputs
        targ_dir = ''  # target directory of output files to be compared
        rslts_dir = ''  # results are put here
        _default_config = {
            'Directories': {
                'ref_dir': ref_dir,
                'ref_id': 'ref',
                'rslts_dir': rslts_dir,
                'summary_only': False,
                'targ1_dir': targ_dir,
                'targ1_id': 'targ1',
                'targ2_dir': targ_dir,
                'targ2_id': 'targ2',
                'use_targ2': False,
                'water_dep': '50.0'
            }
        }
        # if config file does not exist then create it...
        with open(config_file, 'w') as fconfig:
            json.dump(_default_config, fconfig, indent=2, sort_keys=True)
            config = _default_config

    # validate setup file
    # ===================
    grp = 'Directories'
    config_list = ['ref_dir', 'ref_id', 'targ1_dir', 'targ1_id', 'targ2_dir', 'targ2_id', 'use_targ2',
                   'summary_only', 'rslts_dir', 'water_dep']
    for key in config_list:
        if key not in config[grp]:
            print(ERROR_STR + 'attribute {} is required in config file {}'.format(key, config_file))
            sleep(sleepTime)
            exit(0)

    if check_attribs_only:
        return

    # post values
    # ===========
    ref_dir = normpath(config[grp]['ref_dir'])
    form.w_lbl03.setText(ref_dir)
    form.w_ref_id.setText(config[grp]['ref_id'])

    form.w_smmry_only.setChecked(config[grp]['summary_only'])
    form.w_targ2_also.setChecked(config[grp]['use_targ2'])

    targ1_dir = normpath(config[grp]['targ1_dir'])
    form.w_lbl04.setText(targ1_dir)
    form.w_targ1_id.setText(config[grp]['targ1_id'])

    targ2_dir = normpath(config[grp]['targ2_dir'])
    form.w_lbl06.setText(targ2_dir)
    form.w_targ2_id.setText(config[grp]['targ2_id'])

    rslts_dir = normpath(config[grp]['rslts_dir'])
    form.w_lbl13.setText(rslts_dir)
    if not exists(rslts_dir):
        print('Results directory ' + rslts_dir + ' does not exist')

    form.w_water_dep.setText(str(config[grp]['water_dep']))
    form.w_lbl05.setText(format_out_files(form))
    form.w_lbl07.setText(format_out_files(form, target_flag='targ2'))

    return

def write_config_file(form):
    """
    C
    """
    config_file = form.settings['config_file']

    grp = 'Directories'
    config = {
        'Directories': {
            'ref_dir': form.w_lbl03.text(),
            'ref_id': form.w_ref_id.text(),
            'rslts_dir': form.w_lbl13.text(),
            'summary_only': form.w_smmry_only.isChecked(),
            'use_targ2': form.w_targ2_also.isChecked(),
            'targ1_dir': form.w_lbl04.text(),
            'targ1_id': form.w_targ1_id.text(),
            'targ2_dir': form.w_lbl06.text(),
            'targ2_id': form.w_targ2_id.text(),
            'water_dep': form.w_water_dep.text()
        }
    }
    with open(config_file, 'w') as fconfig:
        json.dump(config, fconfig, indent=2, sort_keys=True)

    return
