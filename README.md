# crud web table example

### install req
```shell
python -m venv .venv
source .venv/bin/activate
pip install -r req.txt
```

### start web in dev
```shell
python app.py dev
```

### start web
```shell
python app.py
```


### open sqllite
```shell
cd instance
sqlite3
.open "database.db"

select * from user;
select * from item;

# alter table user add column name String(80);
```


### Example as service
in console
```shell
sudo nano /etc/systemd/system/crud.service
```
and write this in file 

```shell
[Unit]
Description=CRUD Flask приложение на Waitress
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/root/git_proj/crud_example
Environment="PATH=/root/git_proj/crud_example/.venv/bin"
ExecStart=/root/git_proj/crud_example/.venv/bin/python /root/git_proj/crud_example/app.py
Restart=always
RestartSec=5

# Опционально: логи в отдельный файл
StandardOutput=append:/var/log/myflask.log
StandardError=append:/var/log/myflask.log

[Install]
WantedBy=multi-user.target
```

next in console:
```shell
sudo systemctl daemon-reexec
sudo systemctl enable crud.service    # автозапуск при загрузке
sudo systemctl start crud.service
```

status & logs in console
```shell
sudo systemctl status crud.service
journalctl -u crud.service -f          # живые логи
tail -f /var/log/crud.log              # если используешь файл
```
