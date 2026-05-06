# ToMRAGv2 接口文档

## 快速上手

```python
from src.rag_v2 import ToMRAGv2

# 初始化
rag = ToMRAGv2(
    data_dir: str = "./data",
    index_dir: str = "./index",
    model_name: str = "./models/bge-m3",
    use_rewritten: bool = True,
)

# 构建索引（首次运行，后续可加载缓存）
rag.build_index()

# 检索与格式化
results = rag.search("Xiaoming thinks the box is in the kitchen", top_k=3, category="Belief")
context = rag.format_context(results)  # 返回可直接注入 prompt 的字符串
print(context)
```


## 方法参数

### `__init__`

```python
ToMRAGv2(
    data_dir: str = "./data",
    index_dir: str = "./index",
    model_name: str = "./models/bge-m3",
    use_rewritten: bool = True,
)
```

- `data_dir`：JSONL 数据文件目录
- `index_dir`：FAISS 索引存储目录；`use_rewritten=True` 时自动变为 `{index_dir}_rewritten`
- `model_name`：嵌入模型路径（默认本地 `./models/bge-m3`）
- `use_rewritten`：`True`（默认）使用改写聚类数据；`False` 使用原始数据 + ATOMIC 关系过滤

### `build_index`

```python
build_index(force_rebuild: bool = False, num_samples: int = -1) -> None
```

- `force_rebuild`：是否强制重建索引，默认 `False`
- `num_samples`：每个数据源加载的样本数，默认 `-1`（全量）

### `search`

```python
search(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
) -> List[Dict]
```

- `query`：自然语言查询字符串
- `top_k`：每个数据源返回的结果数，默认 `5`
- `category`：ToM 任务类别（如 `"Belief"`、`"Emotion"`、`"Percept"` 等），用于自动路由数据源和过滤关系类型；部分类别直接返回 `[]`

返回 `List[Dict]`，每个元素包含 `content`、`source`、`category`、`title`、`id` 等字段。

### `format_context`

```python
format_context(results: List[Dict], max_length: int = 1500) -> str
```

- `results`：`search()` 的返回值
- `max_length`：输出字符串最大长度，默认 `1500`

返回格式化后的字符串，可直接注入 LLM prompt。
