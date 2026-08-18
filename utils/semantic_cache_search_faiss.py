import numpy as np
import faiss
import os


class SemanticCacheFAISS:

    def __init__(self, index_file):
        self.index_file = index_file
        self.index = None
        self._load()

    def _load(self):
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)

    def create_index(self, dimension):
        self.index = faiss.IndexFlatIP(dimension)

    @staticmethod
    def _prepare_vector(vector):
        vector = np.asarray(vector, dtype="float32")

        if vector.ndim == 1:
            vector = vector.reshape(1, -1)

        faiss.normalize_L2(vector)

        return vector

    def add_vector(self, vector):

        vector = self._prepare_vector(vector)

        if self.index is None:

            self.create_index(vector.shape[1])

        self.index.add(vector)

        self.save()

        return self.index.ntotal - 1

    def search(self, vector, top_k=5):

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        vector = self._prepare_vector(vector)

        top_k = min(top_k, self.index.ntotal)

        scores, indices = self.index.search(vector, top_k)

        results = []

        for score, index in zip(scores[0], indices[0]):

            if index < 0:
                continue

            results.append({
                "index": int(index),
                "score": float(score)
            })

        return results

    def save(self):

        if self.index is not None:
            os.makedirs(os.path.dirname(self.index_file), exist_ok=True)

            faiss.write_index(self.index, self.index_file)

    def size(self):

        if self.index is None:
            return 0

        return self.index.ntotal