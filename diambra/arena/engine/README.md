# How to prepare diambraClient.py

If `interface.proto` (Stored in engine) is updated, the next command is needed to update the `diambra_pb2.py` and `diambra_pb2_grpc.py` files

```
python -m grpc_tools.protoc -I $diambraEngineRoot/interface/  --python_out=. --grpc_python_out=. $diambraEngineRoot/interface/interface.proto

```
