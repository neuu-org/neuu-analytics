"""
NEUU Loading Screen + Sidebar Branding — reutilizavel em todas as paginas.
"""

import streamlit as st

NEUU_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap');

/* Loading animations */
@keyframes neuu-shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
@keyframes neuu-pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
}
@keyframes neuu-fade-out {
    0% { opacity: 1; visibility: visible; }
    90% { opacity: 1; }
    100% { opacity: 0; visibility: hidden; }
}

/* Loading overlay */
.neuu-loading-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: #0E1117;
    z-index: 999999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: neuu-fade-out 1s ease-in-out 1.5s forwards;
    pointer-events: none;
}
.neuu-loading-logo {
    font-family: 'Inter', sans-serif;
    font-size: 3.5rem;
    font-weight: 700;
    letter-spacing: 8px;
    background: linear-gradient(
        90deg,
        #5A5550 0%, #D4A853 25%, #F5E6B8 50%, #D4A853 75%, #5A5550 100%
    );
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: neuu-shimmer 2s linear infinite;
}
.neuu-loading-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #5A5550;
    margin-top: 12px;
    animation: neuu-pulse 2s ease-in-out infinite;
}
.neuu-loading-dots {
    margin-top: 24px;
    display: flex;
    gap: 8px;
}
.neuu-loading-dots span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #D4A853;
    animation: neuu-pulse 1.4s ease-in-out infinite;
}
.neuu-loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.neuu-loading-dots span:nth-child(3) { animation-delay: 0.4s; }

/* Sidebar */
[data-testid="stSidebar"] {
    border-right: 1px solid #2A2D34;
    background: linear-gradient(180deg, #0E1117 0%, #12151C 50%, #0E1117 100%);
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    font-size: 0.9rem;
    letter-spacing: 0.5px;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    transition: all 0.2s ease;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: rgba(212, 168, 83, 0.08);
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: rgba(212, 168, 83, 0.12);
    border-left: 3px solid #D4A853;
}

</style>
"""

LOADING_HTML = """
<div class="neuu-loading-overlay">
    <div class="neuu-loading-logo">NEUU</div>
    <div class="neuu-loading-sub">Analytics</div>
    <div class="neuu-loading-dots">
        <span></span><span></span><span></span>
    </div>
</div>
"""

def show_loading():
    """Mostra loading screen + CSS global. Chamar no inicio de cada pagina."""
    st.markdown(NEUU_CSS + LOADING_HTML, unsafe_allow_html=True)
