"""
Pesticide MRL Compliance Checker
Based on COLEAD Good Agricultural Practices Database

Usage:
    from pesticide_checker import PesticideChecker
    
    checker = PesticideChecker()
    result = checker.check_compliance(
        crop="mango",
        substance="chlorpyrifos",
        target_market="EU",
        residue_level=0.015
    )
    print(result.status, result.message)
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ComplianceResult:
    """Result of a pesticide compliance check"""
    status: str  # "COMPLIANT", "NON_COMPLIANT", "WARNING", "UNKNOWN"
    severity: str  # "CRITICAL", "MAJOR", "MINOR", "INFO"
    message: str
    crop: str
    substance: str
    target_market: str
    mrl_limit: Optional[float]
    mrl_flag: Optional[str]
    residue_level: Optional[float]
    eu_status: Optional[str]
    gap_recommendations: Optional[Dict]
    alternatives: Optional[List[str]]
    references: List[str]


class PesticideChecker:
    """Check pesticide residues against COLEAD MRL database"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize the checker
        
        Args:
            supabase_url: Supabase project URL (or from SUPABASE_URL env var)
            supabase_key: Supabase API key (or from SUPABASE_KEY env var)
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials required. Set SUPABASE_URL and SUPABASE_KEY environment variables "
                "or pass them as parameters."
            )
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def check_compliance(
        self,
        crop: str,
        substance: str,
        target_market: str = "EU",
        residue_level: Optional[float] = None
    ) -> ComplianceResult:
        """
        Check if pesticide residue complies with MRL for target market
        
        Args:
            crop: Crop name (e.g., "mango", "tomato")
            substance: Active substance name (e.g., "Chlorpyrifos")
            target_market: "EU" or "Codex"
            residue_level: Detected residue level in mg/kg (optional)
        
        Returns:
            ComplianceResult with status and recommendations
        """
        # Query database
        response = self.supabase.table('pesticide_mrl') \
            .select('*') \
            .ilike('crop', crop) \
            .ilike('active_substance', substance) \
            .execute()
        
        if not response.data:
            return self._create_unknown_result(crop, substance, target_market, residue_level)
        
        row = response.data[0]
        
        # Check compliance based on target market
        if target_market.upper() == "EU":
            return self._check_eu_compliance(row, residue_level)
        elif target_market.upper() == "CODEX":
            return self._check_codex_compliance(row, residue_level)
        else:
            raise ValueError(f"Unknown target market: {target_market}. Use 'EU' or 'Codex'.")
    
    def _check_eu_compliance(self, row: Dict, residue_level: Optional[float]) -> ComplianceResult:
        """Check compliance against EU standards"""
        
        crop = row['crop']
        substance = row['active_substance']
        eu_status = row['eu_status']
        mrl_eu = row['mrl_eu']
        mrl_flag = row['mrl_eu_flag']
        
        # CRITICAL: Check if substance is approved in EU
        if eu_status in ["Non approuvée", "Non reprise dans la liste"]:
            return ComplianceResult(
                status="NON_COMPLIANT",
                severity="CRITICAL",
                message=f"❌ {substance} is NOT APPROVED in EU for {crop}. Cannot export to EU market.",
                crop=crop,
                substance=substance,
                target_market="EU",
                mrl_limit=mrl_eu,
                mrl_flag=mrl_flag,
                residue_level=residue_level,
                eu_status=eu_status,
                gap_recommendations=None,
                alternatives=self._find_alternatives(crop, row['pesticide_type']),
                references=["COLEAD GAP Database", "EU Reg 396/2005"]
            )
        
        # Check if approval is expiring soon
        if row['eu_expiration']:
            try:
                exp_date = datetime.fromisoformat(row['eu_expiration'])
                days_until = (exp_date - datetime.now()).days
                if days_until < 180:  # Less than 6 months
                    return ComplianceResult(
                        status="WARNING",
                        severity="MAJOR",
                        message=f"⚠️ {substance} EU approval expires in {days_until} days ({row['eu_expiration']}). Monitor for renewal.",
                        crop=crop,
                        substance=substance,
                        target_market="EU",
                        mrl_limit=mrl_eu,
                        mrl_flag=mrl_flag,
                        residue_level=residue_level,
                        eu_status=eu_status,
                        gap_recommendations=self._extract_gap(row),
                        alternatives=None,
                        references=["COLEAD GAP Database"]
                    )
            except:
                pass
        
        # Check residue level if provided
        if residue_level is not None and mrl_eu is not None:
            if residue_level > mrl_eu:
                return ComplianceResult(
                    status="NON_COMPLIANT",
                    severity="MAJOR",
                    message=f"❌ Residue level {residue_level} mg/kg exceeds EU MRL of {mrl_eu} mg/kg.",
                    crop=crop,
                    substance=substance,
                    target_market="EU",
                    mrl_limit=mrl_eu,
                    mrl_flag=mrl_flag,
                    residue_level=residue_level,
                    eu_status=eu_status,
                    gap_recommendations=self._extract_gap(row),
                    alternatives=None,
                    references=["COLEAD GAP Database", "EU Reg 396/2005"]
                )
            else:
                # COMPLIANT
                flag_note = f" (at LOQ)" if mrl_flag == "LOQ" else ""
                return ComplianceResult(
                    status="COMPLIANT",
                    severity="INFO",
                    message=f"✅ Compliant with EU standards. Residue {residue_level} mg/kg ≤ MRL {mrl_eu} mg/kg{flag_note}.",
                    crop=crop,
                    substance=substance,
                    target_market="EU",
                    mrl_limit=mrl_eu,
                    mrl_flag=mrl_flag,
                    residue_level=residue_level,
                    eu_status=eu_status,
                    gap_recommendations=self._extract_gap(row),
                    alternatives=None,
                    references=["COLEAD GAP Database"]
                )
        
        # No residue level provided, just return MRL info
        return ComplianceResult(
            status="INFO",
            severity="INFO",
            message=f"ℹ️ EU MRL for {substance} on {crop}: {mrl_eu} mg/kg. Status: {eu_status}",
            crop=crop,
            substance=substance,
            target_market="EU",
            mrl_limit=mrl_eu,
            mrl_flag=mrl_flag,
            residue_level=None,
            eu_status=eu_status,
            gap_recommendations=self._extract_gap(row),
            alternatives=None,
            references=["COLEAD GAP Database"]
        )
    
    def _check_codex_compliance(self, row: Dict, residue_level: Optional[float]) -> ComplianceResult:
        """Check compliance against Codex Alimentarius standards"""
        
        crop = row['crop']
        substance = row['active_substance']
        mrl_codex = row['mrl_codex']
        mrl_flag = row['mrl_codex_flag']
        
        # Check if Codex MRL exists
        if mrl_codex is None:
            return ComplianceResult(
                status="UNKNOWN",
                severity="INFO",
                message=f"ℹ️ No Codex MRL established for {substance} on {crop}.",
                crop=crop,
                substance=substance,
                target_market="Codex",
                mrl_limit=None,
                mrl_flag=None,
                residue_level=residue_level,
                eu_status=row['eu_status'],
                gap_recommendations=self._extract_gap(row),
                alternatives=None,
                references=["COLEAD GAP Database", "Codex Alimentarius"]
            )
        
        # Check residue level if provided
        if residue_level is not None:
            if residue_level > mrl_codex:
                return ComplianceResult(
                    status="NON_COMPLIANT",
                    severity="MAJOR",
                    message=f"❌ Residue level {residue_level} mg/kg exceeds Codex MRL of {mrl_codex} mg/kg.",
                    crop=crop,
                    substance=substance,
                    target_market="Codex",
                    mrl_limit=mrl_codex,
                    mrl_flag=mrl_flag,
                    residue_level=residue_level,
                    eu_status=row['eu_status'],
                    gap_recommendations=self._extract_gap(row),
                    alternatives=None,
                    references=["COLEAD GAP Database", "Codex Alimentarius"]
                )
            else:
                return ComplianceResult(
                    status="COMPLIANT",
                    severity="INFO",
                    message=f"✅ Compliant with Codex standards. Residue {residue_level} mg/kg ≤ MRL {mrl_codex} mg/kg.",
                    crop=crop,
                    substance=substance,
                    target_market="Codex",
                    mrl_limit=mrl_codex,
                    mrl_flag=mrl_flag,
                    residue_level=residue_level,
                    eu_status=row['eu_status'],
                    gap_recommendations=self._extract_gap(row),
                    alternatives=None,
                    references=["COLEAD GAP Database", "Codex Alimentarius"]
                )
        
        # No residue level provided
        return ComplianceResult(
            status="INFO",
            severity="INFO",
            message=f"ℹ️ Codex MRL for {substance} on {crop}: {mrl_codex} mg/kg.",
            crop=crop,
            substance=substance,
            target_market="Codex",
            mrl_limit=mrl_codex,
            mrl_flag=mrl_flag,
            residue_level=None,
            eu_status=row['eu_status'],
            gap_recommendations=self._extract_gap(row),
            alternatives=None,
            references=["COLEAD GAP Database", "Codex Alimentarius"]
        )
    
    def _extract_gap(self, row: Dict) -> Dict:
        """Extract Good Agricultural Practice recommendations"""
        return {
            "dose": row.get('dose'),
            "max_applications": row.get('max_applications'),
            "interval_days": row.get('interval_days'),
            "preharvest_interval_eu": row.get('preharvest_eu'),
            "preharvest_interval_codex": row.get('preharvest_codex'),
            "who_toxicity_class": row.get('who_class'),
            "pesticide_type": row.get('pesticide_type'),
            "resistance_group": row.get('resistance_group')
        }
    
    def _find_alternatives(self, crop: str, pesticide_type: str) -> List[str]:
        """Find alternative approved pesticides for same crop and type"""
        if not pesticide_type:
            return []
        
        response = self.supabase.table('pesticide_mrl') \
            .select('active_substance') \
            .ilike('crop', crop) \
            .ilike('pesticide_type', f'%{pesticide_type}%') \
            .eq('eu_status', 'Approuvée') \
            .limit(5) \
            .execute()
        
        return [row['active_substance'] for row in response.data]
    
    def _create_unknown_result(
        self, 
        crop: str, 
        substance: str, 
        target_market: str,
        residue_level: Optional[float]
    ) -> ComplianceResult:
        """Create result for unknown crop/substance combination"""
        return ComplianceResult(
            status="UNKNOWN",
            severity="INFO",
            message=f"ℹ️ No data found for {substance} on {crop} in COLEAD database.",
            crop=crop,
            substance=substance,
            target_market=target_market,
            mrl_limit=None,
            mrl_flag=None,
            residue_level=residue_level,
            eu_status=None,
            gap_recommendations=None,
            alternatives=None,
            references=["COLEAD GAP Database"]
        )
    
    def get_all_substances_for_crop(self, crop: str) -> List[Dict]:
        """Get all pesticides documented for a crop"""
        response = self.supabase.table('pesticide_mrl') \
            .select('active_substance, pesticide_type, eu_status, mrl_eu, mrl_codex') \
            .ilike('crop', crop) \
            .order('eu_status', desc=True) \
            .order('active_substance') \
            .execute()
        
        return response.data
    
    def check_batch(
        self,
        crop: str,
        substances: List[Dict],
        target_market: str = "EU"
    ) -> List[ComplianceResult]:
        """
        Check multiple substances for a crop
        
        Args:
            crop: Crop name
            substances: List of dicts with 'name' and optional 'residue_level'
            target_market: "EU" or "Codex"
        
        Returns:
            List of ComplianceResult objects
        """
        results = []
        for item in substances:
            result = self.check_compliance(
                crop=crop,
                substance=item['name'],
                target_market=target_market,
                residue_level=item.get('residue_level')
            )
            results.append(result)
        return results


# Example usage
if __name__ == "__main__":
    # Initialize checker
    checker = PesticideChecker()
    
    # Test case 1: Non-approved substance
    print("=" * 60)
    print("Test 1: Mango + Chlorpyrifos (Non-approved)")
    print("=" * 60)
    result = checker.check_compliance(
        crop="mango",
        substance="Chlorpyrifos",
        target_market="EU",
        residue_level=0.015
    )
    print(f"Status: {result.status}")
    print(f"Severity: {result.severity}")
    print(f"Message: {result.message}")
    if result.alternatives:
        print(f"Alternatives: {', '.join(result.alternatives)}")
    
    print("\n" + "=" * 60)
    print("Test 2: Tomato + Azoxystrobin (Approved)")
    print("=" * 60)
    result = checker.check_compliance(
        crop="tomato",
        substance="Azoxystrobin",
        target_market="EU",
        residue_level=1.5
    )
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    if result.gap_recommendations:
        print(f"GAP: {result.gap_recommendations}")
    
    print("\n" + "=" * 60)
    print("Test 3: Get all substances for mango")
    print("=" * 60)
    substances = checker.get_all_substances_for_crop("mango")
    print(f"Found {len(substances)} substances for mango")
    for s in substances[:5]:
        print(f"  - {s['active_substance']}: {s['eu_status']}")
