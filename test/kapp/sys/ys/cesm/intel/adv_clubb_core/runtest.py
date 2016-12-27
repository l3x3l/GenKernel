import os
import sys
import glob
import shutil
from kapp_sys_ys_cesm_intel_test import KAppSysYSCesmIntelTest


class Test(KAppSysYSCesmIntelTest):

    def generate(self, myname, result):

        workdir = result['mkdir_task']['workdir']
        tmpsrc = result['download_task']['tmpsrc']
        srcmods = result['config_task']['srcmods']
        casedir = result['config_task']['casedir']
        casename = result['config_task']['casename']

        camsrcmods = '%s/src.cam'%srcmods
        result[myname]['camsrcmods'] = camsrcmods

        srcfile = '%s/components/cam/src/physics/cam/clubb_intr.F90'%tmpsrc
        namepath = 'clubb_intr:clubb_tend_cam:advance_clubb_core_api'

        prerun_krun = 'export LD_LIBRARY_PATH=/ncar/opt/intel/psxe-2016_update1/compilers_and_libraries_2016.1.150/linux/mkl/lib/intel64_lin:/ncar/opt/intel/psxe-2016_update1/compilers_and_libraries_2016.1.150/linux/compiler/lib/intel64_lin:\${LD_LIBRARY_PATH}'

        passed, out, err = self.extract_kernel(srcfile, namepath, \
            __cmd_clean='"cd %s; ./case.clean_build all"'%casedir, \
            __cmd_build='"cd %s; ./case.build"'%casedir, \
            __cmd_run='"cd %s; ./case.submit"'%casedir, \
            __invocation='100:0-1:10,100:0-1:50,300:0-1:10,300:0-1:50,500:0-1:10,500:0-1:50', \
            __kernel_option='-mkl=link', \
            __prerun='kernel_run="%s"'%prerun_krun, \
            __timing='repeat=1', \
            _e='%s/exclude.ini'%workdir, \
            __mpi='comm=mpicom,use="spmd_utils:mpicom",header="/ncar/opt/intel/12.1.0.233/impi/4.0.3.008/intel64/include/mpif.h"', \
            __openmp='enable', \
            __outdir=workdir)
            #__rebuild='all',
            #__kernel_compile='PRERUN="module load intel/16.0.2"',
            #__debug='printvar=:i,:j,:output',

        result[myname]['stdout'] = out
        result[myname]['stderr'] = err
        result[myname]['datadir'] = '%s/data'%workdir


        if passed:
            result[myname]['statefiles'] = ['advance_clubb_core_api.100.0.10', 'advance_clubb_core_api.100.1.10', 'advance_clubb_core_api.100.0.50', \
                'advance_clubb_core_api.100.1.50', 'advance_clubb_core_api.300.0.10', 'advance_clubb_core_api.300.1.10', 'advance_clubb_core_api.300.0.50', \
                'advance_clubb_core_api.300.1.50', 'advance_clubb_core_api.500.0.10', 'advance_clubb_core_api.500.1.10', 'advance_clubb_core_api.500.0.50', \
                'advance_clubb_core_api.500.1.50' ]
            self.set_status(result, myname, self.PASSED)
        else:
            result[myname]['statefiles'] = []
            self.set_status(result, myname, self.FAILED, 'STDOUT: %s\nSTDERR: %s'%(out, err))

        return result
#
#    def replace(self, myname, result):
#
#        workdir = result['mkdir_task']['workdir']
#        camsrcmods = result['generate_task']['camsrcmods']
#
#        out, err, retcode = self.run_shcmd('rm -f *', cwd=camsrcmods)
#
#        for instrumented in glob.glob('%s/state/*.F90'%workdir):
#            shutil.copy2(instrumented, camsrcmods)
#
#        self.set_status(result, myname, self.PASSED)
#
#        return result

if __name__ == "__main__":
    # we may allow to run this test individually
    print('Please do not run this script from command line. Instead, run this script through KGen Test Suite .')
    print('Usage: cd ${KGEN_HOME}/test; ./kgentest.py')
    sys.exit(-1)

