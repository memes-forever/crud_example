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
