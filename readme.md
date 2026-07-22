Create the venv first
```
python -m venv .venv
```

Activate your environment (Command below works in Powershell only, search if you're not using powershell)
```
.venv/Scripts/Activate.ps1
```

Install the packages of the environment
```
pip install -r requirements.txt
```

To run
```
python -m flask run
```