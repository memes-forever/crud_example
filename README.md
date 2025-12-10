# crud web table example

### install req
```shell
pip install -r req.txt
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
