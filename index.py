import os
import argparse

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.schema import Document
from llama_index.core import Settings

from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec

from dotenv import load_dotenv
load_dotenv()


def get_pinecone_client() -> Pinecone:
    """
    Create a Pinecone client object.

    Returns:
    Pinecone: The Pinecone client object.
    """
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def create_pinecone_index(pc_client: Pinecone, index_name: str, dimensions: int) -> Pinecone.Index:
    """
    Create an index in Pinecone if it doesn't exist.

    Args:

    pc_client (Pinecone): The Pinecone client.
    index_name (str): The name of the index.
    dimensions (int): The dimension of the index.
    """
    index_names = [index["name"] for index in pc_client.list_indexes()]
    if index_name not in index_names:
        pc_client.create_index(
            name=index_name,
            dimension=dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"Index {index_name} created.")
    else:
        print(f"Index {index_name} already exists.")

    index = pc_client.Index(name=index_name)
    return index


def read_documents(docs_path: str) -> list[Document]:
    """
    Read documents from the docs_path.

    Args:

    docs_path (str): The path to the directory containing the documents.

    Returns:
    list: A list of documents.
    """
    reader = SimpleDirectoryReader(input_dir=docs_path, recursive=True)
    documents = reader.load_data()
    return documents


def create_index(pc_index: Pinecone.Index, documents: list[Document]):
    """
    Index the documents in Pinecone.

    Args:

    pc_index (Pinecone.Index): The Pinecone index.
    documents (list): A list of documents.
    """
    vector_store = PineconeVectorStore(pc_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context
    )
    return index


def load_index(index_name: str) -> VectorStoreIndex:
    """
    Load the index from the existing vector store.

    Args:

    pc_index (Pinecone.Index): The Pinecone index.

    Returns:
    VectorStoreIndex: The index loaded from the existing vector store.
    """
    pc = get_pinecone_client()
    pc_index = pc.Index(name=index_name)
    vector_store = PineconeVectorStore(pc_index)
    return VectorStoreIndex.from_vector_store(vector_store)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str,
                        help="The path to the data directory.")
    parser.add_argument("--pinecone-index", type=str,
                        help="The name of the Pinecone index.")
    parser.add_argument("--embedding-model", type=str,
                        choices=[
                            "text-embedding-ada-002",
                            "text-embedding-3-small",
                            "text-embedding-3-large"],
                        default="text-embedding-3-large",
                        help="Name of the OpenAI embedding model")
    args = parser.parse_args()
    args.data_path = 'data'
    args.pinecone_index = 'nlp-course'
    Settings.embed_model = OpenAIEmbedding(model=args.embedding_model)

    MODEL_TO_DIMENSIONS = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    pc = get_pinecone_client()

    pc_index = create_pinecone_index(pc,
                                     args.pinecone_index,
                                     MODEL_TO_DIMENSIONS[args.embedding_model])
    documents = read_documents(args.data_path)
    index = create_index(pc_index, documents)

    total_vector_count = pc_index.describe_index_stats()['namespaces']['']['vector_count']

    if index and total_vector_count == len(documents):
        print("Indexing successful.")
    else:
        raise Exception("Indexing failed.")
