# Hackers Chat

Source code for https://www.hackerschat.net/

<p align="center">
    <a href="https://www.hackerschat.net/topics/hackerschat/" alt="Chat on Hackerschat">
        <img src="https://img.shields.io/badge/chat-on%20Hackerschat-brightgreen.svg" />
    </a>
    &nbsp;&nbsp;
    <a href="https://www.hackerschat.net/topics/hackerschat/forum/" alt="Forum on Hackerschat">
        <img src="https://img.shields.io/badge/forum-on%20Hackerschat-brightgreen.svg" />
    </a>
</p>

# Setup instructions

*Note* : These instructions were tested on Ubuntu 18.04. If you are using a different OS, the installation instructions will need to be tweaked.

Update package index :

```
sudo apt-get update
```

Install required packages :

```
sudo apt-get install python3-pip python3-dev libpq-dev postgresql postgresql-contrib redis nginx
```

Setup postgres :

```
sudo -u postgres psql

CREATE DATABASE hackerschat;

CREATE USER hackerschatuser WITH PASSWORD 'DB_PASSWORD';

ALTER ROLE hackerschatuser SET client_encoding TO 'utf8';

ALTER ROLE hackerschatuser SET default_transaction_isolation TO 'read committed';

ALTER ROLE hackerschatuser SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE hackerschat TO hackerschatuser;

ALTER USER hackerschatuser WITH SUPERUSER;

\q
```

Setup the hackerschat project :

```
git clone https://github.com/ploggingdev/hackerschat.git

sudo apt install python3-venv

cd hackerschat

mkdir venv

python3 -m venv venv/hackerschat

source venv/hackerschat/bin/activate

pip install --upgrade pip

pip install -r requirements.txt
```

Set env variables in ~/.bashrc :

```
sudo nano ~/.bashrc
```

The following env variables are required :

```
export hackerschat_secret_key="CHOOSE_LONG_SECRET_KEY";
export hackerschat_db_name="hackerschat"
export hackerschat_db_user="hackerschatuser"
export hackerschat_db_password="DB_PASSWORD"
export hackerschat_db_url="localhost"
export redis_url="redis://localhost:6379"
export hackerschat_postmark_token="LEAVE_BLANK"
export DJANGO_SETTINGS_MODULE=hackerschat.settings
export hackerschat_recaptcha_secret_key="RECAPTCHA_KEY"
export hackerschat_toxicity_endpoint="PRIVATE_API"
```

Continue setup :

```
deactivate

source ~/.bashrc

source venv/hackerschat/bin/activate

python manage.py migrate
```

Create admin user :

```
python manage.py createsuperuser
```

Navigate to `http://127.0.0.1:8000/admin/` and add the following :

* "userprofile" for the admin user

* topic named "general"

*Important steps*

This project has a few external dependencies such as postmark for email, google recaptcha to reduce spam and it also depends on a private api to score each comment to automatically ban users who repeatedly use offensive words. Your local setup will need a few changes to get it to work :

1. Use a dummy email backend so that emails won't actually be sent. Change the `EMAIL_BACKEND` in `settings.py` as follows :

```
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
```

2. In `hackerschat/celery.py` there is a function named `check_message_toxicity(message_id)`. Since you don't have access to the private api, make the first statement as `return`. This prevents the original function code from being executed.

3. Recaptcha V2 is used for login and other pages such as registration, password reset. You will need to create an api key on the recaptcha site and update the following :

* In `~/.bashrc` update `hackerschat_recaptcha_secret_key`

* In `user_auth/templates/registration/login.html` update `datasite-key`

Start python and celery :

```
python manage.py runserver

celery -A hackerschat worker -B -l info
```

Visit the development server at `127.0.0.1:8000` to test the site.

If you face any issues, please visit the [hackerschat topic](https://www.hackerschat.net/topics/hackerschat/).