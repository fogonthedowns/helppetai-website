#!/usr/bin/env python3
"""
Pinecone Query Script - Terminal Interface
Query your Pinecone vector database using OpenAI embeddings

Usage:
    python query_pinecone.py "How do I treat dog bloat?"
    python query_pinecone.py --interactive
"""

import os
import argparse
import logging
from pinecone import Pinecone
import requests
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Configuration from your project
PINECONE_INDEX = "1536"  # Extracted from your URL (replace with your index name if needed)
OPENAI_EMBED_MODEL = "text-embedding-3-small"
DYNAMODB_VECTOR_TABLE = "rag_vector_index"
RAG_SOURCES_TABLE = "rag_content_sources"  # Table that stores source-level metadata (web_url, title, species, tags, etc.)

def load_environment():
    """Load environment variables with helpful error messages"""
    api_keys = {}

    # Pinecone API Key
    api_keys['pinecone'] = os.environ.get("PINECONE_API_KEY")
    if not api_keys['pinecone']:
        print("PINECONE_API_KEY not found in environment.")
        api_keys['pinecone'] = input("Enter your Pinecone API key: ").strip()

    # OpenAI API Key
    api_keys['openai'] = os.environ.get("OPENAI_API_KEY")
    if not api_keys['openai']:
        print("OPENAI_API_KEY not found in environment.")
        api_keys['openai'] = input("Enter your OpenAI API key: ").strip()

    return api_keys

def embed_text_openai(text, api_key):
    """Use OpenAI embedding API to embed a single text."""
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "input": text,
        "model": OPENAI_EMBED_MODEL
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]
    except requests.exceptions.RequestException as e:
        log.error(f"OpenAI API error: {e}")
        return None

def connect_to_pinecone(api_key):
    """Connect to your Pinecone index"""
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(PINECONE_INDEX)

        # Test connection by getting index stats (some Pinecone SDKs return different shapes; errors are handled)
        try:
            stats = index.describe_index_stats()
            # Some SDKs return dict; attempt to log whatever was returned
            if hasattr(stats, 'total_vector_count') and hasattr(stats, 'dimension'):
                log.info(f"Connected to Pinecone index '{PINECONE_INDEX}'")
                log.info(f"Index stats: {stats.total_vector_count} vectors, {stats.dimension} dimensions")
            else:
                log.info(f"Connected to Pinecone index '{PINECONE_INDEX}' (stats retrieved)")
        except Exception:
            # ignore stats errors, connection success is enough
            log.info(f"Connected to Pinecone index '{PINECONE_INDEX}' (stats not available)")

        return index
    except Exception as e:
        log.error(f"Failed to connect to Pinecone: {e}")
        return None

def connect_to_dynamodb():
    """Connect to DynamoDB to retrieve vector content"""
    try:
        dynamodb = boto3.resource('dynamodb')
        return dynamodb.Table(DYNAMODB_VECTOR_TABLE)
    except Exception as e:
        log.error(f"Failed to connect to DynamoDB (vectors table): {e}")
        return None

def connect_to_rag_sources_table():
    """Connect to the rag_sources DynamoDB table (source-level metadata)"""
    try:
        dynamodb = boto3.resource('dynamodb')
        return dynamodb.Table(RAG_SOURCES_TABLE)
    except Exception as e:
        log.error(f"Failed to connect to DynamoDB (rag_sources table): {e}")
        return None

def get_text_content_from_dynamodb(table, vector_ids):
    """Retrieve text content for multiple vector IDs from DynamoDB"""
    content_map = {}

    for vector_id in vector_ids:
        try:
            response = table.get_item(Key={'vector_id': vector_id})
            if 'Item' in response:
                item = response['Item']
                content_map[vector_id] = {
                    'chunk_content': item.get('chunk_content', ''),
                    'chunk_index': item.get('chunk_index', 0),
                    'source_id': item.get('source_id', ''),
                    'embed_model': item.get('embed_model', ''),
                    'last_indexed_at': item.get('last_indexed_at', ''),
                    'metadata': item.get('metadata', {})
                }
            else:
                log.warning(f"No content found for vector_id: {vector_id}")
                content_map[vector_id] = None
        except ClientError as e:
            log.error(f"Error retrieving {vector_id}: {e}")
            content_map[vector_id] = None

    return content_map

def get_source_metadata_from_dynamodb(table, source_id):
    """Fetch the source-level metadata (rag_sources table) for a given source_id"""
    if not table:
        return None
    try:
        resp = table.get_item(Key={'source_id': source_id})
        if 'Item' in resp:
            return resp['Item']
        else:
            log.debug(f"No source metadata found for source_id: {source_id}")
            return None
    except ClientError as e:
        log.error(f"Error fetching source metadata for {source_id}: {e}")
        return None
    except Exception as e:
        log.error(f"Unexpected error fetching source metadata for {source_id}: {e}")
        return None

def extract_source_fields(source_item):
    """
    Normalize and extract important fields from a rag_sources item.
    Returns a dict: {title, species (list), symptoms (list), web_url, publication_year, publisher, authority_level, summary}
    """
    if not source_item:
        return {
            "title": "Unknown",
            "species": [],
            "symptoms": [],
            "web_url": None,
            "publication_year": None,
            "publisher": None,
            "authority_level": None,
            "summary": None,
        }

    # Many of our useful fields are nested under 'metadata' in the example you gave
    md = source_item.get('metadata', {}) if isinstance(source_item, dict) else {}

    # title
    title = md.get('title') or source_item.get('title') or md.get('file_name') or "Unknown Title"

    # web_url
    web_url = md.get('web_url') or source_item.get('web_url') or md.get('url') or source_item.get('web_url')

    # species: look in multiple plausible places
    species = []
    cc = md.get('content_classification') or {}
    if isinstance(cc, dict):
        sp = cc.get('species')
        if sp:
            species = sp if isinstance(sp, list) else [sp]
    if not species:
        # fallback to top-level
        sp2 = md.get('species') or source_item.get('species')
        if sp2:
            species = sp2 if isinstance(sp2, list) else [sp2]

    # symptoms/subject tags
    symptoms = []
    st = md.get('subject_tags') or md.get('subject_tag') or cc.get('subject_tags') if isinstance(cc, dict) else None
    if st:
        symptoms = st if isinstance(st, list) else [st]

    # authority level / publisher / year / summary
    authority = md.get('authority_level') or source_item.get('authority_level') or cc.get('authority_level')
    publisher = md.get('publisher') or source_item.get('publisher')
    pub_year = md.get('publication_year') or source_item.get('publication_year')
    summary = md.get('summary') or source_item.get('summary')

    return {
        "title": title,
        "species": species,
        "symptoms": symptoms,
        "web_url": web_url,
        "publication_year": pub_year,
        "publisher": publisher,
        "authority_level": authority,
        "summary": summary
    }

def build_pinecone_filter(args):
    """Build Pinecone filter from CLI args"""
    filters = []

    if args.doc_type:
        filters.append({"doc_type": args.doc_type})
    if args.species:
        filters.append({"classification_species": {"$in": args.species}})
    if args.symptoms:
        filters.append({"classification_symptoms": {"$in": args.symptoms}})
    if args.medical_system:
        filters.append({"classification_medical_system": args.medical_system})
    if args.audience:
        filters.append({"classification_audience": args.audience})
    if args.source_id:
        filters.append({"source_id": args.source_id})
    if args.chunk_index is not None:
        filters.append({"chunk_index": args.chunk_index})
    if args.version:
        filters.append({"classification_version": args.version})

    return {"$and": filters} if filters else None

def query_pinecone(index, query_vector, top_k=5, include_metadata=True, filter=None):
    """Query Pinecone index with a vector"""
    try:
        return index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata
        )
    except Exception as e:
        log.error(f"Pinecone query failed: {e}")
        return None

def format_results(results, content_map=None, rag_table=None, show_summary=False):
    """Format search results for display with optional text content and source enrichment"""
    if not results or not getattr(results, 'matches', None):
        # Some Pinecone SDKs return dicts; handle both shapes
        if isinstance(results, dict) and not results.get('matches'):
            return "No results found."
        return "No results found."

    # unify matches list for either object or dict return types
    matches = results.matches if hasattr(results, 'matches') else results.get('matches', [])

    output = []
    output.append(f"\n🔍 Found {len(matches)} results:\n")
    output.append("=" * 80)

    # cache to avoid repeated source lookups
    source_meta_cache = {}

    for i, match in enumerate(matches, 1):
        # accommodate both attribute access and dict access for matches
        score = getattr(match, 'score', None) or match.get('score', 0.0)
        metadata = getattr(match, 'metadata', None) or match.get('metadata', {}) or {}
        vector_id = getattr(match, 'id', None) or match.get('id')

        output.append(f"\n📄 Result #{i} (Score: {score:.4f})")
        output.append("-" * 40)

        # The Pinecone vector metadata should contain the source/document id (source_id) in many setups.
        source_id = metadata.get('source_id') or metadata.get('document_id') or vector_id
        chunk_index = metadata.get('chunk_index', 'Unknown')
        doc_type = metadata.get('doc_type', metadata.get('document_type', 'Unknown'))

        output.append(f"Document ID: {source_id}")
        output.append(f"Chunk: #{chunk_index}")
        output.append(f"Type: {doc_type}")

        # Additional metadata from the vector (if present)
        if 'authority_level' in metadata:
            output.append(f"Authority: {metadata['authority_level']}")
        if 'classification_audience' in metadata:
            audience = metadata['classification_audience']
            audience_icon = "🐾" if audience == "pet-owner" else "🩺"
            output.append(f"Audience: {audience_icon} {audience}")
        if 'subject_tags' in metadata:
            tags = metadata['subject_tags']
            if isinstance(tags, list):
                tags = ', '.join(tags)
            output.append(f"Tags: {tags}")
        if 'page_number' in metadata:
            output.append(f"Page: {metadata['page_number']}")
        if 'section_title' in metadata:
            output.append(f"Section: {metadata['section_title']}")
        if 'word_range' in metadata:
            output.append(f"Word Range: {metadata['word_range']}")

        # Look up source-level metadata in rag_sources table using source_id
        source_info = None
        if source_id:
            if source_id in source_meta_cache:
                source_info = source_meta_cache[source_id]
            else:
                if rag_table:
                    item = get_source_metadata_from_dynamodb(rag_table, source_id)
                    parsed = extract_source_fields(item) if item else None
                    source_meta_cache[source_id] = parsed
                    source_info = parsed
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print(f"Source info: {source_info}")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

                else:
                    source_info = None

        if source_info:
            # Show title, species, symptoms, and URL
            output.append(f"Title: {source_info.get('title', 'Unknown')}")

            species = source_info.get('species') or []
            if isinstance(species, list):
                species = ', '.join(species)
            output.append(f"Classification Species: {species if species else 'N/A'}")

            symptoms = source_info.get('symptoms') or []
            if isinstance(symptoms, list):
                symptoms = ', '.join(symptoms)
            output.append(f"Symptoms: {symptoms if symptoms else 'N/A'}")

            publisher = source_info.get('publisher')
            if publisher:
                output.append(f"Publisher: {publisher}")

            pub_year = source_info.get('publication_year')
            if pub_year:
                output.append(f"Publication Year: {pub_year}")

            authority = source_info.get('authority_level')
            if authority:
                output.append(f"Authority Level: {authority}")

            web_url = source_info.get('web_url')
            if web_url:
                output.append(f"Source URL: {web_url}")
        else:
            output.append("Source metadata: N/A (rag_sources table not available or no entry)")

        # Add content based on display preference
        if show_summary and source_info and source_info.get('summary'):
            # Show document summary from rag_content_sources
            summary = source_info.get('summary', '')
            if summary:
                output.append(f"\n📄 Document Summary:")
                output.append("-" * 50)
                # Format summary nicely
                summary_lines = summary.replace('. ', '.\n').strip().split('\n')
                for line in summary_lines:
                    if line.strip():
                        output.append(f"  {line.strip()}")
                output.append("-" * 50)
        elif not show_summary and content_map and vector_id in content_map and content_map[vector_id]:
            # Show chunk content if available (from rag_vector_index) - default behavior
            content = content_map[vector_id]
            chunk_text = content.get('chunk_content', '')
            if chunk_text:
                output.append(f"\n📝 Content ({len(chunk_text)} chars):")
                output.append("-" * 50)
                lines = chunk_text.replace('\n\n', '\n').strip().split('\n')
                for line in lines:
                    if line.strip():
                        output.append(f"  {line.strip()}")
                output.append("-" * 50)

        output.append("")

    return "\n".join(output)


def search_knowledge_base(query_text, api_keys, top_k=5, include_text=True, show_summary=False, filter_obj=None):
    """Search pipeline: embed query -> search Pinecone -> get DynamoDB content -> format
    
    Args:
        show_summary: If True, show document summary instead of chunk content
    """
    print(f"\n🤔 Processing query: '{query_text}'")

    print("📝 Generating embedding...")
    query_vector = embed_text_openai(query_text, api_keys['openai'])
    if not query_vector:
        return "❌ Failed to generate embedding for query."

    print("🔌 Connecting to Pinecone...")
    index = connect_to_pinecone(api_keys['pinecone'])
    if not index:
        return "❌ Failed to connect to Pinecone."

    print("🔍 Searching knowledge base...")
    results = query_pinecone(index, query_vector, top_k=top_k, filter=filter_obj)
    if not results:
        return "❌ Search failed."

    content_map = None
    if include_text:
        print("📖 Retrieving text content (vector table)...")
        vec_table = connect_to_dynamodb()
        if vec_table:
            # gather vector ids from matches
            matches = results.matches if hasattr(results, 'matches') else results.get('matches', [])
            vector_ids = [getattr(m, 'id', None) or m.get('id') for m in matches]
            # filter None
            vector_ids = [vid for vid in vector_ids if vid]
            if vector_ids:
                content_map = get_text_content_from_dynamodb(vec_table, vector_ids)
        else:
            print("⚠️  Could not connect to DynamoDB vector table - showing metadata only")

    # connect to rag_sources table for source metadata enrichment
    rag_table = connect_to_rag_sources_table()

    return format_results(results, content_map, rag_table, show_summary)

def interactive_mode(api_keys, args):
    """Interactive query mode"""
    print("\n" + "=" * 60)
    print("🎯 INTERACTIVE PINECONE QUERY MODE")
    print("=" * 60)
    print("Enter your questions. Type 'quit' to exit.")
    if args.show_summary:
        print("📄 Summary mode: Showing document summaries instead of chunk content")
    
    filter_obj = build_pinecone_filter(args)
    
    if filter_obj and "$and" in filter_obj:
        filters = filter_obj["$and"]
        active_filters = []
        for f in filters:
            if "classification_audience" in f:
                audience = f["classification_audience"]
                icon = "🐾" if audience == "pet-owner" else "🩺"
                active_filters.append(f"audience={icon}{audience}")
            elif "classification_species" in f:
                species = f["classification_species"]["$in"] if isinstance(f["classification_species"], dict) else f["classification_species"]
                active_filters.append(f"species={species}")
        if active_filters:
            print(f"Active filters: {', '.join(active_filters)}")
    print("=" * 60)

    while True:
        try:
            query = input("\n💬 Your question: ").strip()
            if not query:
                continue
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            results = search_knowledge_base(query, api_keys, top_k=args.top_k, include_text=not args.no_text, show_summary=args.show_summary, filter_obj=filter_obj)
            print(results)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Query your Pinecone knowledge base")
    parser.add_argument("query", nargs='?', help="Search query text")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--no-text", action="store_true", help="Show only metadata, no text content")
    parser.add_argument("--show-summary", action="store_true", help="Show document summary instead of full chunk content")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Filtering arguments
    parser.add_argument("--doc-type", help="Filter by document type")
    parser.add_argument("--species", nargs='+', help="Filter by species (list)")
    parser.add_argument("--symptoms", nargs='+', help="Filter by symptoms (list)")
    parser.add_argument("--medical-system", help="Filter by medical system")
    parser.add_argument("--audience", choices=["expert", "pet-owner"], help="Filter by audience type (expert or pet-owner)")
    parser.add_argument("--source-id", help="Filter by source ID")
    parser.add_argument("--chunk-index", type=int, help="Filter by chunk index")
    parser.add_argument("--version", help="Filter by classification version")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        api_keys = load_environment()
    except KeyboardInterrupt:
        print("\n👋 Cancelled.")
        return

    filter_obj = build_pinecone_filter(args)

    if args.interactive:
        interactive_mode(api_keys, args)
    elif args.query:
        include_text = not args.no_text
        results = search_knowledge_base(args.query, api_keys, top_k=args.top_k, include_text=include_text, show_summary=args.show_summary, filter_obj=filter_obj)
        print(results)
    else:
        print("❌ Please provide a query or use --interactive mode")
        parser.print_help()

if __name__ == "__main__":
    main()


# python src/scripts/query_pinecone.py "treatment for diarrhea" \                                                             ✔  helppetai-lambda   system   10:03:03 PM 
#   --doc-type PDF \
#   --species dog \
#   --symptoms diarrhea fever \
#   --medical-system digestive \
#   --audience pet-owner
#
# python query_pinecone.py "equine colic diagnosis" --audience expert --species horse
#
# python query_pinecone.py --interactive --audience pet-owner
#
# python query_pinecone.py "dog bloat treatment" --show-summary --audience pet-owner