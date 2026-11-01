"""Retrieval eval: recall@k, precision@k and MRR for several chunk sizes. Local only, no API cost.

Each question has a gold phrase from the source docs; a retrieved chunk counts as relevant
if it contains that phrase. Questions are paraphrased so they can't match on wording alone.

    .venv/bin/python rag_eval.py
"""
import json

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

import rag  # noqa: F401  (sets the same local embedding model)

EVAL = [(c["question"], c["gold_phrase"]) for c in json.load(open("evals/planted_defects.json"))["cases"]]

K = 3


def score(chunk_size: int, overlap: int):
    docs = SimpleDirectoryReader("docs", recursive=True).load_data()
    nodes = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=overlap).get_nodes_from_documents(docs)
    retriever = VectorStoreIndex(nodes).as_retriever(similarity_top_k=K)
    recall = precision = rr = 0.0
    misses = []
    for question, gold in EVAL:
        hits = retriever.retrieve(question)
        relevant = [gold in h.get_content() for h in hits]
        recall += any(relevant)                     # one gold chunk per question, so recall@k = hit rate
        precision += sum(relevant) / K
        rr += next((1 / (i + 1) for i, r in enumerate(relevant) if r), 0)
        if not any(relevant):
            misses.append(question)
    n = len(EVAL)
    return len(nodes), recall / n, precision / n, rr / n, misses


if __name__ == "__main__":
    print(f"{len(EVAL)} questions, k={K}\n")
    print(f"{'chunk/overlap':>14} {'chunks':>7} {'recall@3':>9} {'precision@3':>12} {'MRR':>6}")
    for size, overlap in [(256, 32), (96, 16), (48, 8)]:
        n_chunks, r, p, mrr, misses = score(size, overlap)
        print(f"{f'{size}/{overlap}':>14} {n_chunks:>7} {r:>9.2f} {p:>12.2f} {mrr:>6.2f}")
        for q in misses:
            print(f"{'':>16}missed: {q}")
