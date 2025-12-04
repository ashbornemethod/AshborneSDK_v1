"""
Similarity computation helpers for clone detection.
"""

import hashlib
import re
from typing import Dict, List, Set


def compute_sha256(content: bytes) -> str:
    """
    Compute SHA-256 hash of content.
    
    Args:
        content: Bytes to hash
        
    Returns:
        Hex digest of SHA-256 hash
    """
    return hashlib.sha256(content).hexdigest()


def compute_similarity_score(
    canonical_signatures: Dict[str, Dict],
    matched_files: List[Dict]
) -> float:
    """
    Compute similarity score between canonical signatures and matched files.
    
    Score is based on:
    - Percentage of canonical files that have exact hash matches (70% weight)
    - Filename match weight (30% weight)
    
    Args:
        canonical_signatures: Dict of canonical file signatures
        matched_files: List of matched file data with sha_match and paths
        
    Returns:
        Similarity score from 0-100
    """
    if not canonical_signatures:
        return 0.0
    
    # Count exact hash matches
    exact_matches = sum(1 for f in matched_files if f.get('sha_match', False))
    
    # Count filename matches (even without hash match)
    filename_matches = len(matched_files)
    
    # Calculate weighted score
    total_canonical = len(canonical_signatures)
    hash_match_score = (exact_matches / total_canonical) * 70
    filename_match_score = min((filename_matches / total_canonical) * 30, 30)
    
    score = hash_match_score + filename_match_score
    return min(score, 100.0)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing whitespace and lowercasing.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    return re.sub(r'\s+', ' ', text.lower().strip())


def tokenize(text: str) -> Set[str]:
    """
    Tokenize text into words.
    
    Args:
        text: Text to tokenize
        
    Returns:
        Set of tokens
    """
    return set(re.findall(r'\w+', text.lower()))


def create_shingles(text: str, k: int = 3) -> Set[str]:
    """
    Create k-length word shingles from text.
    
    Args:
        text: Text to shingle
        k: Shingle size (number of words)
        
    Returns:
        Set of shingles
    """
    words = text.lower().split()
    shingles = set()
    
    for i in range(len(words) - k + 1):
        shingle = ' '.join(words[i:i+k])
        shingles.add(shingle)
    
    return shingles


def readme_fingerprint_similarity(readme1: str, readme2: str) -> float:
    """
    Compare two README contents using token overlap and shingling.
    
    Args:
        readme1: First README content
        readme2: Second README content
        
    Returns:
        Similarity score from 0.0 to 1.0
    """
    if not readme1 or not readme2:
        return 0.0
    
    # Normalize
    norm1 = normalize_text(readme1)
    norm2 = normalize_text(readme2)
    
    # Token-based Jaccard similarity
    tokens1 = tokenize(norm1)
    tokens2 = tokenize(norm2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    token_intersection = tokens1.intersection(tokens2)
    token_union = tokens1.union(tokens2)
    token_similarity = len(token_intersection) / len(token_union)
    
    # Shingle-based similarity
    shingles1 = create_shingles(norm1, k=3)
    shingles2 = create_shingles(norm2, k=3)
    
    if not shingles1 or not shingles2:
        shingle_similarity = 0.0
    else:
        shingle_intersection = shingles1.intersection(shingles2)
        shingle_union = shingles1.union(shingles2)
        shingle_similarity = len(shingle_intersection) / len(shingle_union)
    
    # Weighted average (60% tokens, 40% shingles)
    return 0.6 * token_similarity + 0.4 * shingle_similarity


def levenshtein_ratio(s1: str, s2: str) -> float:
    """
    Compute normalized Levenshtein similarity ratio.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity ratio from 0.0 to 1.0
    """
    s1 = s1.lower()
    s2 = s2.lower()
    
    if s1 == s2:
        return 1.0
    
    len1 = len(s1)
    len2 = len(s2)
    
    if len1 == 0 or len2 == 0:
        return 0.0
    
    # Create distance matrix
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )
    
    distance = matrix[len1][len2]
    max_len = max(len1, len2)
    
    return 1.0 - (distance / max_len)


def check_name_similarity(name1: str, name2: str, threshold: float = 0.7) -> bool:
    """
    Check if two repository names are similar.
    
    Args:
        name1: First repository name
        name2: Second repository name
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if names are similar above threshold
    """
    # Exact match
    if name1.lower() == name2.lower():
        return True
    
    # Substring check
    if name1.lower() in name2.lower() or name2.lower() in name1.lower():
        return True
    
    # Levenshtein ratio
    ratio = levenshtein_ratio(name1, name2)
    return ratio >= threshold


def extract_filenames_from_signatures(signatures: Dict[str, Dict]) -> List[str]:
    """
    Extract just the filenames (not full paths) from signature keys.
    
    Args:
        signatures: Signature dictionary with paths as keys
        
    Returns:
        List of filenames
    """
    filenames = []
    for path in signatures.keys():
        # Extract filename from path
        filename = path.split('/')[-1]
        if filename:
            filenames.append(filename)
    return filenames
