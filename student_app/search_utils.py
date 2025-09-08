"""
Enhanced Search Utilities for Django Student Portal
==================================================

This module implements advanced search algorithms using TF-IDF and Cosine Similarity
for academic resource search functionality.

Algorithms Implemented:
1. TF-IDF (Term Frequency-Inverse Document Frequency)
2. Cosine Similarity for document ranking
3. Text preprocessing and normalization

Author: Student Portal Development Team
Purpose: Final Year Project - Enhanced Search System
"""

import re
import math
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Download required NLTK data (only once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class EnhancedSearchEngine:
    """
    Advanced search engine using TF-IDF and Cosine Similarity
    
    This class implements:
    - Text preprocessing and normalization
    - TF-IDF vectorization
    - Cosine similarity calculation
    - Result ranking and grouping
    """
    
    def __init__(self):
        """Initialize the search engine with preprocessing tools"""
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit vocabulary size for performance
            stop_words='english',
            ngram_range=(1, 2),  # Include both unigrams and bigrams
            min_df=1,  # Minimum document frequency
            max_df=0.95,  # Maximum document frequency (ignore very common words)
            lowercase=True,
            strip_accents='unicode'
        )
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better search results
        
        Steps:
        1. Convert to lowercase
        2. Remove special characters and numbers
        3. Remove stop words
        4. Apply stemming
        
        Args:
            text (str): Raw text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers, keep only letters and spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize and remove stop words
        words = text.split()
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Apply stemming
        words = [self.stemmer.stem(word) for word in words]
        
        return ' '.join(words)
    
    def extract_document_text(self, resource) -> str:
        """
        Extract and combine all searchable text from a resource
        
        Args:
            resource: Django model instance (Note, Syllabus, QuestionBank, etc.)
            
        Returns:
            str: Combined searchable text
        """
        text_parts = []
        
        # Add title (weighted more heavily)
        if hasattr(resource, 'title') and resource.title:
            text_parts.append(resource.title)
            text_parts.append(resource.title)  # Double weight for title
        
        # Add description
        if hasattr(resource, 'description') and resource.description:
            text_parts.append(resource.description)
        
        # Add content (for syllabus)
        if hasattr(resource, 'content') and resource.content:
            text_parts.append(resource.content)
        
        # Add subject name for context
        if hasattr(resource, 'subject') and resource.subject:
            text_parts.append(resource.subject.name)
            if hasattr(resource.subject, 'faculty') and resource.subject.faculty:
                text_parts.append(resource.subject.faculty.name)
        
        return ' '.join(text_parts)
    
    def calculate_tf_idf_scores(self, query: str, documents: List[Any]) -> List[Tuple[Any, float]]:
        """
        Calculate TF-IDF scores for documents against a query
        
        TF-IDF Formula:
        TF(t,d) = (Number of times term t appears in document d) / (Total number of terms in document d)
        IDF(t) = log(Total number of documents / Number of documents containing term t)
        TF-IDF(t,d) = TF(t,d) * IDF(t)
        
        Args:
            query (str): Search query
            documents (List[Any]): List of document objects
            
        Returns:
            List[Tuple[Any, float]]: List of (document, score) tuples sorted by score
        """
        if not query or not documents:
            return []
        
        # Preprocess query
        processed_query = self.preprocess_text(query)
        
        # Extract and preprocess document texts
        doc_texts = []
        for doc in documents:
            raw_text = self.extract_document_text(doc)
            processed_text = self.preprocess_text(raw_text)
            doc_texts.append(processed_text)
        
        # Add query to corpus for vectorization
        corpus = [processed_query] + doc_texts
        
        try:
            # Create TF-IDF matrix
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity between query and documents
            # Query is at index 0, documents start from index 1
            query_vector = tfidf_matrix[0:1]
            doc_vectors = tfidf_matrix[1:]
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            # Create results with scores
            results = []
            for i, doc in enumerate(documents):
                if similarities[i] > 0:  # Only include documents with some similarity
                    results.append((doc, similarities[i]))
            
            # Sort by similarity score (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results
            
        except Exception as e:
            # Fallback to simple text matching if TF-IDF fails
            print(f"TF-IDF calculation failed: {e}")
            return self._fallback_search(query, documents)
    
    def _fallback_search(self, query: str, documents: List[Any]) -> List[Tuple[Any, float]]:
        """
        Fallback search method using simple text matching
        
        Args:
            query (str): Search query
            documents (List[Any]): List of document objects
            
        Returns:
            List[Tuple[Any, float]]: List of (document, score) tuples
        """
        query_lower = query.lower()
        results = []
        
        for doc in documents:
            score = 0
            raw_text = self.extract_document_text(doc)
            text_lower = raw_text.lower()
            
            # Simple scoring based on query term frequency
            query_terms = query_lower.split()
            for term in query_terms:
                if term in text_lower:
                    # Higher score for title matches
                    if hasattr(doc, 'title') and term in doc.title.lower():
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                results.append((doc, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def search_resources(self, query: str, resources: List[Any], limit: int = 10) -> Dict[str, List[Any]]:
        """
        Search and rank resources by relevance
        
        Args:
            query (str): Search query
            resources (List[Any]): List of resource objects
            limit (int): Maximum number of results per category
            
        Returns:
            Dict[str, List[Any]]: Dictionary with resource types as keys and ranked results as values
        """
        if not query or not resources:
            return {'notes': [], 'syllabi': [], 'question_banks': [], 'notices': []}
        
        # Calculate TF-IDF scores
        scored_results = self.calculate_tf_idf_scores(query, resources)
        
        # Group results by resource type
        grouped_results = {
            'notes': [],
            'syllabi': [],
            'question_banks': [],
            'notices': []
        }
        
        for resource, score in scored_results:
            resource_type = self._get_resource_type(resource)
            if resource_type in grouped_results:
                grouped_results[resource_type].append(resource)
        
        # Limit results per category
        for resource_type in grouped_results:
            grouped_results[resource_type] = grouped_results[resource_type][:limit]
        
        return grouped_results
    
    def _get_resource_type(self, resource) -> str:
        """
        Determine the resource type based on the model class
        
        Args:
            resource: Django model instance
            
        Returns:
            str: Resource type string
        """
        model_name = resource.__class__.__name__.lower()
        
        if 'note' in model_name:
            return 'notes'
        elif 'syllabus' in model_name:
            return 'syllabi'
        elif 'question' in model_name or 'bank' in model_name:
            return 'question_banks'
        elif 'notice' in model_name:
            return 'notices'
        else:
            return 'notes'  # Default fallback


# Global search engine instance
search_engine = EnhancedSearchEngine()


def perform_enhanced_search(query: str, all_resources: List[Any], limit: int = 10) -> Dict[str, List[Any]]:
    """
    Convenience function to perform enhanced search
    
    Args:
        query (str): Search query
        all_resources (List[Any]): List of all resources to search
        limit (int): Maximum results per category
        
    Returns:
        Dict[str, List[Any]]: Grouped and ranked search results
    """
    return search_engine.search_resources(query, all_resources, limit)


def get_search_statistics(query: str, results: Dict[str, List[Any]]) -> Dict[str, int]:
    """
    Get search statistics for display
    
    Args:
        query (str): Search query
        results (Dict[str, List[Any]]): Search results
        
    Returns:
        Dict[str, int]: Statistics dictionary
    """
    total_results = sum(len(resource_list) for resource_list in results.values())
    
    return {
        'query': query,
        'total_results': total_results,
        'notes_count': len(results.get('notes', [])),
        'syllabi_count': len(results.get('syllabi', [])),
        'question_banks_count': len(results.get('question_banks', [])),
        'notices_count': len(results.get('notices', []))
    }


def get_tfidf_similarity(text1: str, text2: str) -> float:
    """
    Calculate TF-IDF based cosine similarity between two text strings.
    
    Args:
        text1 (str): First text string
        text2 (str): Second text string
        
    Returns:
        float: Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    try:
        # Preprocess texts
        processed_text1 = search_engine.preprocess_text(text1)
        processed_text2 = search_engine.preprocess_text(text2)
        
        if not processed_text1 or not processed_text2:
            return 0.0
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Fit and transform the texts
        tfidf_matrix = vectorizer.fit_transform([processed_text1, processed_text2])
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return float(similarity)
        
    except Exception as e:
        # If any error occurs, return 0 similarity
        print(f"Error calculating similarity: {e}")
        return 0.0
