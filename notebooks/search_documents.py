# %%
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import DistanceMetric

# %%
data = pd.read_parquet("../data/transcripts_with_embeddings.parquet")

# %%
model = SentenceTransformer("all-MiniLM-L6-v2")

# %%
empty_string = model.encode("")

# %%
def search_embeddings(
    query: str,
    model: SentenceTransformer,
    df: pd.DataFrame,
    id_column: str,
    embedding_column: str,
    metric: str = "euclidean",
    top_k: int = 5,
) -> pd.DataFrame:

    # Embed the query
    query_embedding = model.encode(query).reshape(1, -1)

    dist = DistanceMetric.get_metric(metric)

    # Calculate cosine similarity
    cosine_scores = df[embedding_column].apply(
        lambda x: dist.pairwise(query_embedding, x.reshape(1, -1))[0][0]
    )

    return data.iloc[cosine_scores.nsmallest(5).index]["id"]

# %%
scores = search_embeddings("How to use redis", model, data, "id", "text_embedding")

# %%
scores


