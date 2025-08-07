"""
Risk analysis export functionality for account data.

Handles risk metrics and analysis export.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import AccountMonitorConfig, AccountDisplaySettings
from ..messages import AccountExportCompleted

logger = logging.getLogger(__name__)


class RiskExporter:
    """Handles risk analysis export functionality."""
    
    def __init__(
        self,
        config: AccountMonitorConfig,
        display_settings: AccountDisplaySettings,
        export_dir: Path,
        completion_callback=None
    ):
        """Initialize risk exporter."""
        self.config = config
        self.display_settings = display_settings
        self.export_dir = Path(export_dir)
        self.completion_callback = completion_callback
    
    async def export_risk_analysis(
        self,
        risk_metrics: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export risk analysis to JSON format."""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"risk_analysis_{timestamp}.json"
            
            filepath = self.export_dir / filename
            
            # Prepare risk analysis data
            risk_data = {
                "export_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "type": "risk_analysis",
                    "source": "Foxtrot Trading Platform - Account Monitor"
                },
                "risk_metrics": risk_metrics,
                "analysis": self._generate_risk_analysis(risk_metrics),
                "recommendations": self._generate_recommendations(risk_metrics)
            }
            
            # Write JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(risk_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Notify completion
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath),
                    record_count=1,
                    export_type="risk_analysis",
                    success=True
                )
                await self.completion_callback(completion_msg)
            
            logger.info(f"Exported risk analysis to {filepath}")
            return str(filepath)
            
        except Exception as e:
            error_msg = f"Risk analysis export failed: {e}"
            logger.error(error_msg)
            
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath) if 'filepath' in locals() else "unknown",
                    record_count=0,
                    export_type="risk_analysis",
                    success=False,
                    error=error_msg
                )
                await self.completion_callback(completion_msg)
            
            raise
    
    def _generate_risk_analysis(self, risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk analysis from metrics."""
        analysis = {
            "overall_risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "key_concerns": [],
            "strengths": []
        }
        
        try:
            # Calculate overall risk score (0-100)
            risk_score = 0.0
            
            # Margin ratio impact (40% of score)
            margin_ratio = risk_metrics.get("portfolio_margin_ratio", 0.0)
            if margin_ratio > 0.8:
                risk_score += 40
                analysis["key_concerns"].append("High margin utilization")
            elif margin_ratio > 0.5:
                risk_score += 20
            else:
                analysis["strengths"].append("Conservative margin usage")
            
            # Concentration risk (30% of score)
            concentration = risk_metrics.get("concentration_risk", 0.0)
            if concentration > 0.7:
                risk_score += 30
                analysis["key_concerns"].append("High portfolio concentration")
            elif concentration > 0.4:
                risk_score += 15
            else:
                analysis["strengths"].append("Well-diversified portfolio")
            
            # Volatility risk (30% of score)
            volatility = risk_metrics.get("portfolio_volatility", 0.0)
            if volatility > 0.3:
                risk_score += 30
                analysis["key_concerns"].append("High portfolio volatility")
            elif volatility > 0.15:
                risk_score += 15
            else:
                analysis["strengths"].append("Low portfolio volatility")
            
            analysis["overall_risk_score"] = risk_score
            
            # Determine risk level
            if risk_score >= 70:
                analysis["risk_level"] = "HIGH"
            elif risk_score >= 40:
                analysis["risk_level"] = "MEDIUM"
            else:
                analysis["risk_level"] = "LOW"
                
        except Exception as e:
            logger.warning(f"Error generating risk analysis: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _generate_recommendations(self, risk_metrics: Dict[str, Any]) -> list[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        try:
            margin_ratio = risk_metrics.get("portfolio_margin_ratio", 0.0)
            concentration = risk_metrics.get("concentration_risk", 0.0)
            volatility = risk_metrics.get("portfolio_volatility", 0.0)
            
            # Margin recommendations
            if margin_ratio > 0.8:
                recommendations.append("Consider reducing margin utilization to below 70%")
                recommendations.append("Review position sizes to lower leverage")
            elif margin_ratio > 0.5:
                recommendations.append("Monitor margin levels closely")
            
            # Concentration recommendations
            if concentration > 0.7:
                recommendations.append("Diversify portfolio across more assets/sectors")
                recommendations.append("Consider reducing largest position sizes")
            elif concentration > 0.4:
                recommendations.append("Continue monitoring concentration levels")
            
            # Volatility recommendations
            if volatility > 0.3:
                recommendations.append("Consider adding lower volatility assets")
                recommendations.append("Review position sizing and risk management rules")
            elif volatility > 0.15:
                recommendations.append("Monitor portfolio volatility trends")
            
            # General recommendations
            if len(recommendations) == 0:
                recommendations.append("Current risk profile appears well-managed")
                recommendations.append("Continue regular risk monitoring")
            else:
                recommendations.append("Implement gradual risk reduction over time")
                recommendations.append("Set up alerts for key risk thresholds")
                
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations due to data issues")
        
        return recommendations