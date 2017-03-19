"""
The DSB3 Pipeline

This is the general-purpose command-line utility.
"""

import os, sys
import argparse
import logging
import getpass
from collections import OrderedDict
from importlib import import_module
from . import pipeline as pipe
from . import utils
sys.path.insert(0, '.')
user = getpass.getuser()
master_config = __import__('master_config_' + user.split('.')[0].split('_')[0]).config

steps = OrderedDict([
    ('step1', 'resample_lungs')
])

def main_descr():
    descr = 'choices for step:'
    for key, help in steps.items():
        descr += '\n  {:12}'.format(key) + help
    return descr

def main():
    os.environ['CUDA_VISIBLE_DEVICES'] = ','.join([str(i) for i in master_config['GPU_ids']])
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # disable tensorflow info and warning logs
    # --------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, epilog=main_descr())
    aa = parser.add_argument
    aa('step', type=str, help='One of the choices below, either in the form "stepX" or "step_name".')
    aa('-a, --action', choices=['run', 'eval', 'train'], default='run', help='Action to perform on step (default: run).')
    args = parser.parse_args()
    # --------------------------------------------------------------------------
    step_name = args.step
    # some checks
    if step_name not in steps and step_name not in set(steps.values):
        raise ValueError()
    if step_name in steps:
        step_name = steps[step_name]
    if step_name not in master_config:
        raise ValueError('Provide a parameter dict for step ' + step_name + ' in master_config_ ' + user + '!')
    if not os.path.exists('./dsb3/steps/' + step_name + '.py'):
        raise ValueError('Don\'t now any step called ' + step_name +'.')
    # init pipeline
    pipe.init(master_config)
    # init step
    pipe.init_step(step_name)
    # run step
    step = import_module('.steps.' + step_name, 'dsb3')
    try:
        step.run(**master_config[step_name])
    except TypeError as e:
        if 'run() got an unexpected keyword argument' in str(e):
            raise TypeError(str(e) + '\n Provide one of the valid parameters\n' + step.run.__doc__)
        else:
            raise e
    pipe.logger.info('finished step ' + step_name)