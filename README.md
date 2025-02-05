# CLEAR
Our CLEAR app. 
Our app takes keyword from the user and automatically push like button to keyword-related video.
This code includes python backend server and vanilla html&CSS&JS frontend.

# Setup

## Make virtual environment using venv or conda

If you want to use venv, follow below command.
You can use conda instead of venv.
``` bash
python -m venv .venv
```
You can select .venv environment from the button on the bottom right in vs code.

In bash(linux) terminal, you can activate this environment using below command.
``` bash
source .venv/bin/activate
```

In powershell(windows), you can use below command.
``` powershell
. .venv\Scripts\activate
```

## Install Dependencies
``` bash
pip install flask # This is the backend framework
pip install google-auth-oauthlib google-api-python-client google-auth # Pacakges for installing youtube api call
```

## Define Authentication Keys
This app requires google cloud OAuth 2.0 keys for authentication. To work locally, use a desktop type key. For a hosted server, use a web application type key. 

Then, define the authenticate function to read the relevant json file:

```
def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        "desktop or server key json.json", SCOPES
    )
```


# Run
You can host the server locally by executing below command.
``` bash
python connectingtoOathtesting_ratelikeall_web_in_use.py
```
You can use python debug(F5) button also.

Then, access the hosted webpage via [localhost:5000](localhost:5000)

Press `ctrl+c` to quit.

To make the server publically available, you need a DNS service and port forwarding to port 8443 locally for using https. 

# Hosted service
Alternativelly, you can access our hosted service at this link:

[link](https://melnikov.tplinkdns.com:8443)
