git pull
apt-get update
apt-get --assume-yes install graphviz ufw
pip install graphviz pydot
pip install --upgrade torch torchvision
python rpc_parameter_server.py --world_size="$1" --rank="$2" --num_gpus=1
