# golem-ray
Setup project
```bach
pip install -r requirements.txt
python setup.py develop

Create an .env file basing on .env.example
```
Run yagna
```bash
export YAGNA_APPKEY=...
yagna payment fund
yagna service run
```
Run Server
```bash
python run.py
```
Start ray
```bash
ray up golem-cluster.yaml
```
