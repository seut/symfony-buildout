import os, logging

log = logging.getLogger('Info hooks')

def post_install(options, buildout):
    print ""
    print ""
    print "see README for details... "    
    print ""
    print "======================="
    print "INSTALLATION SUCCESSFUL"
    print "======================="

if __name__ == '__main__':
    post_install({}, {})
