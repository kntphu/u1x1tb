
**Google cloud command**  

`gcloud auth login `

** Deploy Google Cloud Function**

```
cd app_gcp/
gcloud functions deploy run_script_01 --runtime python38 --allow-unauthenticated --memory 2048MB --timeout 240 --region asia-southeast1
gcloud functions deploy run_script_02 --runtime python38 --allow-unauthenticated --memory 2048MB --timeout 240 --region asia-southeast2
```


**Add more function worker**

- Go to `app_gcp/main.py`

- Add more function with new ones (Ex. `def run_script_03`)
```commandline
@functions_framework.http
def run_script_XX(request: Request):
    return run_script_general(request)
```

- deploy new function with
```commandline
gcloud functions deploy run_script_XX --runtime python38 --allow-unauthenticated --memory 2048MB --timeout 240 --region asia-southeast2
gcloud functions deploy run_script_xx --gen2 --runtime python38 --allow-unauthenticated --memory 2048MB --entry-point run_script_103 --region asia-southeast2 --trigger-http --timeout 360s --max-instances 4
```


**How to debug and run local?**

- run `app_gcp/main_loca.py`

- hit POST `http://127.0.0.1:5000/run`
