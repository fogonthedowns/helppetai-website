"""
RAG Service for question answering with source attribution.
Integrates Pinecone vector search with OpenAI for contextual responses.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError
from openai import AsyncOpenAI
from pinecone import Pinecone

from ..config import settings
from ..schemas.base import RAGQueryRequest, RAGResponse, SourceReference

logger = logging.getLogger(__name__)


class RAGService:
    """Service for handling RAG (Retrieval-Augmented Generation) operations."""
    
    def __init__(self):
        """Initialize the RAG service with required clients."""
        self._pinecone_client = None
        self._pinecone_index = None
        self._openai_client = None
        self._dynamodb_resource = None
        self._vector_table = None
        self._sources_table = None
        
    async def _get_pinecone_client(self):
        """Lazy initialization of Pinecone client."""
        if self._pinecone_client is None:
            if not settings.pinecone_api_key:
                raise ValueError("PINECONE_API_KEY is required for RAG functionality")
            
            self._pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
            self._pinecone_index = self._pinecone_client.Index(settings.pinecone_index_name)
            logger.info(f"Connected to Pinecone index: {settings.pinecone_index_name}")
            
        return self._pinecone_index
    
    async def _get_openai_client(self):
        """Lazy initialization of OpenAI client."""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for RAG functionality")
            
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("Connected to OpenAI API")
            
        return self._openai_client
    
    def _get_dynamodb_tables(self):
        """Lazy initialization of DynamoDB tables."""
        if self._dynamodb_resource is None:
            # Use default AWS configuration like the CLI script
            self._dynamodb_resource = boto3.resource('dynamodb')
            self._vector_table = self._dynamodb_resource.Table(settings.dynamodb_vector_table)
            self._sources_table = self._dynamodb_resource.Table(settings.rag_sources_table)
            logger.info("Connected to DynamoDB tables")
        
        return self._vector_table, self._sources_table
    
    async def _embed_text(self, text: str) -> List[float]:
        """Generate embedding for the given text using OpenAI."""
        try:
            openai_client = await self._get_openai_client()
            response = await openai_client.embeddings.create(
                input=text,
                model=settings.openai_embed_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def _build_pinecone_filter(self, request: RAGQueryRequest) -> Optional[Dict]:
        """Build Pinecone filter from request parameters (matching query_pinecone.py)."""
        filters = []
        
        if request.doc_type:
            filters.append({"doc_type": request.doc_type})
        if request.species:
            filters.append({"classification_species": {"$in": request.species}})
        if request.symptoms:
            filters.append({"classification_symptoms": {"$in": request.symptoms}})
        if request.medical_system:
            filters.append({"classification_medical_system": request.medical_system})
        if request.audience:
            filters.append({"classification_audience": request.audience})
        if request.source_id:
            filters.append({"source_id": request.source_id})
        if request.chunk_index is not None:
            filters.append({"chunk_index": request.chunk_index})
        if request.version:
            filters.append({"classification_version": request.version})
        
        return {"$and": filters} if filters else None
    
    async def _query_pinecone(
        self, 
        query_vector: List[float], 
        max_results: int,
        filter_obj: Optional[Dict] = None
    ) -> List[Dict]:
        """Query Pinecone with the given vector."""
        try:
            index = await self._get_pinecone_client()
            
            results = index.query(
                vector=query_vector,
                top_k=max_results,
                filter=filter_obj,
                include_metadata=True
            )
            
            # Handle both object and dict return types from Pinecone
            matches = results.matches if hasattr(results, 'matches') else results.get('matches', [])
            
            formatted_results = []
            for match in matches:
                score = getattr(match, 'score', None) or match.get('score', 0.0)
                metadata = getattr(match, 'metadata', None) or match.get('metadata', {})
                vector_id = getattr(match, 'id', None) or match.get('id')
                
                formatted_results.append({
                    'id': vector_id,
                    'score': score,
                    'metadata': metadata
                })
            
            logger.info(f"Retrieved {len(formatted_results)} results from Pinecone")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            raise
    
    def _get_text_content_from_dynamodb(self, vector_ids: List[str]) -> Dict[str, Dict]:
        """Retrieve text content for multiple vector IDs from DynamoDB."""
        vector_table, _ = self._get_dynamodb_tables()
        content_map = {}
        successful_retrievals = 0
        
        for vector_id in vector_ids:
            try:
                # Try the vector_id as-is first
                response = vector_table.get_item(Key={'vector_id': vector_id})
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
                    successful_retrievals += 1
                else:
                    logger.debug(f"No content found for vector_id: {vector_id}")
                    content_map[vector_id] = None
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.debug(f"DynamoDB table or item not found for {vector_id}")
                else:
                    logger.error(f"DynamoDB error retrieving {vector_id}: {e}")
                content_map[vector_id] = None
            except Exception as e:
                logger.error(f"Unexpected error retrieving {vector_id}: {e}")
                content_map[vector_id] = None
        
        logger.info(f"Successfully retrieved content for {successful_retrievals}/{len(vector_ids)} vectors")
        return content_map
    
    def _get_source_metadata_from_dynamodb(self, source_id: str) -> Optional[Dict]:
        """Fetch source-level metadata from DynamoDB."""
        try:
            _, sources_table = self._get_dynamodb_tables()
            resp = sources_table.get_item(Key={'source_id': source_id})
            if 'Item' in resp:
                return resp['Item']
            else:
                logger.debug(f"No source metadata found for source_id: {source_id}")
                return None
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.debug(f"DynamoDB sources table or item not found for {source_id}")
            else:
                logger.error(f"DynamoDB error fetching source metadata for {source_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching source metadata for {source_id}: {e}")
            return None
    
    def _extract_source_fields(self, source_item: Optional[Dict]) -> Dict[str, Any]:
        """Extract and normalize important fields from a rag_sources item."""
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
        
        md = source_item.get('metadata', {}) if isinstance(source_item, dict) else {}
        
        # Extract title
        title = md.get('title') or source_item.get('title') or md.get('file_name') or "Unknown Title"
        
        # Extract web_url
        web_url = md.get('web_url') or source_item.get('web_url') or md.get('url')
        
        # Extract species
        species = []
        cc = md.get('content_classification') or {}
        if isinstance(cc, dict):
            sp = cc.get('species')
            if sp:
                species = sp if isinstance(sp, list) else [sp]
        if not species:
            sp2 = md.get('species') or source_item.get('species')
            if sp2:
                species = sp2 if isinstance(sp2, list) else [sp2]
        
        # Extract symptoms/subject tags
        symptoms = []
        st = md.get('subject_tags') or md.get('subject_tag') or (cc.get('subject_tags') if isinstance(cc, dict) else None)
        if st:
            symptoms = st if isinstance(st, list) else [st]
        
        # Extract other metadata
        authority = md.get('authority_level') or source_item.get('authority_level') or (cc.get('authority_level') if isinstance(cc, dict) else None)
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
    
    def _format_sources(self, pinecone_results: List[Dict], content_map: Dict[str, Dict]) -> List[SourceReference]:
        """Convert Pinecone results to structured source references."""
        sources = []
        source_meta_cache = {}
        
        for result in pinecone_results:
            vector_id = result['id']
            metadata = result['metadata']
            score = result['score']
            
            # Get source ID and chunk info
            source_id = metadata.get('source_id') or metadata.get('document_id') or vector_id
            chunk_index = metadata.get('chunk_index', 'Unknown')
            
            # Get source metadata
            if source_id not in source_meta_cache:
                source_item = self._get_source_metadata_from_dynamodb(source_id)
                source_meta_cache[source_id] = self._extract_source_fields(source_item)
            
            source_info = source_meta_cache[source_id]
            
            source_ref = SourceReference(
                id=source_id,
                title=source_info.get('title', 'Unknown'),
                url=source_info.get('web_url'),
                chunk_info=f"Chunk: #{chunk_index}",
                relevance_score=score,
                audience=metadata.get('classification_audience'),
                authority_level=source_info.get('authority_level'),
                publisher=source_info.get('publisher'),
                publication_year=source_info.get('publication_year'),
                species=source_info.get('species'),
                symptoms=source_info.get('symptoms')
            )
            
            sources.append(source_ref)
        
        return sources
    
    async def _generate_response(
        self, 
        question: str, 
        context_docs: List[Dict], 
        content_map: Dict[str, Dict]
    ) -> str:
        """Generate AI response using OpenAI with retrieved context."""
        try:
            openai_client = await self._get_openai_client()
            
            # Build context from retrieved documents
            context_parts = []
            for i, doc in enumerate(context_docs, 1):
                vector_id = doc['id']
                content = content_map.get(vector_id, {})
                chunk_content = content.get('chunk_content', '') if content else ''
                
                if chunk_content:
                    # Get source metadata for better context
                    source_id = doc['metadata'].get('source_id', 'Unknown')
                    title = "Unknown"
                    
                    # Try to get title from source metadata
                    source_item = self._get_source_metadata_from_dynamodb(source_id)
                    if source_item:
                        source_info = self._extract_source_fields(source_item)
                        title = source_info.get('title', 'Unknown')
                    
                    context_parts.append(f"[Document {i}] Title: {title}\nContent: {chunk_content}")
            
            context_text = "\n\n".join(context_parts)
            
            # Create the prompt
            system_prompt = """You are an expert veterinary assistant with deep knowledge of animal health and medical care. Your role is to provide accurate, helpful, and well-sourced answers to questions about pet health, veterinary medicine, and animal care.

Instructions:
- Answer the user's question based ONLY on the provided context documents
- Use numbered references [1], [2], etc. to cite specific documents in your response
- Provide comprehensive, accurate answers that are practical and actionable
- If the context doesn't contain sufficient information to fully answer the question, clearly state what information is missing
- Focus on evidence-based information and best practices
- When discussing medical conditions or treatments, emphasize the importance of professional veterinary consultation
- Use clear, accessible language appropriate for pet owners while maintaining medical accuracy"""

            user_prompt = f"""Context Documents:
{context_text}

User Question: {question}

Please provide a comprehensive answer to the user's question based on the provided context documents. Use numbered citations [1], [2], etc. to reference specific documents."""

            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for expert system - consistent, factual responses
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    async def process_rag_query(self, request: RAGQueryRequest) -> RAGResponse:
        """Main RAG processing pipeline."""
        start_time = time.time()
        
        try:
            logger.info(f"Processing RAG query: {request.question[:100]}...")
            
            # Step 1: Generate embedding for the question
            query_vector = await self._embed_text(request.question)
            
            # Step 2: Build filter from request parameters
            filter_obj = self._build_pinecone_filter(request)
            if filter_obj:
                logger.info(f"Applying filters: {filter_obj}")
            
            # Step 3: Query Pinecone for relevant documents
            pinecone_results = await self._query_pinecone(
                query_vector=query_vector,
                max_results=request.max_results,
                filter_obj=filter_obj
            )
            
            if not pinecone_results:
                return RAGResponse(
                    answer="I couldn't find any relevant information to answer your question. Please try rephrasing your question or asking about a different topic.",
                    sources=[],
                    query_metadata={
                        "processing_time_seconds": time.time() - start_time,
                        "pinecone_results_count": 0,
                        "question": request.question,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            # Step 4: Get text content from DynamoDB
            vector_ids = [result['id'] for result in pinecone_results]
            content_map = self._get_text_content_from_dynamodb(vector_ids)
            
            # Check if we have any actual content (for logging only)
            available_content = sum(1 for content in content_map.values() if content and content.get('chunk_content'))
            logger.info(f"Retrieved content for {available_content}/{len(vector_ids)} vectors")
            
            # Step 5: Generate AI response (continue even if no content, like CLI script)
            answer = await self._generate_response(
                question=request.question,
                context_docs=pinecone_results,
                content_map=content_map
            )
            
            # Step 6: Format sources
            sources = self._format_sources(pinecone_results, content_map)
            
            # Step 7: Build metadata
            query_metadata = {
                "processing_time_seconds": time.time() - start_time,
                "pinecone_results_count": len(pinecone_results),
                "sources_count": len(sources),
                "available_content_count": available_content,
                "question": request.question,
                "timestamp": datetime.utcnow().isoformat(),
                "openai_model": "gpt-4o-mini",
                "openai_temperature": 0.1,  # Fixed low temperature for expert system
                "embedding_model": settings.openai_embed_model,
                "pinecone_index": settings.pinecone_index_name,
                "filters_applied": filter_obj is not None,
                "filter_details": filter_obj if filter_obj else {},
                "status": "success"
            }
            
            logger.info(f"RAG query processed successfully in {query_metadata['processing_time_seconds']:.2f}s")
            
            return RAGResponse(
                answer=answer,
                sources=sources,
                query_metadata=query_metadata
            )
            
        except Exception as e:
            logger.error(f"RAG query processing failed: {e}")
            raise
