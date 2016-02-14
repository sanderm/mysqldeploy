#!/usr/bin/env python

# Mysql Continues deployment - Deploys mysql data and git files between diffrent remote git targets
# Copyright (C) 2013  Sander Johansen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# How to install

# Requirements:
# apt-get install python-yaml keychain

# use ssh-keygen (without password) to generate a key
# copy this key to all your servers with ssh-copy-id
# $ ssh-keygen (enter 3x)
# $ ssh-copy-id username@webserverip.com (answer yes, and type in password)
# You should now be able to log into this machine without typing a password.

# Do on each mysql server you want to deploy to/from:
# (change and write down the dbname, dbusername and dbpassword in this file's config).
#
# $ mysql -u root -p -e "GRANT ALL ON dbname.* to 'dbusername'@'127.0.0.1' IDENTIFIED BY 'dbpassword';"

# Do on each mysql server you want to deploy from (read only content)
# $ mysql -u root -p -e "GRANT SELECT, LOCK TABLES ON dbname.* to 'dbusername'@'127.0.0.1' IDENTIFIED BY 'dbpassword';

# To make sure everyone got write group bit set, so none writes files none else also can write:
# $ echo "umask 0002" >> /etc/bash.bashrc

# Execute theese commands inside all root deployable dirs (be careful and repeat for every project):
# $ cd /var/www/project1/
# $ find -type d -exec chmod g=rwxs "{}" ";"
# $ chmod g+w -R .
# $ chgrp www-data -R .

# add deploy user, add the deploy user in www-data group, and everyone with deploy access should be in the deploy group
# $ useradd deploy
# $ addgroup deploy www-data
# $ addgroup username1 deploy
# $ addgroup username2 deploy
# Add access to everyone in the deploy group to execute commands under the deploy user: 
# $ echo "%deploy    ALL =(deploy) NOPASSWD: ALL" >> /etc/sudoers

# Make sure to change the setup of remote and local targets in the bottom of this file (require easy python programming)

# add a wrapper deploy script:
# $ echo -e '#!/bin/bash\n\nsudo -i -u deploy deploy.py "$@"' > /usr/local/bin/deploy
# Make sure the deploy user can execute the deploy command:
# $ echo 'export PATH="$PATH:/home/deploy/bin/"; umask 0002' >> /home/deploy/.bashrc
# Install this script:
# $ cp deploy.py /home/deploy/bin/deploy.py

import sys, os, re;
# if your python version dont have yaml, append the path to yaml
#sys.path.append("lib/python2.4/yaml/");
import argparse;

import yaml
config_str = """
dev_files:
  - wp-content/languages/
  - wp-content/themes/retlehs-roots-52064b6/
content_files:
  - wp-content/blogs.dir/
  - wp-content/uploads/
fullcopy:
  - ./
oslostartup:
  weburl: 'http://startupnorway.com'
  readonly: True
  db_user: DBUSERNAME
  db_pass: DBPASSWORD
  db_name: DBNAME
  db_host: DBHOST
  db_dump_ssh: True
  remote_file_path: 'sander@somehostname.com'
  dir_root_path: /home/sander/webapps/oslostartup/
  easy_replace:
  - '(emailname|sander)\%40startupnorway\.com'
  - '(\@|www\.)?startupnorway\.com'
oslostartuplocal:
  weburl: 'http://startupnorway.local/'
  readonly: False
  db_user: DBUSERNAME
  db_pass: DBPASSWORD
  db_name: DNNAME
  db_host: 127.0.0.1
  remote_file_path: '127.0.0.1'
  dir_root_path: /var/www/oslostartup/
  easy_replace:
  - '(emailname|sander)\%40startupnorway\.com'
  - '(\@|www\.)?startupnorway\.local'
"""

#########################################################################
## Dont edit under this line, only the last main funcion in this file  ##
#########################################################################

# uncomment to debug configuration
#print yaml.dump(yaml.load(config_str), default_flow_style=False)

config= yaml.load(config_str)
#print config_des['active24_st'];

#yaml.load_all(document);

def create_pid_data_dir():
   pid=os.getpid();
   data_path= os.path.join("/var/log/deploy/", str(pid));
   #data_path= os.path.join(os.path.dirname(__file__), "deploy_data/", str(pid));
   os.mkdir(data_path);
   return data_path;
config['data_path']= create_pid_data_dir();


def project_exists(name):
   global config;
   if name not in config:
     print "Couldn't find target: " + name;
     sys.exit(1);

def execute_command(cmd, message):
   print 'Executing: ' + message;
   print cmd;
   os.system(cmd);

def download_mysql_dump(name):
   global config;
   pid=os.getpid();
   project_exists(name);
   ssh_add="";
   ssh_after="";
   from_host= config[name]['remote_file_path'];
   mysql_backup_data=os.path.join(config['data_path'], "mysql_backup_" + name + ".sql");
   dump_path="~/" + "mysql_backup_" + str(pid) + "_" + name + ".sql";
   if 'db_dump_ssh' in config[name]:
     ssh_add="ssh " + from_host + " \"";
     ssh_after="\"";
     dump_host="localhost";
   else:
     dump_host=config[name]['db_host'];
     #dump_path=mysql_backup_data;


   cmd=ssh_add + "mysqldump --skip-extended-insert -u " + config[name]['db_user'] + " -h " + dump_host + " -p" + config[name]['db_pass'] + " " + config[name]['db_name'] + " > " + dump_path + ";" + ssh_after;
   message="Downloading MYSQL database from " + name + ":";
   execute_command(cmd, message);
   if 'db_dump_ssh' in config[name]:
     cmd="ssh "+ from_host + " \"cd ~/; cat " + dump_path + "\" > " + dump_path
     message="Copying mysql sql files from " + name + " to localhost";
     execute_command(cmd, message);

   cmd="mv "+ dump_path + " " + mysql_backup_data 
   message="Moving dump to archive: " + name;
   execute_command(cmd, message);



def replace_string_mysql_dump(name_from, name_to):
   global config;
   mysql_tmp_after_data= os.path.join(config['data_path'], "mysql_tmp_after_from_" + name_from + ".sql");
   mysql_backup_data= os.path.join(config['data_path'], "mysql_backup_" + name_from + ".sql");
   mysql_tmp_ready_import_data= os.path.join(config['data_path'], "mysql_tmp_ready_for_import_" + name_to + ".sql");

   project_exists(name_from);
   project_exists(name_to);

   message="Copying mysql dump (we dont want to overwrite backup on string replace):";
   cmd="cp -f " + mysql_backup_data + " " + mysql_tmp_after_data ;
   execute_command(cmd, message);

   #for sed_replace in config[name_from]['string_replace_from']:
   #  cmd="sed -ri '" + sed_replace + "' " + mysql_tmp_after_data;
   #  message="Replacing strings:";
   #  execute_command(cmd, message);
   i=1;
   for sed_easy in config[name_from]['easy_replace']:
     sed_re = re.findall(r'\([^)]*\)', sed_easy);
     num_groups= len(sed_re);
     sed_keep_groups="";
     print num_groups;
     for b in range(num_groups):
       sed_keep_groups= sed_keep_groups + "\\" + str(b+1) + "_abc_";

     sed_replace="s/" + sed_easy + "/tmp_replace_abc_" + str(i) + "_" + sed_keep_groups + "/g";
     cmd="sed -ri '" + sed_replace + "' " + mysql_tmp_after_data;
     message="Replacing strings:";
     execute_command(cmd, message);
     i=i+1;

   message="Moving mysql dump from " + name_from + " to " + name_to + ":";
   cmd="mv -f " + mysql_tmp_after_data + " " + mysql_tmp_ready_import_data;
   execute_command(cmd, message);

   #for sed_replace in config[name_to]['string_replace_to']:
   #  cmd="sed -ri '" + sed_replace + "' " + mysql_tmp_ready_import_data;
   #  message="Replacing strings:";
   #  execute_command(cmd, message);
   i=len(config[name_to]['easy_replace']);
   for sed_easy in reversed(config[name_to]['easy_replace']):
     sed_re = re.findall(r'\([^)]*\)\??', sed_easy);
     num_groups= len(sed_re);
     sed_keep_groups="";
     sed_keep_matches="";
     print num_groups;
     for b in range(num_groups):
       sed_keep_groups= sed_keep_groups + "\\" + str(b+1) + "_abc_";
     for sed_i in sed_re:
       sed_keep_matches= sed_keep_matches + sed_i + "_abc_";
     a_range = iter(range(1,4)); 
     sed_easy_final= re.sub(r'\(.*?\)\??', lambda x: "\\" + str(next(a_range)), sed_easy);

     sed_replace="s/tmp_replace_abc_" + str(i) + "_" + sed_keep_matches + "/" + sed_easy_final + "/g";
     cmd="sed -ri '" + sed_replace + "' " + mysql_tmp_ready_import_data;
     message="Replacing strings:";
     execute_command(cmd, message);
     i=i-1;

def import_mysql_dump(name):
   global config;
   mysql_tmp_ready_import_data= os.path.join(config['data_path'],"mysql_tmp_ready_for_import_" + name + ".sql");
   project_exists(name);

   message="Starting mysql insert dump to " + name;
   cmd="mysql -u " + config[name]['db_user'] + " -h " + config[name]['db_host'] + " -p" + config[name]['db_pass'] + " " + config[name]['db_name'] + " < " + mysql_tmp_ready_import_data + ";";
   execute_command(cmd, message);

def copy_files(name_from, name_to, what_files):
   if 'readonly' in config[name_to]:
      if config[name_to]['readonly'] == "True" and what_files != dev_files:
         print "Not allowed to deploy files to " + name_to;
         sys.exit(1);
   project_exists(name_from);
   project_exists(name_to);
   if what_files not in config:
      print "Can't find files " + what_files;
      sys.exit(1);

   for file in config[what_files]:
     basename= os.path.basename(os.path.normpath(file));
     from_host= config[name_from]['remote_file_path'];
     to_host= config[name_to]['remote_file_path'];

     from_path= os.path.join(config[name_from]['dir_root_path'], file);
     parent_from_path= os.path.dirname(os.path.normpath(from_path));

     to_path= os.path.join(config[name_to]['dir_root_path'], file);
     parent_to_path= os.path.dirname(os.path.normpath(to_path));

     tmp_path=os.path.join(config['data_path'],basename);

     #from_args= config[name_from]['remote_file_path'] + ":" + os.path.join(config[name_from]['dir_root_path'], from_file);
     #cmd="scp -r -q " + from_args + " " + config['data_path'];
     cmd="ssh "+ from_host + " \"cd " + parent_from_path + "; tar cfz - " + basename + "\" > " + tmp_path + ".tgz "
     message="Copying files from " + name_from + " to backupdir";
     execute_command(cmd, message);

     if os.path.exists(tmp_path + ".tgz"):

       #cmd="scp -r -q " +  os.path.join(config['data_path'],to_basename) + " " + config[name_to]['remote_file_path'] + ":" + to_file;
       cmd="cat " + tmp_path + ".tgz | ssh "+ to_host + " \"cd " + parent_to_path + "; tar zxfm - \"";
       #cmd="ssh  " +  os.path.join(config['data_path'],to_basename) + " " + config[name_to]['remote_file_path'] + ":" + to_file;
       message="Copying files from backupdir to " + name_to;
       execute_command(cmd, message);

       cmd="ssh " + to_host + " \"find " + to_path + " ! -perm /g+w -printf '%M %p\\n'\""
       message="Files that needs to be chmodded:";
       # you should run this commmand on those files: find -type d -exec chmod g=rwxs \"{}\" \";\"; chmod g+w -R .;";
       execute_command(cmd, message);

       cmd="ssh " + to_host + " \"find " + to_path + " ! -perm /o+r -printf '%M %p\\n'\""
       message="Files that needs to be chmodded:";
       # you should run this commmand on those files: chmod o+r -R .;";
       execute_command(cmd, message);

def transfer_mysql_dump(name_from, name_to):
   if 'readonly' in config[name_to]:
      if config[name_to]['readonly'] == "True":
         print "Not allowed to deploy mysql dump to " + name_to;
         sys.exit(1);
   download_mysql_dump(name_from);
   download_mysql_dump(name_to);
   replace_string_mysql_dump(name_from, name_to);
   import_mysql_dump(name_to);


def main():
   global config;
   if len(sys.argv) < 2:
      #sys.exit('Deploys mysql data and files between diffrent remote targets\nUsage: %s <deploy to>\n  st: dump and content files from live, dev files from dev\n  dev: dump and content from live\n  prod: dump and content files from live, dev files from dev\n  live: dev files from dev\n' % sys.argv[0]);
      for site in config:
        if 'weburl' in config[site]:
          print site, ": ", config[site]['weburl'];
      sys.exit('Mysql continutes deployment - Deploys mysql data and git files between diffrent remote git targets\nUsage: %s <deploy to>\n  \nstartupnorwaylocal: dump live files and content files from live to localhost\n' % "deploy");

   deploy_target=str(sys.argv[1]);
   fullcopy_var=str(sys.argv[2]);
   print "Deploying to " + deploy_target;
   if ("fullcopy" in fullcopy_var):
     fullcopy=True;
     copy_files("oslostartup", "oslostartuplocal", "full_copy");
   else:
     fullcopy=False;

   if deploy_target == "startupnorwaylocal":
      transfer_mysql_dump("oslostartup", "oslostartuplocal");
      if fullcopy:
        copy_files("oslostartup", "oslostartuplocal", "full_copy");
      else:
        copy_files("oslostartup", "oslostartuplocal", "dev_files");
        copy_files("oslostartup", "oslostartuplocal", "content_files");
   else:
      print "unknown target, choose between: startupnorwaylocal";

if  __name__ =='__main__':main()

