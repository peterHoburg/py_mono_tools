### Installation

`pip install py-mono-tools`

#### Installing extras

Install all extras

`pip install py-mono-tools[all]`

Install all python extras

`pip install py-mono-tools[python]`

Install specific extras

```bash
pip install py-mono-tools[python_linters]
pip install py-mono-tools[python_testers]
```


**NOTE: Docker is REQUIRED to run any of the Terraform linters, or use the Docker backend.**

### Basic Usage

CONF in current directory

`pmt lint`

Relative path to CONF

`pmt -rp ./src/example_module lint`

Absolute path to CONF

`pmt -ap /home/user/src/example_module lint`

Name in CONF (CONF must be in current/child directory)

`pmt -n example_name lint`
