# Install and execute Slice Manager

## Steps

1. Install libraries

```sh {"id":"01HZ7JWHHSBR26VZF89D530PMN"}
pip install flask # Create web server
pip install pyjwt # Use JWT
```

2. Run flask server

```sh {"id":"01HZ7JWHHSBR26VZF89F314ZDR"}
#python main.py
nohup python3 main.py > log_main.txt 2>&1 &
```

3. Run flask server debug mode

```sh {"id":"01HZ7JWHHSBR26VZF89J5S2R1W"}
flask --app main.py --debug run
```
