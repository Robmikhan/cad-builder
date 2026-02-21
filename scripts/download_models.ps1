.\.venv\Scripts\Activate.ps1
pip install -U "huggingface_hub[cli]"
mkdir data\cache\models -Force | Out-Null

huggingface-cli download stabilityai/TripoSR --local-dir data\cache\models\triposr --local-dir-use-symlinks False
huggingface-cli download stabilityai/stable-fast-3d --local-dir data\cache\models\sf3d --local-dir-use-symlinks False
huggingface-cli download tencent/Hunyuan3D-2 --local-dir data\cache\models\hunyuan3d --local-dir-use-symlinks False
