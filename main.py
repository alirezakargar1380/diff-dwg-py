from typing import Union
from fastapi import File, UploadFile
from typing import List
from fastapi import FastAPI
import os
import uuid
from app import process_images
from minio import Minio
from minio.error import S3Error

app = FastAPI()

@app.post("/upload")
def upload(files: List[UploadFile] = File(...)):
    file_names = {
        "file_1": None, 
        "file_2": None 
    }

    for i in range(len(files)):
        file = files[i]
        try:
            contents = file.file.read()
            filename = str(uuid.uuid4()) + ".png"
            if i == 0:
                file_names["file_1"] = filename
            else:
                file_names["file_2"] = filename
            with open(f"uploads/{filename}", 'wb') as f:
                f.write(contents)
        except Exception:
            return {"message": "There was an error uploading the file(s)"}
        finally:
            file.file.close()

    # True Code            
    # process_images("D:/code_projects/python/diff-dwg/uploads/" + file_names["file_1"],
    #                 "D:/code_projects/python/diff-dwg/uploads/" + file_names["file_2"])
    location = os.getcwd() + "/uploads/"
    diff_location = os.getcwd() + "/diff/"
    convertedFileName = process_images(location + file_names["file_1"],
                    location + file_names["file_2"])
    

    client = Minio(
        "5.56.134.154:9000",
        access_key="VIc01QJGemJBGBpZeeLq",
        secret_key="30yHBBftjVOCj2OVh2mPIRFr1gqc7p2Vrft0MOmp",
        secure=False,
        region="us-west"
    )

    found = client.bucket_exists("diffdwg")
    if not found:
        client.make_bucket("diffdwg")
    else:
        print("Bucket 'diffdwg' already exists")

    diffdir = os.getcwd() + '/diff/'

    client.fput_object(
        "diffdwg", convertedFileName, diffdir + convertedFileName,
    )

    url = client.get_presigned_url(
        "GET",
        "diffdwg",
        convertedFileName
    )

    os.remove(diffdir + convertedFileName)
    print(url)

    print("uploaded file name is:", convertedFileName)

    return {
        "message": f"Successfuly uploaded {[file.filename for file in files]}",
        "url": url
    }

# def main():
#     print(os.getcwd() + "/////")

# main()

if not os.path.exists("./uploads"):
    os.makedirs("./uploads")