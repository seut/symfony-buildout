import os, logging
from subprocess import PIPE, Popen
import re

log = logging.getLogger('PHP hooks')

# hook to modify the Makefile of php to 
# let php use our openssl and not macports' 
# one
# in MH_BUNDLE_FLAGS set our openssl libdir to 
# be the first libdir..
def premake(options, buildout):
    makefile = os.path.join(buildout['php']['compile-directory'], 
            re.sub('(php-[0-9\.]+[0-9]).*', '\\1',
                buildout['php']['url'].split('/')[-1]),
            'Makefile')
    log.info("processing Makefile: %s" % makefile)

    data = open(makefile).read()
    lib_target = "%s/lib" % buildout['openssl']['location']
    log.info("add lib target: %s" % lib_target)

    w = open(makefile, 'w')
    w.write( re.sub('((?<!$)MH_BUNDLE_FLAGS)(.*?)(-L.*)', '\\1 \\2 -L%s \\3'
        % lib_target, data) )
    w.close

def run_phpize(options, buildout):
    #here = os.getcwd()
    #log.info('pwd is: '+here)
    #log.info('options: '+str(options))
    phpize_bin = buildout['php']['location'] + '/bin/phpize'
    log.info("Running phpize..")
    pr = Popen(phpize_bin, shell=True, stdout=PIPE, stderr=PIPE)
    if pr.wait() != 0:
        log.error(pr.stderr.read())

def post_make(options, buildout):
    log.info('Fixing CLI name ...')
    base_dir = buildout['php']['location']
    src = os.path.join(base_dir, 'bin', 'php.dSYM')
    trg = os.path.join(base_dir, 'bin', 'php')

    if os.path.isfile(src):
        os.rename(src, trg)
        log.info('done: %s > %s', src, trg)
    else:
        log.info('nothing to do')
