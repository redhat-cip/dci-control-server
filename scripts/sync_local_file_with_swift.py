#!/usr/bin/env python

import os
import io
import tqdm
from dci import dci_config
from dci.db import models2
from sqlalchemy.orm import sessionmaker


conf = dci_config.CONFIG
swift = dci_config.get_store("files")
engine = dci_config.get_engine(conf).connect()
session = sessionmaker(bind=engine)()


# Calculate the total files to sync
file_list = os.walk(conf["FILES_UPLOAD_FOLDER"])


with tqdm.tqdm(total=sum(1 for _ in file_list)) as pbar:
    for dirname, dirnames, filenames in os.walk(conf["FILES_UPLOAD_FOLDER"]):
        if not filenames:
            pbar.update(1)
            continue
        for filename in filenames:
            # Check if file exist in the DB
            query = session.query(models2.File).filter(models2.File.id == filename)
            file = query.one()

            # If not, do not sync, that's an orphan file
            if file is None:
                tqdm.tqdm.write("File %s not found, do not sync" % filename)
                continue

            # If the file exist, check if it is already present in swift
            # and then upload it to swift if needed
            tqdm.tqdm.write("File %s found in DB" % filename)
            folder_len = len(conf["FILES_UPLOAD_FOLDER"])
            top_path = dirname[folder_len:]
            swift_path = swift.build_file_path(file.team_id, file.job_id, filename)
            tqdm.tqdm.write("Check if file is in swift : %s" % swift_path)
            try:
                swift.head(swift_path)
                tqdm.tqdm.write("File exist on swift")
            except:
                tqdm.tqdm.write("File not found on swift, we will sync it")
                f = io.open(dirname + "/" + filename, "rb")
                swift.upload(swift_path, f)
        pbar.update(1)
