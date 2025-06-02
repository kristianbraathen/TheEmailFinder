@echo off
echo [%date% %time%] Test WebJob Starting > D:\home\LogFiles\testjob.txt
echo Hello World! >> D:\home\LogFiles\testjob.txt
echo [%date% %time%] Test WebJob Completed >> D:\home\LogFiles\testjob.txt 