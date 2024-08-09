import multiprocessing
import os

default_nb_workers = multiprocessing.cpu_count() * 2 + 1
workers = int(os.getenv("DCI_NB_WORKERS", default_nb_workers))
