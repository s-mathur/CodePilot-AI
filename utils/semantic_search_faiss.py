import numpy as np
import faiss


class SemanticSearchFAISS:
    def __init__(self):
        self.index = None
        self.metadata = []

    def create_index(self, dimension):
        self.index = faiss.IndexFlatL2(dimension)

    def add_vector(self, vector, metadata):
        vector = np.array([vector]).astype("float32")
        self.index.add(vector)
        self.metadata.append(metadata)

    def search(self, vector, top_k=5):
        vector = np.array([vector]).astype("float32")
        distances, indices = self.index.search(vector, top_k)
        results = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results