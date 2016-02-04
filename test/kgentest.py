#!/usr/bin/env python

import sys
import os
import inspect

# Python version check
if sys.hexversion < 0x020700F0:
    print 'ERROR: KGEN works with Python Version 2.7 or later.'
    sys.exit(-1)

SCRIPT_HOME, SCRIPT_NAME = os.path.split(os.path.realpath(__file__))
KGEN_HOME = '%s/..'%SCRIPT_HOME
sys.path.insert(0, '%s/base'%KGEN_HOME)
sys.path.insert(1, '%s/packages'%KGEN_HOME)
TEST_SCRIPT = 'runtest.py'
TEST_PREFIX = '_KGENTEST'

from doit.loader import generate_tasks
from doit.doit_cmd import DoitMain
from doit.cmd_base import TaskLoader
from kgen_test import KGenTest
from ordereddict import OrderedDict

class KGenTestTaskLoader(TaskLoader):
    """create test tasks on the fly based on cmd-line arguments"""
    DOIT_CONFIG = {
        'verbosity': 2,
        'pdb': True,
        'dep_file': os.path.join(SCRIPT_HOME, '.%s.db'%SCRIPT_NAME),
        'num_process': 1,
        }

        #'continue': True,

    def get_title(task):
        return "testing... %s" % task.name

    def __init__(self):
        import argparse

        self.testDB = OrderedDict()

        parser = argparse.ArgumentParser(description='Perform KGEN tests.')
        parser.add_argument('tests', type=str, nargs='*', help='Specify tests.')
        parser.add_argument('-f', dest='func_tests', action='store_true', default=False, help='Functional test only.')
        parser.add_argument('-s', dest='sys_tests', action='store_true', default=False, help='System test only.')
        parser.add_argument('-c', dest='changed', action='store_true', default=False, help='Changed test only.')
        parser.add_argument('-t', dest='leavetemp', action='store_true', default=False, help='Leave temporary directory.')
        parser.add_argument('--compiler', dest='compiler', type=str, default='ifort', help='Default compiler to be used for tests.')
        parser.add_argument('--compiler-flags', dest='compiler_flags', type=str, default='', help='Default compiler flgas to be used for tests.')

        # parse command line arguments
        args = parser.parse_args()


        # activate all test if no specific test is requested
        if not args.func_tests and not args.sys_tests:
            args.func_tests = True
            args.sys_tests = True

        # walk through test directory tree
        for dirName, subdirList, fileList in os.walk(SCRIPT_HOME):
            relpath = os.path.relpath(dirName, SCRIPT_HOME)
            if relpath.startswith('packages'): continue
            if relpath.startswith('old'):
                del subdirList[:]
                continue
            if relpath.endswith('templates'):
                del subdirList[:]
                continue

            # if kgen test script exists in a directory
            # the name of test script is fixed according to relative path to SCRIPT HOME
            path_script = '%s_test.py'%relpath.replace('/', '_')
            if path_script in fileList and dirName != SCRIPT_HOME:
                pathsave = sys.path[:]
                sys.path.insert(0, dirName)
                mod = __import__(path_script[:-3])

                test_found = False

                # find classes inherited from KGenTest class
                match = lambda x: inspect.isclass(x) and issubclass(x, KGenTest) and x is not KGenTest
                for name, cls in inspect.getmembers(mod, match):
                    test_found = True
                    break
                if not test_found: sys.path = pathsave


            # if TEST_SCRIPT exists in a directory
            if TEST_SCRIPT in fileList:
                pathsave = sys.path[:]
                sys.path.insert(0, dirName)
                mod = __import__(TEST_SCRIPT[:-3])

                test_found = False

                # find classes inherited from KGenTest class
                match = lambda x: inspect.isclass(x) and issubclass(x, KGenTest) and x is not KGenTest and len(x.__subclasses__())==0
                for name, cls in inspect.getmembers(mod, match):
                    # process module level preparation
                    print('Adding Test: %s' % relpath)

                    #  generate test object
                    obj = cls()
                    obj.KGEN_HOME = KGEN_HOME
                    obj.TEST_HOME = SCRIPT_HOME
                    obj.TEST_SCRIPT = TEST_SCRIPT
                    obj.TEST_DIR = dirName
                    obj.TEST_NUM += 1
                    obj.TEST_ID = '%s/%s'%(relpath, name)
                    obj.TEST_PREFIX = TEST_PREFIX
                    obj.COMPILER = args.compiler
                    obj.COMPILER_FLAGS = args.compiler_flags
                    obj.LEAVE_TEMP = args.leavetemp

                    # process class level preparation
                    obj.configure_test()

                    self.testDB[obj.TEST_ID] = obj

                sys.path = pathsave

    # def download build ref execution for homme, cesm, ....

    def testtask(self):

        task = {}
        task['name'] = 'testtask'
        task['uptodate'] = [False]
        task['actions'] = ['pwd']
        return task

    def report(self):
        ntests = len(self.testDB)
        npassed = len([ obj for obj in self.testDB.values() if obj.get_result('passed')])
        nfailed = ntests - npassed

        print ''
        print '*********** TEST REPORT ***********'
        print ''
        print 'Total # of tests : %d'%ntests
        print '# of passed tests: %d'%npassed
        print '# of failed tests: %d'%nfailed
        print ''

        for testname, testobj in self.testDB.iteritems():
            if testobj.get_result('passed'):
                pass
                #print '%s : PASSED'%testname
            else:
                print '%s : FAILED'%testname
                print 'ERROR MSG:', id(testobj.result['general']), id(testobj.result['general']['errmsg'])
                print testobj.get_result('errmsg')
                print ''
        
        print '***********************************'
#
#    def gentask_report(self, deptasks):
#
#        task = {}
#        task['name'] = 'generate_report'
#        task['task_dep'] = deptasks
#        task['actions'] = [(self.report, None, None)]
#        return task

    def _gen_tasks(self):
        # generate test tasks
        testnames = []
        for testname, testobj in self.testDB.iteritems():
            for subtask in testobj.get_tasks():
                testnames.append('%s:%s'%(TEST_PREFIX, subtask['name']))
                yield subtask
        #yield self.gentask_report(testnames)

    def load_tasks(self, cmd, params, args):
        """implements loader interface, return (tasks, config)"""
        return generate_tasks(TEST_PREFIX, self._gen_tasks()), self.DOIT_CONFIG

if __name__ == "__main__":
    kgentests = KGenTestTaskLoader()
    doit_main = DoitMain(kgentests)
    retval = doit_main.run(['run'])
    kgentests.report()
    sys.exit(retval)
