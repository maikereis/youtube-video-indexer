# %%
import pandas as pd
from sentence_transformers import SentenceTransformer

# %%
data = pd.read_parquet("../data/transcripts.parquet", dtype_backend="pyarrow")
data = data.fillna("")

# %%
# Good trade-off between speed and accuracy
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# %%
text_vector = embedder.encode(
    data["text"].tolist(), show_progress_bar=True, batch_size=32
)

# %%
title_vector = embedder.encode(
    data["title"].tolist(), show_progress_bar=True, batch_size=32
)

# %%
data.loc[:, "text_embedding"] = pd.DataFrame({"a": list(text_vector)})
data.loc[:, "title_embedding"] = pd.DataFrame({"b": list(title_vector)})

# %%
data[
    [
        "id",
        "title_embedding",
        "text_embedding",
    ]
].to_parquet("../data/transcripts_with_embeddings.parquet", index=False)


