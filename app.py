import json
import streamlit as st
from classifier import classify_po

st.set_page_config(page_title="PO Category Classifier", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

st.markdown(
    """
    <style>
    .hero {
        background: linear-gradient(120deg, #0b3d4f 0%, #105a6b 40%, #2c8c7b 100%);
        color: #f2fbff;
        padding: 28px 32px;
        border-radius: 18px;
        box-shadow: 0 12px 30px rgba(9, 30, 66, 0.25);
        margin-bottom: 18px;
    }
    .hero h1 { margin: 0 0 6px 0; font-size: 2.2rem; }
    .hero p { margin: 0; opacity: 0.9; }
    .card {
        border-radius: 16px;
        padding: 18px;
        background: #f7fbfa;
        border: 1px solid #e5f0ed;
    }
    .kpi-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 14px 16px;
        border: 1px solid #e1eeea;
        box-shadow: 0 8px 18px rgba(11, 61, 79, 0.08);
    }
    .chip {
        display: inline-block;
        background: #0b3d4f;
        color: #f2fbff;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        margin-right: 6px;
    }
    .pill {
        display: inline-block;
        background: #e8f6f2;
        color: #0b3d4f;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px 6px 4px 0;
        border: 1px solid #d3ebe3;
    }
    .badge {
        display: inline-block;
        background: #0b3d4f;
        color: #f2fbff;
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>PO L1-L2-L3 Classifier</h1>
        <p>Structured categorization for purchase orders with fast, explainable output.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Controls")
    show_raw = st.toggle("Show raw model output", value=False)
    auto_json = st.toggle("Auto-parse JSON", value=True)
    quick_sample = st.selectbox(
        "Sample descriptions",
        [
            "None",
            "Quarterly software license renewal for CRM platform",
            "Office chairs and adjustable standing desks for HQ",
            "Freight charges for outbound shipment to regional DC",
        ],
    )
    if quick_sample != "None":
        st.session_state.po_description = quick_sample
    if st.button("Clear history"):
        st.session_state.history = []

col_main, col_info = st.columns([3, 2], gap="large")

with col_main:
    st.markdown("#### Input")
    po_description = st.text_area(
        "PO Description",
        height=180,
        placeholder="Describe the goods or services in the PO...",
        value="" if quick_sample == "None" else quick_sample,
        key="po_description",
    )
    supplier = st.text_input(
        "Supplier (optional)",
        placeholder="Vendor or supplier name",
        key="supplier",
    )
    st.markdown(
        "<span class='chip'>L1</span><span class='chip'>L2</span><span class='chip'>L3</span>",
        unsafe_allow_html=True,
    )

    left_btn, right_btn = st.columns([1, 1])
    with left_btn:
        classify_clicked = st.button("Classify", type="primary")
    with right_btn:
        reset_clicked = st.button("Reset")
        if reset_clicked:
            st.session_state.po_description = ""
            st.session_state.supplier = ""

with col_info:
    st.markdown("#### Guidance")
    st.markdown(
        """
        - Be specific about the item or service.
        - Include quantities or contractual hints if relevant.
        - Add supplier name when it helps disambiguate.
        """
    )
    st.markdown("#### Activity")
    kpi_cols = st.columns(2)
    with kpi_cols[0]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="badge">Total</div>
                <div style="font-size: 1.6rem; font-weight: 700;">{len(st.session_state.history)}</div>
                <div style="opacity: 0.7;">Items classified</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi_cols[1]:
        latest_supplier = (
            st.session_state.history[0]["supplier"]
            if st.session_state.history
            else "N/A"
        )
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="badge">Latest</div>
                <div style="font-size: 1.1rem; font-weight: 700;">{latest_supplier or "N/A"}</div>
                <div style="opacity: 0.7;">Supplier</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with st.expander("Recent classifications", expanded=False):
        if not st.session_state.history:
            st.caption("No items yet.")
        else:
            for entry in st.session_state.history[:5]:
                st.markdown(f"- {entry['description']}")

st.markdown("---")

tabs = st.tabs(["Result", "History", "Raw"])

result_payload = None
raw_text = None
confidence_value = "N/A"


def _value_for_keys(payload, keys):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload[key]:
            return payload[key]
    return None

if classify_clicked:
    if not po_description.strip():
        st.warning("Please enter a PO Description")
    else:
        with st.spinner("Classifying..."):
            raw_text = classify_po(po_description, supplier)
        if auto_json:
            try:
                result_payload = json.loads(raw_text)
            except Exception:
                result_payload = None
        confidence_value = _value_for_keys(
            result_payload,
            ["confidence", "score", "probability", "model_confidence"],
        )
        st.session_state.history.insert(
            0,
            {
                "description": po_description.strip(),
                "supplier": supplier.strip(),
                "raw": raw_text,
                "parsed": result_payload,
            },
        )

with tabs[0]:
    st.markdown("#### Result")
    if classify_clicked:
        if auto_json and result_payload is not None:
            l1 = _value_for_keys(result_payload, ["l1", "L1", "level1", "category_l1"])
            l2 = _value_for_keys(result_payload, ["l2", "L2", "level2", "category_l2"])
            l3 = _value_for_keys(result_payload, ["l3", "L3", "level3", "category_l3"])

            st.markdown("**Category Highlights**")
            pills = []
            if l1:
                pills.append(f"<span class='pill'>L1: {l1}</span>")
            if l2:
                pills.append(f"<span class='pill'>L2: {l2}</span>")
            if l3:
                pills.append(f"<span class='pill'>L3: {l3}</span>")
            if pills:
                st.markdown("".join(pills), unsafe_allow_html=True)
            else:
                st.caption("No structured L1/L2/L3 fields detected.")

            result_cols = st.columns(3)
            with result_cols[0]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="badge">Confidence</div>
                        <div style="font-size: 1.3rem; font-weight: 700;">{confidence_value}</div>
                        <div style="opacity: 0.7;">Model score</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with result_cols[1]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="badge">Supplier</div>
                        <div style="font-size: 1.1rem; font-weight: 700;">{supplier or "N/A"}</div>
                        <div style="opacity: 0.7;">Input context</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with result_cols[2]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="badge">Tokens</div>
                        <div style="font-size: 1.1rem; font-weight: 700;">N/A</div>
                        <div style="opacity: 0.7;">Usage</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("**Structured Output**")
            st.json(result_payload)
        elif raw_text is not None:
            st.warning("Could not parse JSON. Showing raw output.")
            st.text(raw_text)
    else:
        st.caption("Run a classification to see the result.")

with tabs[1]:
    st.markdown("#### History")
    if not st.session_state.history:
        st.caption("No history yet.")
    else:
        for entry in st.session_state.history:
            st.markdown(f"**Description:** {entry['description']}")
            if entry["supplier"]:
                st.markdown(f"**Supplier:** {entry['supplier']}")
            if entry["parsed"] is not None:
                st.json(entry["parsed"])
            else:
                st.text(entry["raw"])
            st.markdown("---")

with tabs[2]:
    st.markdown("#### Raw Output")
    if show_raw and st.session_state.history:
        st.text(st.session_state.history[0]["raw"])
    elif show_raw:
        st.caption("No raw output yet.")
    else:
        st.caption("Enable 'Show raw model output' in the sidebar.")
