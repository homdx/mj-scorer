copy C:\library\Dropbox\source\android\ZAPScorer\src\*.py D:\ZAPS\scorer\src\

docker run --rm -it --privileged -v d:\ZAPS\scorer:/src -v buildozer:/home/kivy applysci/buildozer /src/debug.sh


rem how to run a command as root in a running container:
rem docker exec -u root -t -i 4b55750b943c /bin/bash
rem usermod -aG sudo kivy

rem /opt/buildozer/buildozer/targets/android.py

