# MISFILS
MISFILS: The MongoDB-based Implementation for the San Francisco Integrated Library System.

This folder contains the submission files for Assignment 2. The remaining folders contain the files from Assignment 1.

Make sure to keep all your Assignment 2 files inside this folder to keep the rest of the folders free from clutter. That way, it will be easier to grade both Assignment 1 and Assignment 2.


Requirements:
-Python 3
-MongoDB Community Server
-MongoDB Compass (for GUI)
-PyMongo
-pandas
-openpyxl

Installation:
python -m pip install -r .\mongo\requirements.txt

Start MongoDB Community Server. The application connects using: "mongodb://localhost:27017"

Get data from SFILS repository with command "python ./mongo/scripts/import_data.py"

Create indexes with command "python ./mongo/scripts/create_indexes.py"


From the root SFILS project folder, use command "python .\mongo\app.py"

The application gives allows choices:
1. Database summary
2. Sample usage records
3. Search by patron type
4. Usage by library
5. Search by registration year
6. Exit