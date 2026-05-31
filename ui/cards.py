import streamlit as st

def badge(label, value, color="green"):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:12px;
            border-radius:8px;
            text-align:center;
            font-size:22px;
            font-weight:600;">
            <div style="font-size:16px; color:"white";">{label}</div>
            <div style="color:cyan;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def badgeRed(label, value, color="red"):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:12px;
            border-radius:8px;
            text-align:center;
            font-size:16px;
            font-weight:600;">
            <div style="font-size:13px; color:white;">{label}</div>
            <div style="color:white;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def badgeGreen(label, value, color="darkgreen"):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:12px;
            border-radius:8px;
            text-align:center;
            font-size:16px;
            font-weight:600;">
            <div style="font-size:13px; color:white;">{label}</div>
            <div style="color:white;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def badgeBlue(label, value, color="blue"):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:12px;
            border-radius:8px;
            text-align:center;
            font-size:16px;
            font-weight:600;">
            <div style="font-size:13px; color:white;">{label}</div>
            <div style="color:white;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )




