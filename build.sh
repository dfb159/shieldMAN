poetry lock
poetry install
poetry run python -m grpc_tools.protoc --proto_path=src --python_out=src --pyi_out=src --grpc_python_out=src src/protos/message_board/message_board.proto