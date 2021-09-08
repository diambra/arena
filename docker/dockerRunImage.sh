# X11Docker repo: https://github.com/mviereck/x11docker
docker cp /../roms/mame/ diambra-arena:/opt/diambraArena/roms/
docker run --rm --gpus all -it -v pythonDep:/usr/local/lib/python3.6/dist-packages/ -v diambraRoms:/opt/diambraArena/roms --name diambraArena diambra:diambra-arena-base bash
./x11docker --cap-default --hostipc --hostnet --name=diambraArena --wm=host -- -it -v pythonDep:/usr/local/lib/python3.6/dist-packages/ -v diambraRoms:/opt/diambraArena/roms -- diambra:diambra-arena-base bash
docker exec -u 0 -it diambraArena bash
