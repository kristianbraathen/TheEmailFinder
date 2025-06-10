@echo off
cd App_Data\jobs\triggered\test_webjob
set DATABASE_CONNECTION_STRING=postgresql://appbruker:SterktPassord123@theemailfinderserver.postgres.database.azure.com:5432/theemailfinder_database?sslmode=require
python run.py 