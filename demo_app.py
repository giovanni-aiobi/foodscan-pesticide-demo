"""
Streamlit Demo App for Pesticide Compliance Checker
Simple interface to test the checker before API integration
"""

import streamlit as st
import pandas as pd
from pesticide_checker import PesticideChecker

# Page config
st.set_page_config(
    page_title="Pesticide Compliance Checker",
    page_icon="🌱",
    layout="wide"
)

# Initialize checker
@st.cache_resource
def get_checker():
    return PesticideChecker()

checker = get_checker()

# Title
st.title("🌱 Pesticide Compliance Checker")
st.markdown("Check if your crop + pesticide combination is compliant with EU/Codex regulations")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    target_market = st.selectbox(
        "Target Market",
        ["EU", "Codex"],
        help="Select the regulatory market to check against"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This tool checks pesticide compliance using COLEAD's MRL database (2,294 records)")

# Cache substance lookup for performance
@st.cache_data(ttl=600)
def get_substances_for_crop(crop_name: str):
    """Get all substances for a crop (cached for 10 min)"""
    return checker.get_all_substances_for_crop(crop_name)


def display_compliance_result(result, crop_name):
    """Display compliance check results"""
    st.markdown("---")
    st.subheader("📋 Compliance Results")
    
    # Status badge
    status_colors = {
        "COMPLIANT": "🟢",
        "NON_COMPLIANT": "🔴",
        "WARNING": "🟠",
        "INFO": "🔵",
        "UNKNOWN": "⚪"
    }
    st.markdown(f"## {status_colors.get(result.status, '⚪')} **{result.status}**")
    
    # Severity
    if result.severity:
        severity_colors = {
            "CRITICAL": "🔴",
            "MAJOR": "🟠",
            "MINOR": "🟡",
            "INFO": "🔵"
        }
        st.markdown(f"**Severity:** {severity_colors.get(result.severity, '⚪')} {result.severity}")
    
    # Message
    st.info(result.message)
    
    # Details in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        is_approved = result.eu_status and "Approuvée" in result.eu_status
        st.metric("EU Approved", "✅ Yes" if is_approved else "❌ No")
        if result.eu_status:
            st.caption(f"Status: {result.eu_status}")
    
    with col2:
        if result.mrl_limit:
            st.metric("MRL Limit", f"{result.mrl_limit} mg/kg")
        else:
            st.metric("MRL Limit", "Not Set")
    
    with col3:
        if result.residue_level:
            st.metric("Your Residue", f"{result.residue_level} mg/kg")
            if result.mrl_limit and result.residue_level > result.mrl_limit:
                st.error("⚠️ Exceeds MRL!")
    
    # GAP Recommendations
    if result.gap_recommendations:
        st.markdown("---")
        st.subheader("📖 Good Agricultural Practice (GAP)")
        
        gap = result.gap_recommendations
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if gap.get("dose"):
                st.metric("Recommended Dose", gap["dose"])
        
        with col2:
            if gap.get("max_applications"):
                st.metric("Max Applications", gap["max_applications"])
        
        with col3:
            if gap.get("preharvest_interval"):
                st.metric("Pre-harvest Interval", f"{gap['preharvest_interval']} days")
    
    # Alternatives (if non-compliant)
    if result.alternatives and len(result.alternatives) > 0:
        st.markdown("---")
        st.subheader("🔄 Approved Alternatives")
        st.markdown(f"Found **{len(result.alternatives)}** approved alternatives for **{crop_name}**:")
        
        alt_data = []
        for alt in result.alternatives[:5]:
            if isinstance(alt, dict):
                alt_data.append({
                    "Substance": alt.get("active_substance", "N/A"),
                    "MRL (mg/kg)": alt.get("mrl_eu", "N/A"),
                    "Status": alt.get("eu_status", "N/A")
                })
            else:
                alt_data.append({
                    "Substance": str(alt),
                    "MRL (mg/kg)": "N/A",
                    "Status": "Approved"
                })
        
        if alt_data:
            st.dataframe(pd.DataFrame(alt_data), use_container_width=True)


# Main content - Tabs for different search modes
tab1, tab2 = st.tabs(["🔍 Direct Search", "🌾 Browse by Crop"])

# ============ TAB 1: Direct Search ============
with tab1:
    st.markdown("*Enter the crop and substance names directly if you know them.*")
    
    col1, col2 = st.columns(2)

    with col1:
        crop = st.text_input(
            "🥕 Crop Name",
            placeholder="e.g., mango, tomato, carrot",
            help="Enter the crop name (case-insensitive)",
            key="direct_crop"
        )

    with col2:
        substance = st.text_input(
            "🧪 Active Substance",
            placeholder="e.g., Azoxystrobin, Alpha-cypermethrin",
            help="Enter the pesticide active substance",
            key="direct_substance"
        )

    residue_level = st.number_input(
        "📊 Residue Level (mg/kg) - Optional",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.01,
        help="Enter measured residue level to check against MRL",
        key="direct_residue"
    )

    if st.button("🔍 Check Compliance", type="primary", use_container_width=True, key="direct_check"):
        if not crop or not substance:
            st.error("⚠️ Please enter both crop and substance names")
        else:
            with st.spinner("Checking compliance..."):
                result = checker.check_compliance(
                    crop=crop,
                    substance=substance,
                    target_market=target_market,
                    residue_level=residue_level if residue_level > 0 else None
                )
                st.session_state.direct_result = result
                st.session_state.direct_crop_name = crop

    if "direct_result" in st.session_state:
        display_compliance_result(st.session_state.direct_result, st.session_state.get("direct_crop_name", ""))

# ============ TAB 2: Browse by Crop ============
with tab2:
    st.markdown("*Don't know the pesticide name? Search by crop first to see all available substances.*")
    
    browse_crop = st.text_input(
        "🌾 Enter Crop Name",
        placeholder="e.g., mango, tomato, avocado",
        help="Enter a crop name to see all documented pesticides",
        key="browse_crop"
    )
    
    if st.button("🔎 Find Pesticides", use_container_width=True, key="browse_search"):
        if not browse_crop:
            st.error("⚠️ Please enter a crop name")
        else:
            with st.spinner(f"Searching pesticides for {browse_crop}..."):
                substances = get_substances_for_crop(browse_crop)
                st.session_state.browse_substances = substances
                st.session_state.browse_crop_name = browse_crop
    
    # Display substances if found
    if "browse_substances" in st.session_state and st.session_state.browse_substances:
        substances = st.session_state.browse_substances
        crop_name = st.session_state.browse_crop_name
        
        st.success(f"✅ Found **{len(substances)}** pesticides documented for **{crop_name}**")
        
        # Create a nice table view
        st.markdown("### 📋 Available Pesticides")
        
        # Prepare data for display
        df_data = []
        for s in substances:
            status_icon = "✅" if s.get("eu_status") == "Approuvée" else "❌"
            df_data.append({
                "Active Substance": s.get("active_substance", "N/A"),
                "Type": s.get("pesticide_type", "N/A"),
                "EU Status": f"{status_icon} {s.get('eu_status', 'N/A')}",
                "MRL EU (mg/kg)": s.get("mrl_eu", "N/A"),
                "MRL Codex (mg/kg)": s.get("mrl_codex", "N/A")
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, height=300)
        
        # Dropdown to select a substance for compliance check
        st.markdown("---")
        st.markdown("### 🧪 Check Specific Substance")
        
        substance_names = [s.get("active_substance", "") for s in substances if s.get("active_substance")]
        
        selected_substance = st.selectbox(
            "Select a substance to check",
            options=[""] + substance_names,
            help="Choose a substance from the list above",
            key="browse_select_substance"
        )
        
        browse_residue = st.number_input(
            "📊 Residue Level (mg/kg) - Optional",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.01,
            help="Enter measured residue level to check against MRL",
            key="browse_residue"
        )
        
        if st.button("🔍 Check Selected Substance", type="primary", use_container_width=True, key="browse_check"):
            if not selected_substance:
                st.error("⚠️ Please select a substance from the dropdown")
            else:
                with st.spinner("Checking compliance..."):
                    result = checker.check_compliance(
                        crop=crop_name,
                        substance=selected_substance,
                        target_market=target_market,
                        residue_level=browse_residue if browse_residue > 0 else None
                    )
                    st.session_state.browse_result = result
        
        if "browse_result" in st.session_state:
            display_compliance_result(st.session_state.browse_result, st.session_state.get("browse_crop_name", ""))
    
    elif "browse_substances" in st.session_state and not st.session_state.browse_substances:
        st.warning(f"⚠️ No pesticides found for '{st.session_state.browse_crop_name}'. Try a different crop name.")

# Example section
st.markdown("---")
st.subheader("💡 Try These Examples")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ Compliant Example", use_container_width=True):
        with st.spinner("Checking compliance..."):
            result = checker.check_compliance(
                crop="mango",
                substance="Azoxystrobin",
                target_market=target_market,
                residue_level=2.0
            )
            st.session_state.example_result = result
            st.session_state.example_info = ("mango", "Azoxystrobin", 2.0)

with col2:
    if st.button("❌ Non-Compliant Example", use_container_width=True):
        with st.spinner("Checking compliance..."):
            result = checker.check_compliance(
                crop="mango",
                substance="Alpha-cypermethrin",
                target_market=target_market,
                residue_level=0.5
            )
            st.session_state.example_result = result
            st.session_state.example_info = ("mango", "Alpha-cypermethrin", 0.5)

with col3:
    if st.button("⚠️ MRL Exceeded Example", use_container_width=True):
        with st.spinner("Checking compliance..."):
            result = checker.check_compliance(
                crop="mango",
                substance="Azoxystrobin",
                target_market=target_market,
                residue_level=5.0
            )
            st.session_state.example_result = result
            st.session_state.example_info = ("mango", "Azoxystrobin", 5.0)

# Display example result if exists
if "example_result" in st.session_state:
    crop_name, substance_name, residue_val = st.session_state.example_info
    result = st.session_state.example_result
    
    # Status badge
    status_colors = {
        "COMPLIANT": "🟢",
        "NON_COMPLIANT": "🔴",
        "WARNING": "🟠",
        "INFO": "🔵",
        "UNKNOWN": "⚪"
    }
    status_icon = status_colors.get(result.status, "⚪")
    
    st.markdown(f"**Example:** {crop_name} + {substance_name} @ {residue_val} mg/kg → {status_icon} **{result.status}**")
    st.caption(result.message)

# Footer
st.markdown("---")
st.caption("🔬 Powered by COLEAD Pesticide Database | Data: 2,294 crop×pesticide combinations")
