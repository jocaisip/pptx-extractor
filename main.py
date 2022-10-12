# -*- coding: utf-8 -*-
from flask import Flask
from flask import request, session
from flask import render_template
from werkzeug.utils import secure_filename
from google.cloud import storage

import os
import pptx_helper
import shutil

storage_client = storage.Client.from_service_account_json("serviceaccount.json")
app = Flask(__name__, template_folder="templates", static_folder="static")
upload_path = "static/uploads"


@app.route("/create_gcp_bucket", methods=["POST"])
def create_gcp_bucket():

    # get userId json - ex.{"userId":"sample_userid"}
    data = request.get_json()
    userId = data["userId"]

    # if userId is not received, return error json
    if not userId:
        return {"confirmation": "fail", "message": "userId is required"}
    try:
        bucketId = ""
        # if bucket is not exist, create new bucket and return success json
        # if bucket exists, return success json

        if not storage_client.bucket(userId).exists():
            try:
                bucketId = pptx_helper.create_bucket(userId)
                return {"confirmation": "success", "data": {"bucketId": bucketId}}
            except:
                return {"confirmation": "fail", "message": "GCP bucket created failed"}
        else:  
            bucketId = userId

        return {"confirmation": "success", "data": {"bucketId": bucketId}}
    except:
         return {"confirmation": "fail", "message": "GCP bucket created failed"}
    



@app.route("/pptx_upload", methods=["POST"])
def pptx_upload():

    # get userId 
    userId = request.form.get("userId")

    if not userId:
        return {"confirmation": "fail", "message": "userId is required"}

    # get pptx file
    file = request.files['file']

    if not file:
        return {"confirmation": "fail", "message": "file is required"}

    if not file.filename.endswith((".pptx")):
        return {"confirmation": "fail", "message": "Invalid file, must be .pptx"}

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
        output_json = pptx_helper.pptx_extractor(
            (os.path.join(TEMP_DIR, filename)), TEMP_DIR, userId
        )

        # remove temp_directory
        shutil.rmtree(TEMP_DIR)

        return {"confirmation": "success", "data": output_json}
    except:
        return {"confirmation": "fail", "message": "api error"}



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)