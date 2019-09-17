#!/usr/bin/env python

import os
import io
import tqdm
from dci import dci_config
from dci.db import models
from sqlalchemy import sql


conf = dci_config.CONFIG
swift = dci_config.get_store('files')
engine = dci_config.get_engine(conf).connect()

_TABLE = models.FILES

# Calculate the total files to sync
file_list = os.walk(conf['FILES_UPLOAD_FOLDER'])


with tqdm.tqdm(total=sum(1 for _ in file_list)) as pbar:
    for dirname, dirnames, filenames in os.walk(conf['FILES_UPLOAD_FOLDER']):
        if not filenames:
            pbar.update(1)
            continue
        for filename in filenames:
            # Check if file exist in the DB
            query = sql.select([_TABLE]).where(_TABLE.c.id == filename)
            result = engine.execute(query)

            # If not, do not sync, that's an orphan file
            if result.rowcount == 0:
                tqdm.tqdm.write("File %s not found, do not sync" % filename)
                continue

            # If the file exist, check if it is already present in swift
            # and then upload it to swift if needed
            if result.rowcount == 1:
                tqdm.tqdm.write("File %s found in DB" % filename)
                top_path = dirname[len(conf['FILES_UPLOAD_FOLDER']):]
                row = result.fetchone()
                swift_path = swift.build_file_path(row['team_id'],
                                                   row['job_id'],
                                                   filename)
                tqdm.tqdm.write("Check if file is in swift : %s" % swift_path)
                try:
                    swift.head(swift_path)
                    tqdm.tqdm.write("File exist on swift")
                except:
                    tqdm.tqdm.write("File not found on swift, we will sync it")
                    f = io.open(dirname + "/" + filename, "rb")
                    swift.upload(swift_path, f)
        pbar.update(1)
