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

