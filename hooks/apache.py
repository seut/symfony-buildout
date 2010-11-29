import os, logging
from subprocess import PIPE, Popen
import fileinput

httpd_conf_append = """
<IfModule mod_php5.c>

AddType  application/x-httpd-php         .php
AddType  application/x-httpd-php-source  .phps

</IfModule>

# Include ports configuration:
Include conf/ports.conf

# Include the virtual host configurations:
Include conf/vhosts/*.conf

"""

log = logging.getLogger('Apache hooks')

def post_make(options, buildout):
    config_path = buildout['apache']['location'] + '/conf/'
    vhost_config_path = config_path + 'vhosts'
    if not os.path.exists(vhost_config_path):
        log.info('Creating vhosts config directory')
        os.makedirs(vhost_config_path)

    for line in fileinput.input(config_path + 'httpd.conf', inplace=1):
        if line.startswith('Listen'):
            line = '#' + line
        print line,
    fileinput.close()

    configfile = open(config_path + 'httpd.conf', 'a')
    configfile.write(httpd_conf_append)
    configfile.close()

    cert_dir = config_path + 'ssl/'
    create_certificate(cert_dir, buildout)


def create_certificate(cert_dir, buildout):
    hostname = os.uname()[1].split('.')[0]
    hostname_long = hostname + '.' + buildout['phx']['domain']
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    if not os.path.exists(cert_dir+'/cert.pem'):
        log.info('Creating apache ssl certificate')
        cmd = 'openssl req -new -newkey rsa:1024 -keyout "%(cert)s" -out "%(cert)s" -days 3650 -nodes -x509 -subj "/C=DE/O=studiVZ/OU=engineering/CN=*.%(hostname_long)s" -batch' % dict(cert=cert_dir+'/cert.pem', hostname_long=hostname_long)
        pr = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        if pr.wait() != 0:
            log.error(pr.stderr.read())

