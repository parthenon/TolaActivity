# Tola Activity

**The build status of the dev branch is: [![Build Status](https://travis-ci.org/mercycorps/TolaActivity.svg?branch=dev)](https://travis-ci.org/mercycorps/TolaActivity)**

[TolaActivity](http://www.github.com/toladata/TolaActivity) extends
the functionality of [TolaData](https://www.toladata.com/) to include a
set of forms and reports for managing project activities for a Program. It
includes workflow for approving and completing projects as well as sharing
the output data. TolaActivity functionality is intended to allow importing
and exporting of project-specific data from 3rd party data sources or
excel files.

# Creating a local TolaActivity instance

Running a local instance of TolaActivity makes development much faster and
eliminates your dependence on access to any of MC's TolaActivity instances.
These instructions should get you up and running with a minimum of fuss if
you have [macOS](#macos) or one of the many [Ubunten](#ubuntu). If they do
not, we accept pull requests updating it. :)

## Install the bits

TolaActivity requires Python 2. MC uses MySQL as Django's datastore.

### macOS

On macOS, you can use Homebrew to install Python 2 alongside the system
Python 2 installation as shown in the following. You'll need to get a copy
the file _settings.secret.yml_ from your mentor before proceeding.

```bash
$ brew install python@2
$ brew install pip
$ brew install mysql mysql-utilies
$ brew install py2cairo pango
$ git clone https://github.com/mercycorps.org/TolaActivity.git
$ cd TolaActivity
$ git checkout dev
$ virtualenv -p python2 TolaActivty --no-site-packages venv # need to specify Python 2 for systems that might have Python 3 as default system version
$ source venv/bin/activate
$ mkdir config
# Place settings.secret.yml into config/ directory
cp config/sample-settings.secret.yml config/settings.secret.yml
pip install -r requirements.txt
pip install --upgrade google-api-python-client
```

Edit the configuration file as described in
[Modify the config file](#modify-the-config-file).

### Ubuntu

On _Ubunten_ and derivatives, the following should get you going. We
specify Python 2 because one day Python 3 *will* be the system Python.
You'll need to get a copy the file _settings.secret.yml_
from your mentor before proceeding:

```bash
$ python --version
# Make sure output from above indicates Python 2
$ sudo apt install mysql-server libmysqld-dev mysql-utilities mysql-client
$ sudo apt install libsasl2-dev python-dev libldap2-dev libssl-dev
$ git clone https://github.com/mercycorps.org/TolaActivity.git
$ cd TolaActivity
$ virtualenv -p python2 --no-site-packages venv
$ source venv/bin/activate
$ git checkout dev
$ mkdir config
# Place settings.secret.yml into config/ directory
$ pip install -r requirements.txt
$ pip install --upgrade google-api-python-client
```

Edit the configuration file as described in
[Modify the config file](#modify-the-config-file).

## Modify the config file

1. Edit _config/settings.secret.yml_. Find the node named, "DATABASES" and set the
database `PASSWORD` as appropriate. The result should resemble the following:

    ```yaml
    DATABASES:
      default:
        ENGINE: "django.db.backends.mysql"
        NAME: "tola_activity"
        USER: "admin"
        PASSWORD: "SooperSekritWord"
        OPTIONS: {"init_command": "SET default_storage_engine=MYISAM",}
        HOST: "localhost"
        PORT: ""
    ```

    Don't change the `USER` entry unless you know why you need
    to do that.

1. Add an entry for the `SECRET_KEY` at the bottom of the file:

    ```yaml
    SECRET_KEY: 'YOUR_RANDOM_STRING_HERE'
    ```

1. Add an entry for the server `LOGFILE` at the bottom of the file:

    ```yaml
    LOGFILE: 'logs/runserver.log'
    ```

1. Make the log dir

    ```bash
    $ mkdir logs
    ```

## Set up Django's MySQL backing store

```sql
mysql> CREATE DATABASE 'tola_activity';
mysql> CREATE USER 'admin';
mysql> GRANT ALL ON tola_activity.* TO 'admin'@'localhost' IDENTIFIED BY 'SooperSekritWord';
```

## Set up Django

Set up the Django database:

```bash
$ python manage.py migrate

Operations to perform:
  Apply all migrations: admin, auth, authtoken, contenttypes, customdashboard, formlibrary, indicators, reports, sessions, sites, social_django, workflow
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK


  [output deleted]

  Applying workflow.0018_auto_20180514_1637... OK
  Applying workflow.0019_language_choice... OK
  Applying workflow.0020_auto_20180918_1554... OK
```

### If you get an error during migration

During migration, you might see an error like the following:

```bash
Applying social_django.0005_auto_20160727_2333
  django.db.utils.OperationalError: (1071, 'Specified key was too long; max key length is 1000 bytes')
```

The *social_django* app creates a *unique_together* relationship between two rows that concatenate
to a value too long for the destination row. To fix this, manually change the following two fields:

* social_auth_association.server_url to varchar(100)
* social_auth_association.handle to varchar(100)

In the MySQL CLI:

```bash
mysql> USE tola_activity;
mysql> ALTER TABLE social_auth_association MODIFY server_url varchar(100) NOT NULL;
mysql> ALTER TABLE social_auth_association MODIFY handle varchar(100) NOT NULL;
```

...then re-run the migration as normal:

```bash
$ python manage.py migrate
```


Start the server:

```bash
$ python manage.py runserver
Performing system checks...

System check identified 1 issue (0 silenced).
March 20, 2018 - 11:51:55
Django version 1.11.2, using settings 'tola.settings.local'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

## Configuring OAuth authentication

When running a local instance, we use Google's OAuth API for
authentication to TolaActivity. There exists a bug in the API library
that requires an ugly manual workaround before you can actually log in
and starting using TolaActivity. The following procedure is a workaround
for this bug until the bug is well and truly crushed.

1. Start the TolaActivity server as described in the previous section
1. Open the home page in a web browser
1. Click the "Google+" link below the login button to authenticate with
   Google OAuth
1. Login as normal using your MercyCorps SSO login
1. What _should_ happen is that you get logged in and redirected to
   to the TolaActivity home page. Likely as not, though, you'll get
   a screen remarkably similar to the one in the following figure.
   You guessed it, that means you've hit the bug.
   ![ugly Django/Python traceback](docs/oauth_error.png)
1. Stop the TolaActivity server
1. Open a MySQL shell and connect to the tola_activity database
1. Get the id of the record Google OAuth added to the TolaActivity
   user table:

    ```bash
    mysql> SELECT id,username,first_name,last_name FROM auth_user;
    +----+----------+------------+-----------+
    | id | username | first_name | last_name |
    +----+----------+------------+-----------+
    |  1 | kwall    | Kurt       | Wall      |
    +----+----------+------------+-----------+
    ```
    
    Note the value for `id` to use in the next step.

1. Insert the `id` value from the `auth_user` table into the `user_id` field
   of the `workflow_tolauser` table:

    ```bash
    msql> INSERT INTO workflow_tolauser (name, privacy_disclaimer_accepted, user_id, language) VALUES (YOURNAME, 1,1, "en");
    ```

1. Restart the Tola Activity server

    ```bash
    $ python manage.py runserver
    Performing system checks...

    System check identified no issues (0 silenced).
    March 26, 2018 - 23:38:10
    Django version 1.11.2, using settings 'tola.settings.local'
    Starting development server at http://127.0.0.1:8000/
    Quit the server with CONTROL-C.
    ```

1. Refresh the browser window and you should be logged in and immediately
   redirected to the TolaActivity home page
1. Rejoice!

## Loading demo data

1. Get a recent DB dump from a Tola instance from your mentor
1. Kill the TolaActivity server
1. Make a backup of the current *tola_activity* DB if it's precious
1. Drop and recreate the *tola_activity* DB. Using the MySQL CLI:

   ```sql
   DROP DATABASE 'tola_activity';
   CREATE DATABASE 'tola_activity';
   ```

1. Execute the SQL script you were given to load the data:

    ```bash
    $ mysql -u root -p tola_activity < demo_data.sql
    ```

## Front-end development setup and dev server

Tola uses Webpack and `npm` installed packages in `node_modules` to build javascript bundles.
During development, you will need to run the webpack development server to have the latest JS
bundles available, and to re-generate the bundles if you modify any JS handled by Webpack.

Directions for installing `npm` can be found below. It can also be installed via homebrew on macOS

```bash
$ brew install npm
```

### Install all `node_module` package dependencies using `npm`

```bash
$ npm install
```

Note: You made need to periodiclly run this after doing a `git pull` if `package.json` has been
updated with new dependencies. This is similar to running `pip install -r requements.txt` if
the `requirements.txt` has been updated.

### Start the webpack development server

```bash
$ npm run watch
```

This should be done along side `./manage.py runserver`

### Build bundles for production

When you are ready to deploy to an external server, you will need to build and check-in the
production ready bundles. These are generated with:

```bash
$ npm run build:prod
```

or use the alias

```bash
$ npm run build
```

## Installing and running the front-end harness

*See also the [front-end architecture roadmap](https://github.com/mercycorps/TolaActivity/wiki/Proposal-for-front-end-architecture).*

This is *optional* if you are not doing significant front-end development. You can bypass the frontend build by dropping selectors into `/path/to/project/tola/static/css/app.css`.

### Installation & Startup:

1. Globally install [npm](https://www.npmjs.com). Here are [general instructions](https://docs.npmjs.com/getting-started/installing-node#install-npm--manage-npm-versions) to do so. On my Mac I prefer to install it via [Homebrew](https://www.dyclassroom.com/howto-mac/how-to-install-nodejs-and-npm-on-mac-using-homebrew)
2. Install local dependencies:
    ```bash
    $ cd /path/to/project/
    $ npm install
    ```
    This will install all necessary node modules into `node_modules` at the project root.
3. Start a watch task that will copy necessary libraries and compile static files while you work:
    ```bash
    $ cd /path/to/project/
    $ npm start
    ```
    You can also configure PyCharm to run this task in the background:
    1. Select __Run__ → __Edit Configurations...__
    2. __Add new configuration__ (__⌘-n__ or click the __+__ button)
    3. Choose __npm__ in the wee popup
    4. PyCharm should automagically select the correct __package.json__: `/path/to/project/package.json`
    5. Choose the __Command__ `start`

npm will compile a single global css file at `/path/to/project/tola/static/css/tola.css`. This file includes the entire Bootstrap library (previously in `bootstrap.min.css` and `bootstrap-multiselect.min.css`), our custom selectors (previously in `app.css`), and overrides to Bootstrap (previously in `bootstrap_overrides.css`)



### Other tips:

1. __Never edit the compiled css (`tola.css`) directly.__ Any manual changes to compiled css files will be overwritten the next time the css is regenerated. They are theoretically retrievable via Git but see #3, below. Remember: you can always bypass the harness by dropping css selectors directly into `app.css`.

2. But seriously, you should just put your css into a .scss file & compile it properly. __Valid css is also valid scss.__ If you’re not sure where to write a selector, append it to the __end__ of the master scss file: `/path/to/project/scss/tola.scss`.

3. Please commit your compiled css to GitHub, preferably in the same commit as your edits to our scss files.

4. There is no need to resolve merge conflicts in compiled css. Resolve them in the scss files first, then regenerate your css and accept all changes from the right (HEAD) side.

5. Suggestions for Frontend coding practices are forthcoming.


