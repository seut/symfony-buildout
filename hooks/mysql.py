import sys, os, logging
from subprocess import PIPE, Popen, call
import tempfile
import setuptools.archive_util
import shutil
import fileinput
import socket
import time

from zc.buildout.download import Download
from zc.buildout import UserError

log = logging.getLogger('MySQL hooks')

def pre_buildout(options, buildout):
    port = buildout['mysql']['port']
    check_running_mysqld(port)

def check_running_mysqld(port):
    log.debug('Check for running process(mysqld) on mysql-port %s' % port)

    client = socket.socket()
    client.settimeout(0.25)
    try:
        client.connect(("127.0.0.1", int(port)))
    except socket.error:
        client.close()
        return False
    client.close()
    raise UserError("Seems like some process is listening on mysql-port" \
                  ' %s.\nCheck your processes and stop it before re-running ' \
                  'buildout.'
                  % port)


def pre_configure(options, buildout):
    destination = options.get('compile-directory')
    os.chdir(destination)
    log.info('Running autorun.sh')
    autorun_cmd = "sh BUILD/autorun.sh"
    pr = Popen(autorun_cmd, shell=True, stdout=PIPE, stderr=PIPE)
    if pr.wait() != 0:
        log.error(pr.stderr.read())


def post_make(options, buildout):
    location = options.get('location')
    log.debug('Fixing path in mysql_secure_installation.sh')
    mysql_sec_inst_path = os.path.join(location, 'bin', 'mysql_secure_installation')
    for line in fileinput.input(mysql_sec_inst_path,inplace=1):
        if "mysql --defaults-file=$config <$command" in line:
            line=line.replace('mysql', '%s/bin/mysql' % location)
            print line
    fileinput.close()




def setup_default_db(options, buildout):
    # check for running mysqld process
    port = buildout['mysql']['port']
    check_running_mysqld(port)
    location = buildout['mysql']['location']
    db_dir = buildout['buildout']['directory'] + '/var/mysql/db'
    base_dir = location
    etc_dir = location + '/etc'
    pw = buildout['mysql']['root-password']
    install_db = "%s/bin/mysql_install_db --basedir=%s --ldata=%s" % (location, base_dir, db_dir)
    change_pw = "%s/bin/mysqladmin -u root password %s" % (location, pw)
    mysqld_bin = "%s/libexec/mysqld" % location

    if not os.path.exists(db_dir + '/mysql'):
        log.info('Installing default database')
        os.makedirs(db_dir)
        pr = Popen(install_db, shell=True, stdout=PIPE, stderr=PIPE)
        if pr.wait() != 0:
            log.error(pr.stderr.read())

    log.debug('Starting mysql daemon ...')
    mysqld_pr = Popen(mysqld_bin, shell=True, stdout=PIPE, stderr=PIPE)
    time.sleep(1)
    log.info('Setting root password: %s ...', pw)
    pr = Popen(change_pw, shell=True, stdout=PIPE, stderr=PIPE)
    while pr.poll():
        line = pr.stdout.readline()
        log.debug(line.strip("\n"))
    if pr.wait() != 0:
        log.error(pr.stderr.read())
    log.debug('Terminating mysql daemon ...')
    #mysqld_pr.kill()
    mysqld_pr.terminate()
    counter = 0
    while mysqld_pr.poll():
        counter = counter + 1

        if counter > 10:
            log.error(mysqld_pr.stderr.read())
            break
        time.sleep(1)
    if mysqld_pr.wait() != 0:
        log.error(mysqld_pr.stderr.read())
    time.sleep(3)

    if not os.path.exists(etc_dir):
        log.info('Creating config directory ...')
        os.makedirs(etc_dir)


