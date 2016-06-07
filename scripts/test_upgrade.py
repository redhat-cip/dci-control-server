#!/usr/bin/python

import os
import shutil
import subprocess

patches = {
    '11c31b8': (
        "diff --git a/scripts/db_provisioning.py b/scripts/db_provisioning.py\n"
        "index 022a7a9..63a39bb 100755\n"
        "--- a/scripts/db_provisioning.py\n"
        "+++ b/scripts/db_provisioning.py\n"
        "@@ -355,14 +355,6 @@ def init_db(db_conn):\n"
        "         tests[test] = db_ins(models.TESTS, name=test, data=DATA,\n"
        "                              topic_id=topic_id)\n"
        " \n"
        "-    # Create the super admin user\n"
        "-    admin_team = db_ins(models.TEAMS, name='admin')\n"
        "-\n"
        "-    db_ins(models.USERS, name='admin',\n"
        "-           role='admin',\n"
        "-           password=auth.hash_password('admin'),\n"
        "-           team_id=admin_team)\n"
        "-\n"
        "     # For each constructor create an admin and a user, cis and jobs\n"
        "     for company in COMPANIES:\n"
        "         c = {}\n"
        "@@ -391,20 +383,6 @@ if __name__ == '__main__':\n"
        "     conf = config.generate_conf()\n"
        "     db_uri = conf['SQLALCHEMY_DATABASE_URI']\n"
        " \n"
        "-    if sqlalchemy_utils.functions.database_exists(db_uri):\n"
        "-        while True:\n"
        "-            print('Be carefull this script will override your "
        "database:')\n"
        "-            print(db_uri)\n"
        "-            print('')\n"
        "-            i = raw_input('Continue ? [y/N] ').lower()\n"
        "-            if not i or i == 'n':\n"
        "-                sys.exit(0)\n"
        "-            if i == 'y':\n"
        "-                break\n"
        "-\n"
        "-        sqlalchemy_utils.functions.drop_database(db_uri)\n"
        "-\n"
        "-    sqlalchemy_utils.functions.create_database(db_uri)\n"
        " \n"
        "     engine = sqlalchemy.create_engine(db_uri)\n"
        "     models.metadata.create_all(engine)")
}


def clean_up():
    print('git clean')
    subprocess.call(['git', 'clean', '-fdx', '-e', '.db_dir'])
    print('git reset')
    subprocess.call(['git', 'reset', '--hard'])


def start_db():
    subprocess.call(['./scripts/start_db.sh'])
    subprocess.call(['createdb', '--host=%s/.db_dir/' % os.getcwd(), 'dci'])


def stop_db():
    subprocess.call(['pg_ctl', 'stop', '-D', '.db_dir'])
    shutil.rmtree('.db_dir')


def jump_to(rev):
    clean_up()
    subprocess.call(['git', 'checkout', rev])
    subprocess.call(['pip', 'install', '-e', '.'])
    if rev in patches:
        print('patching')
        with open('/tmp/my_patch', 'w') as fd:
            fd.write(patches[rev])
        print(subprocess.check_output(['patch', '-p1', '-i', '/tmp/my_patch']))


if 'EAT_MY_DATA' not in os.environ:
    print('This script will wipe your uncommited changes.')
    exit(1)

cur_rev = subprocess.check_output(['git', 'rev-parse', 'HEAD']).rstrip('\n')

stop_db()
start_db()

with open('/tmp/settings.py', 'a+') as fd:
    uri = 'postgresql:///dci?host=%s/.db_dir' % os.getcwd()
    fd.write("SQLALCHEMY_DATABASE_URI = '%s'\n" % uri)
    fd.write("FILES_UPLOAD_FOLDER = '/tmp/var/lib/dci-control-server/files'\n")
my_env = os.environ
my_env.update({
    'DCI_LOGIN': 'admin',
    'DCI_PASSWORD': 'admin',
    'DCI_SETTINGS_FILE': '/tmp/settings.py'})

jump_to('11c31b8')
subprocess.call(['dci-dbinit'], env=my_env)
subprocess.call(['./scripts/db_provisioning.py'], env=my_env)
jump_to(cur_rev)
subprocess.call(['dci-dbsync'], env=my_env)
