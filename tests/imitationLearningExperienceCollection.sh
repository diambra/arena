echo "Recording exprience for imitation learning"
echo "1) python randomTestWrappers.py --recordTraj 1;"
python randomTestWrappers.py --recordTraj 1;
echo "2) python randomTestWrappers.py --recordTraj 1 --hardCore 1;"
python randomTestWrappers.py --recordTraj 1 --hardCore 1;
echo "3) python randomTestWrappers.py --recordTraj 1 --player P1P2;"
python randomTestWrappers.py --recordTraj 1 --player P1P2;
echo "4) python randomTestWrappers.py --recordTraj 1 --player P1P2 --hardCore 1;"
python randomTestWrappers.py --recordTraj 1 --player P1P2 --hardCore 1;
echo "5) python randomTestWrappers.py --recordTraj 1 --actionSpace multiDiscrete;"
python randomTestWrappers.py --recordTraj 1 --actionSpace multiDiscrete;
echo "6) python randomTestWrappers.py --recordTraj 1 --actionSpace multiDiscrete --hardCore 1;"
python randomTestWrappers.py --recordTraj 1 --actionSpace multiDiscrete --hardCore 1;
echo "7) python randomTestWrappers.py --recordTraj 1 --player P1P2 --actionSpace multiDiscrete;"
python randomTestWrappers.py --recordTraj 1 --player P1P2 --actionSpace multiDiscrete;
echo "8) python randomTestWrappers.py --recordTraj 1 --player P1P2 --actionSpace multiDiscrete --hardCore 1;"
python randomTestWrappers.py --recordTraj 1 --player P1P2 --actionSpace multiDiscrete --hardCore 1;
