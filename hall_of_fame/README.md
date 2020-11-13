This [Flask](https://flask.palletsprojects.com) powers <https://chezsoi.org/lucas/undying-dusk/hall-of-fame>.


# Installation

    pip install flask

## Local launch

    FLASK_ENV=development ./hof_app.py

## nginx configuration

    location /lucas/undying-dusk/hall-of-fame {
        include uwsgi_params;
        rewrite ^/lucas/undying-dusk/hall-of-fame/?(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8085;
    }

## systemd service

    $ pew new undying-dusk -p python3 -i flask
    $ cat /etc/systemd/system/undying-dusk-hall-of-fame.service
    [Service]
    WorkingDirectory=/path/to/parent/dir
    ExecStart=/usr/local/bin/pew in undying-dusk python -u hof_app.py
    Restart=always
