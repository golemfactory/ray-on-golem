# golem-ray
Setup project
```bash
$ poetry install
```
Create an .env file basing on .env.example

Run yagna
```bash
$ export YAGNA_APPKEY=...
$ yagna payment fund
$ yagna service run
```
Run Server
```bash
$ python golem_ray/server/run.py
```
Start ray
```bash
$ ray up golem-cluster.yaml
```


## Contributing

### Running code auto format

```bash
$ poetry run poe format
```
