#!/usr/bin/python

import os
import shutil
import subprocess

patches = {
    '11c31b8': """diff --git a/scripts/db_provisioning.py b/scripts/db_provisioning.py
index 022a7a9..63a39bb 100755
--- a/scripts/db_provisioning.py
+++ b/scripts/db_provisioning.py
@@ -355,14 +355,6 @@ def init_db(db_conn):
         tests[test] = db_ins(models.TESTS, name=test, data=DATA,
                              topic_id=topic_id)
 
-    # Create the super admin user
-    admin_team = db_ins(models.TEAMS, name='admin')
-
-    db_ins(models.USERS, name='admin',
-           role='admin',
-           password=auth.hash_password('admin'),
-           team_id=admin_team)
-
     # For each constructor create an admin and a user, cis and jobs
     for company in COMPANIES:
         c = {}
@@ -391,20 +383,6 @@ if __name__ == '__main__':
     conf = config.generate_conf()
     db_uri = conf['SQLALCHEMY_DATABASE_URI']
 
-    if sqlalchemy_utils.functions.database_exists(db_uri):
-        while True:
-            print('Be carefull this script will override your database:')
-            print(db_uri)
-            print('')
-            i = raw_input('Continue ? [y/N] ').lower()
-            if not i or i == 'n':
-                sys.exit(0)
-            if i == 'y':
-                break
-
-        sqlalchemy_utils.functions.drop_database(db_uri)
-
-    sqlalchemy_utils.functions.create_database(db_uri)
 
     engine = sqlalchemy.create_engine(db_uri)
     models.metadata.create_all(engine)
"""
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


jump_to('master')
stop_db()
start_db()

with open('/tmp/settings.py', 'a+') as fd:
    fd.write("SQLALCHEMY_DATABASE_URI = 'postgresql:///dci?host=%s/.db_dir'\n" % os.getcwd())
    fd.write("FILES_UPLOAD_FOLDER = '/tmp/var/lib/dci-control-server/files'\n")
my_env = os.environ
my_env.update({'DCI_LOGIN': 'admin', 'DCI_PASSWORD': 'admin', 'DCI_SETTINGS_FILE': '/tmp/settings.py'})

jump_to('11c31b8')
subprocess.call(['dci-dbinit'], env=my_env)
subprocess.call(['./scripts/db_provisioning.py'], env=my_env)
jump_to('master')
subprocess.call(['dci-dbsync'], env=my_env)
