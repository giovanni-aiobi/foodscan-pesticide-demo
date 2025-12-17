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

# Main content
col1, col2 = st.columns(2)

with col1:
    crop = st.text_input(
        "🥕 Crop Name",
        placeholder="e.g., mango, tomato, carrot",
        help="Enter the crop name (case-insensitive)"
    )

with col2:
    substance = st.text_input(
        "🧪 Active Substance",
        placeholder="e.g., Azoxystrobin, Alpha-cypermethrin",
        help="Enter the pesticide active substance"
    )

residue_level = st.number_input(
    "📊 Residue Level (mg/kg) - Optional",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=0.01,
    help="Enter measured residue level to check against MRL"
)

# Check button
if st.button("🔍 Check Compliance", type="primary", use_container_width=True):
    if not crop or not substance:
        st.error("⚠️ Please enter both crop and substance names")
    else:
        with st.spinner("Checking compliance..."):
            # Run check
            result = checker.check_compliance(
                crop=crop,
                substance=substance,
                target_market=target_market,
                residue_level=residue_level if residue_level > 0 else None
            )
            
            # Display results
            st.markdown("---")
            st.subheader("📋 Compliance Results")
            
            # Status badge
            status_colors = {
                "COMPLIANT": "🟢",
                "NON_COMPLIANT": "🔴",
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
                # Check if EU approved based on eu_status
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
                st.markdown(f"Found **{len(result.alternatives)}** approved alternatives for **{crop}**:")
                
                # Show alternatives in a table
                alt_data = []
                for alt in result.alternatives[:5]:  # Show top 5
                    alt_data.append({
                        "Substance": alt.get("active_substance", "N/A"),
                        "MRL (mg/kg)": alt.get("mrl_eu", "N/A"),
                        "Status": alt.get("eu_status", "N/A")
                    })
                
                if alt_data:
                    st.dataframe(pd.DataFrame(alt_data), use_container_width=True)

# Example section
st.markdown("---")
st.subheader("💡 Try These Examples")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ Compliant Example", use_container_width=True):
        st.session_state.example_crop = "mango"
        st.session_state.example_substance = "Azoxystrobin"
        st.session_state.example_residue = 2.0
        st.rerun()

with col2:
    if st.button("❌ Non-Compliant Example", use_container_width=True):
        st.session_state.example_crop = "mango"
        st.session_state.example_substance = "Alpha-cypermethrin"
        st.session_state.example_residue = 0.5
        st.rerun()

with col3:
    if st.button("⚠️ MRL Exceeded Example", use_container_width=True):
        st.session_state.example_crop = "mango"
        st.session_state.example_substance = "Azoxystrobin"
        st.session_state.example_residue = 5.0
        st.rerun()

# Load example if clicked
if "example_crop" in st.session_state:
    st.info(f"Example loaded: {st.session_state.example_crop} + {st.session_state.example_substance}")
    # Clear after showing
    del st.session_state.example_crop
    del st.session_state.example_substance
    del st.session_state.example_residue

# Footer
st.markdown("---")
st.caption("🔬 Powered by COLEAD Pesticide Database | Data: 2,294 crop×pesticide combinations")
