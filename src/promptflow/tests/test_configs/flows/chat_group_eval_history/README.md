# Basic Eval
This example shows how to create a basic evaluation flow that can evaluate multi-turn conversation history. 

Tools used in this flow：
- `python` tool

## Prerequisites

Install promptflow sdk and other dependencies in this folder:
```bash
pip install -r requirements.txt
```

## What you will learn

In this flow, you will learn
- how to compose a point based evaluation flow, where you can calculate point-wise metrics.
- the way to log metrics. use `from promptflow import log_metric`
    - see file [aggregate](aggregate.py).

### 1. Test flow with single line data

Testing flow/node:
```bash
# test with default input value in flow.dag.yaml
pf flow test --flow .

# test with flow inputs
pf flow test --flow . --inputs ground_truth=ABC

# test node with inputs
pf flow test --flow . --node line_process --inputs ground_truth=ABC
```

### 2. create flow run with multi line data
There are two ways to evaluate an classification flow.

```bash
pf run create --flow . --data ./data.jsonl --column-mapping ground_truth='${data.ground_truth}' --stream
```

You can also skip providing `column-mapping` if provided data has same column name as the flow.
Reference [here](https://aka.ms/pf/column-mapping) for default behavior when `column-mapping` not provided in CLI.
