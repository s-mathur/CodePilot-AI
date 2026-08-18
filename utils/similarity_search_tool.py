from utils.embedding_model import EmbeddingModel

from tools.semantic_search_faiss import SemanticSearchFAISS


class SimilaritySearch:
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.faiss_manager = SemanticSearchFAISS()

    def build_index(self, chunks):
        if not chunks:
            return

        sample_vector = self.embedding_model.generate_embedding(chunks[0]["content"])

        self.faiss_manager.create_index(len(sample_vector))

        for chunk in chunks:
            vector = self.embedding_model.generate_embedding(chunk["content"])
            self.faiss_manager.add_vector(vector, chunk)

    def search(self, query, top_k=5):
        query_vector = self.embedding_model.generate_embedding(query)

        return self.faiss_manager.search(query_vector, top_k)
