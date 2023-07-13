# golem-ray
Setup project
```bach
pip install -r requirements.txt
python setup.py develop
```
Run yagna
```bash
export YAGNA_APPKEY=...
yagna payment fund
yagna service run
```
Run Server
```bash
python main.py
```
Start ray
```bash
ray up golem-cluster.yaml
```
