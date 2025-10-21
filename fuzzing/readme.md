# mutating test set

## Fuzzer

Use designed mutators to mutate specific attributes/operator based on randomness.

```bash
# in root
python main.py ./policy_test_set/IIC351/Policy_IIC351.xml --fuzzing
```

## Merger

Merge multiple polcies into one.

```bash
# in root
python main.py ./policy_test_set/IIC351/Policy_IIC351.xml --merge --merge-level=3
```
