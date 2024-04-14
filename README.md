
# TianGong AI LangServe

## Env Preparing

### Using Ubuntu

```bash

sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.12
sudo apt install -y python3.12-dev
# sudo apt install -y python3.12-venv

sudo apt upgrade
```

### Using VSCode Dev Contariners

[Tutorial](https://code.visualstudio.com/docs/devcontainers/tutorial)

Python 3 -> Additional Options -> 3.12-bookworm -> Trust @devcontainers-contrib -> Keep Defaults

### Using Poetry

```bash
sudo apt update
sudo apt install pipx
sudo pipx ensurepath

pipx install poetry
# pipx install poetry --python /usr/bin/python3.12

poetry shell
poetry install --no-root
```

### LCA DB Schema Generation

```bash
npm install -g @xata.io/cli@latest
xata auth login
xata schema dump --file src/tools/lca_data_schema/schema_origin.json
```

### Auto Build

The auto build will be triggered by pushing any tag named like release-v$version. For instance, push a tag named as v0.0.1 will build a docker image of 0.0.1 version.

```bash
#list existing tags
git tag
#creat a new tag
git tag v0.0.1
#push this tag to origin
git push origin v0.0.1
```

### LangSmith

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_api_key
```

### secrets.toml

Copy secrets_dev.toml to secrets.toml and fill in the real secrets.

### To Be Removed

Setup `venv`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install requirements:

```bash
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt --upgrade

pip freeze > requirements_freeze.txt
```
