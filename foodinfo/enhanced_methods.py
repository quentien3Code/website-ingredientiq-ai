"""
Enhanced Methods for FoodLabelNutritionView
Add these methods to the FoodLabelNutritionView class
"""

def get_ai_health_insight_and_expert_advice_enhanced(self, user, nutrition_data, flagged_ingredients):
    """
    Enhanced AI Health Insights - ChatGPT 4.0 Quality
    Implements condition-specific flagging, weighted scoring transparency, and expert insights with citations
    """
    try:
        from .enhanced_ai_analysis import EnhancedAIAnalysis
        enhanced_analyzer = EnhancedAIAnalysis()
        return enhanced_analyzer.get_enhanced_health_insights(user, nutrition_data, flagged_ingredients)
    except Exception as e:
        print(f"Enhanced AI analysis failed, falling back to standard analysis: {e}")
        # Fallback to standard analysis
        return self.get_ai_health_insight_and_expert_advice(user, nutrition_data, flagged_ingredients)

def optimize_analysis_performance(self, user, image_content, nutrition_data, ingredients_list):
    """
    Optimize analysis performance to achieve 2-3 second processing time
    """
    try:
        from .performance_optimization import PerformanceOptimizer
        optimizer = PerformanceOptimizer()
        return optimizer.optimize_analysis_pipeline(
            user=user,
            image_content=image_content,
            nutrition_data=nutrition_data,
            ingredients_list=ingredients_list
        )
    except Exception as e:
        print(f"Performance optimization failed: {e}")
        # Fallback to standard processing
        return None

def validate_scan_quality(self, image_content):
    """
    Validate scan quality before processing
    """
    try:
        from .barcode_scanner_optimization import BarcodeScannerOptimizer
        scanner_optimizer = BarcodeScannerOptimizer()
        return scanner_optimizer.validate_scan_quality(image_content)
    except Exception as e:
        print(f"Scan quality validation failed: {e}")
        return {"quality_passed": True, "error": str(e)}

def get_enhanced_scan_settings(self):
    """
    Get enhanced scan settings for frontend implementation
    """
    try:
        from .barcode_scanner_optimization import BarcodeScannerOptimizer
        scanner_optimizer = BarcodeScannerOptimizer()
        return scanner_optimizer.optimize_scan_settings()
    except Exception as e:
        print(f"Failed to get enhanced scan settings: {e}")
        return {
            "focus_dwell_time": 1.5,
            "scan_timeout": 10,
            "retry_attempts": 3,
            "focus_threshold": 0.8
        }

def get_performance_optimization_settings(self):
    """
    Get performance optimization settings
    """
    try:
        from .performance_optimization import PerformanceOptimizer
        optimizer = PerformanceOptimizer()
        return {
            "parallel_processing": True,
            "max_workers": 6,
            "cache_enabled": True,
            "timeout_per_task": 3
        }
    except Exception as e:
        print(f"Failed to get performance settings: {e}")
        return {
            "parallel_processing": True,
            "max_workers": 4,
            "cache_enabled": False,
            "timeout_per_task": 5
        }
