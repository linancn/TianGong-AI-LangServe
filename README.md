
# TianGong AI LangServe

## Env Preparing

### Using VSCode Dev Contariners

[Tutorial](https://code.visualstudio.com/docs/devcontainers/tutorial)

Python 3 -> Additional Options -> 3.11-bullseye -> ZSH Plugins (Last One) -> Trust @devcontainers-contrib -> Keep Defaults

Setup `venv`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install requirements:

```bash
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt --upgrade

pip freeze > requirements_freeze.txt
```

.env file

```bash
BEARER_TOKEN = 
XATA_API_KEY =
XATA_DB_URL =
XATA_TABLE_NAME = #Do not create table manually, it will be created automatically
OPENAI_API_KEY =
OPENAI_MODEL =
XATA_WORKSPACE_ID = #Full name of the workspace, such as "John Doe's workspace"
PINECONE_API_KEY =
PINECONE_ENVIRONMENT =
PINECONE_INDEX =
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
