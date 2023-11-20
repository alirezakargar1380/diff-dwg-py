from typing import Union
from fastapi import File, UploadFile
from typing import List
from fastapi import FastAPI
import os
import uuid
from app import process_images

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
            
    process_images("D:/code_projects/python/diff-dwg/uploads/" + file_names["file_1"],
                    "D:/code_projects/python/diff-dwg/uploads/" + file_names["file_2"])

    # process_images("D:/code_projects/python/diff-dwg/uploads/42b4559b-9cc2-4d0e-896b-ccdf010a6264.png",
    #                 "D:/code_projects/python/diff-dwg/uploads/edce41da-70aa-44ce-847c-d067675b309a.png")
    
    return {"message": f"Successfuly uploaded {[file.filename for file in files]}"}


if not os.path.exists("./uploads"):
    os.makedirs("./uploads")