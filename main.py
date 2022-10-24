# -*- coding: utf-8 -*-
from flask import Flask
from flask import request
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

from google.cloud import storage

import os
import pptx_helper
import shutil

storage_client = storage.Client.from_service_account_json("serviceaccount.json")
app = Flask(__name__, template_folder="templates", static_folder="static")
upload_path = "static/uploads"


@app.route("/create_gcp_bucket", methods=["POST"])
def create_gcp_bucket():

    # get org_name json - ex.{"organizationName": "main_bucket"}
    data = request.get_json()
    org_name = data["organizationName"]

    # if org_name is not received, return error json
    if not org_name:
        return {"confirmation": "fail", "message": "organizationName is required"}
    try:
        bucketId = ""
        # if bucket is not exist, create new bucket and return success json
        # if bucket exists, return success json

        if not storage_client.bucket(org_name).exists():
            try:
                bucketId = pptx_helper.create_bucket(org_name)
                return {"confirmation": "success", "data": {"bucketId": bucketId}}
            except:
                return {"confirmation": "fail", "message": "GCP bucket created failed"}
        else:  
            bucketId = org_name

        return {"confirmation": "success", "data": {"bucketId": bucketId}}

    except Exception as e:
        print(e)    
        return {"confirmation": "fail", "message": "GCP bucket created failed"}
    

@app.route("/create_user_folder", methods=["POST"])

def create_user_folder():

    # bucket 
    org_name = request.form.get("organizationName")

    if not org_name:
        return {"confirmation": "fail", "message": "organizationName is required"}

    # check if main bucket exists
    if not storage_client.bucket(org_name).exists():
        return {"confirmation": "fail", "message": "organizationName does not exist"}

    # userId folder 
    userId = request.form.get("userId")

    if not userId:
        return {"confirmation": "fail", "message": "userId is required"}
    try:
        bucket = storage_client.get_bucket(org_name)
        blob = bucket.blob(f"{userId}/")

        if blob.exists():
            bucketPath = f"{org_name}/{userId}/"
        else:
            blob.upload_from_string('')

            bucketPath = f"{org_name}/{userId}/"

        return {"bucketPath": bucketPath}
    except Exception as e:
        print(e)
        return {"confirmation": "fail", "message": "error creating user folder"}




@app.route("/pptx_upload", methods=["POST"])
def pptx_upload():

     # bucket 
    org_name = request.form.get("organizationName")

    if not org_name:
        return {"confirmation": "fail", "message": "organizationName is required"}

    # check if main bucket exists
    if not storage_client.bucket(org_name).exists():
        return {"confirmation": "fail", "message": "organizationName does not exist"}

    # userId folder 

    userId = request.form.get("userId")

    if not userId:
        return {"confirmation": "fail", "message": "userId is required"}

    # check if userId folder exists
    bucket = storage_client.get_bucket(org_name)
    blob = bucket.blob(f"{userId}/")

    if not blob.exists():    
        return {"confirmation": "fail", "message": "userId does not exist"}


    # get pptx file
    file = request.files['file']

    if not file:
        return {"confirmation": "fail", "message": "file is required"}

    if not file.filename.endswith((".pptx")):
        return {"confirmation": "fail", "message": "Invalid file, must be .pptx"}


    try:
        try:
            # save pptx into temp directory
            if not os.path.exists(f"static/uploads/{userId}_pptx/"):
                os.mkdir(f"static/uploads/{userId}_pptx/")
                os.mkdir(f"static/uploads/{userId}_pptx/json/")
                os.mkdir(f"static/uploads/{userId}_pptx/tables/")
                os.mkdir(f"static/uploads/{userId}_pptx/images/")

            TEMP_DIR = f"static/uploads/{userId}_pptx"
            filename = secure_filename(file.filename)
            file.save(os.path.join(TEMP_DIR, filename))

            # extract and upload to gcp
            output_json = pptx_helper.pptx_extractor((os.path.join(TEMP_DIR, filename)), filename, TEMP_DIR, org_name, userId)

            # remove temp_directory
            shutil.rmtree(TEMP_DIR)
        
        except Exception as e:
            print(e)
        if output_json is None:
            return {"confirmation": "fail", "message": "pptx file extraction error"}
        else:
            return {"confirmation": "success", "data": output_json}

    except (HTTPException, TypeError, ValueError, NameError, KeyError) as e:
        print(e)
        return {"confirmation": "fail", "message": "api error"}
    except Exception as e:
        print(e)
        return {"confirmation": "fail", "message": "api error"}



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)