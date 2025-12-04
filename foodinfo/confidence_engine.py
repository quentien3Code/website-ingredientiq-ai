"""
Confidence Engine for IngredientIQ
Implements geometric mean confidence calculation per onboarding guide specifications.
"""

import math
from typing import Dict, List, Optional


class ConfidenceEngine:
    """
    Confidence Engine per onboarding guide spec.
    Calculates confidence using geometric mean of multiple factors.
    """
    
    CONFIDENCE_THRESHOLD = 0.72  # Per spec: if C < 0.72, set status = Defer
    
    def calculate_confidence(self, 
                            ocr_quality: float,
                            barcode_confidence: float,
                            ner_confidence: float,
                            source_reliability: float,
                            ai_consistency: Optional[float] = None,
                            regulatory_coverage: Optional[float] = None) -> float:
        """
        Calculate combined confidence using geometric mean.
        
        Args:
            ocr_quality: OCR confidence score (0.0-1.0)
            barcode_confidence: Barcode match confidence (0.0-1.0)
            ner_confidence: Named entity recognition confidence (0.0-1.0)
            source_reliability: Source data reliability (0.0-1.0)
            ai_consistency: AI response consistency (optional, 0.0-1.0)
            regulatory_coverage: Regulatory data coverage (optional, 0.0-1.0)
        
        Returns:
            Combined confidence score (0.0-1.0) using geometric mean
        """
        # Core required factors
        factors = [
            max(ocr_quality, 0.01),  # Avoid zero for geometric mean
            max(barcode_confidence, 0.01),
            max(ner_confidence, 0.01),
            max(source_reliability, 0.01)
        ]
        
        # Optional factors if provided
        if ai_consistency is not None:
            factors.append(max(ai_consistency, 0.01))
        if regulatory_coverage is not None:
            factors.append(max(regulatory_coverage, 0.01))
        
        # Geometric mean: (x1 * x2 * ... * xn)^(1/n)
        product = 1.0
        for factor in factors:
            product *= factor
        
        confidence = product ** (1.0 / len(factors))
        return min(confidence, 1.0)  # Cap at 1.0
    
    def should_defer(self, confidence: float) -> bool:
        """
        Determine if status should be Defer based on confidence threshold.
        
        Args:
            confidence: Combined confidence score (0.0-1.0)
        
        Returns:
            True if confidence < threshold (should defer), False otherwise
        """
        return confidence < self.CONFIDENCE_THRESHOLD
    
    def extract_confidence_factors(self, scan_data: Dict) -> Dict:
        """
        Extract confidence factors from scan data.
        
        Args:
            scan_data: Dictionary containing scan metadata
        
        Returns:
            Dictionary with confidence factors
        """
        return {
            "ocr_quality": scan_data.get("ocr_confidence", scan_data.get("ocr_quality", 0.0)),
            "barcode_confidence": scan_data.get("barcode_confidence", 0.0),
            "ner_confidence": scan_data.get("ner_confidence", scan_data.get("ingredient_match_accuracy", 0.0)),
            "source_reliability": scan_data.get("source_reliability", 0.0),
            "ai_consistency": scan_data.get("ai_consistency"),
            "regulatory_coverage": scan_data.get("regulatory_coverage")
        }
    
    def get_confidence_metadata(self, confidence: float, factors: Dict) -> Dict:
        """
        Get metadata about confidence calculation for audit logging.
        
        Args:
            confidence: Calculated confidence score
            factors: Input factors used in calculation
        
        Returns:
            Dictionary with confidence metadata
        """
        return {
            "combined_confidence": confidence,
            "threshold": self.CONFIDENCE_THRESHOLD,
            "should_defer": self.should_defer(confidence),
            "factors": factors,
            "calculation_method": "geometric_mean"
        }

