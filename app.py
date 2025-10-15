# app.py
import streamlit as st
from queue_manager import QueueManager
from priority_manager import PriorityManager
from service_counter import ServiceCounterManager
from user_search import UserSearch
from analytics import Analytics
from undo_stack import UndoStack
from file_handler import FileHandler
import time
import pandas as pd
import numpy as np

# -------------------------
# App setup and state init
# -------------------------
st.set_page_config(page_title="SmartQueue — Intelligent Queue Management", layout="wide",
                   initial_sidebar_state="expanded")

# Use session_state to persist managers across interactions
if "qm" not in st.session_state:
    st.session_state.qm = QueueManager(avg_service_time_seconds=180)  # default 3 minutes
if "pm" not in st.session_state:
    st.session_state.pm = PriorityManager()
if "sm" not in st.session_state:
    st.session_state.sm = ServiceCounterManager()
if "us" not in st.session_state:
    st.session_state.us = UserSearch()
if "an" not in st.session_state:
    st.session_state.an = Analytics()
if "undo" not in st.session_state:
    st.session_state.undo = UndoStack()
if "fh" not in st.session_state:
    st.session_state.fh = FileHandler("smartqueue_state.json")

qm = st.session_state.qm
pm = st.session_state.pm
sm = st.session_state.sm
us = st.session_state.us
an = st.session_state.an
undo = st.session_state.undo
fh = st.session_state.fh

# Load persisted state if any
if "loaded" not in st.session_state:
    loaded = fh.load_from_file(qm, pm, sm, an, undo)
    st.session_state.loaded = True if loaded else False

# Demo dataset: create some sample users if queue empty (only once)
if not qm.queue and not pm.heap:
    demo_names = ["Anita", "Ravi", "Sunil", "Maya"]
    for n in demo_names:
        qm.enqueue(n, "Normal")
    # add one VIP and one emergency
    vip = pm.add_priority_customer(qm.next_token, "Dr. Roy", priority_level=5, user_type="VIP")
    qm.next_token += 1  # ensure unique tokens
    emergency = pm.add_priority_customer(qm.next_token, "Emergency-X", priority_level=10, user_type="Emergency")
    qm.next_token += 1

# -------------------------
# Layout: Sidebar (Admin) & Main (User + Queue)
# -------------------------
st.markdown("""
<style>
.big-button{
  padding: .9rem 1rem;
  font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar - admin controls
with st.sidebar:
    st.markdown("## Admin Panel")
    st.markdown("**Service counters**")
    with st.expander("Manage counters"):
        cols = st.columns([2,1])
        new_counter = cols[0].text_input("Add counter id (e.g., C1)", key="new_counter")
        if cols[1].button("Add", key="add_counter"):
            if new_counter:
                sm.push_counter(new_counter)
                st.success(f"Counter {new_counter} added.")
    st.markdown("Available counters: " + (", ".join(sm.available_counters()) if sm.available_counters() else "None"))

    st.markdown("---")
    st.markdown("**Queue actions**")
    col1, col2 = st.columns(2)
    if col1.button("Serve next customer", key="serve_next"):
        # Serve priority first
        served = None
        served_source = None
        counter = sm.pop_counter()
        if counter is None:
            st.warning("No available counters. Add a counter first.")
        else:
            # priority first
            p = pm.get_next_priority_customer()
            if p:
                served = p
                served_source = "priority"
            else:
                item = qm.dequeue()
                if item:
                    served = item
                    served_source = "normal"
            if served:
                # record for analytics
                an.record_service(time.time())
                # store undo info
                if served_source == "priority":
                    undo.push_operation('dequeue_priority', {"item": served.to_dict()})
                else:
                    undo.push_operation('dequeue', {"item": served.to_dict()})
                st.success(f"Served {served.name} (Token {served.token}) at counter {counter}.")
    if col2.button("Undo last action"):
        undo_last_operation()
        if res:
            st.success(f"Undo result: {res}")
        else:
            st.info("Nothing to undo.")

    st.markdown("---")
    st.markdown("**Remove by token**")
    remove_token = st.text_input("Token to remove", key="remove_token")
    if st.button("Remove", key="remove_button"):
        try:
            t = int(remove_token)
            removed = us.remove_user(t, qm, pm)
            if removed:
                # push to undo stack
                container = 'normal' if hasattr(removed, 'type') and removed.type != 'VIP' and removed.type != 'Emergency' else 'priority'
                undo.push_operation('remove', {"item": removed.to_dict() if hasattr(removed, "to_dict") else {}, "container": container})
                st.success(f"Removed token {t} ({removed.name if hasattr(removed, 'name') else 'unknown'}).")
            else:
                st.warning("Token not found.")
        except ValueError:
            st.error("Enter a numeric token.")

    st.markdown("---")
    st.markdown("**Persistence**")
    if st.button("Save state", key="save_state"):
        path = fh.save_to_file(qm, pm, sm, an, undo)
        st.success(f"Saved to {path}")
    if st.button("Load state", key="load_state"):
        ok = fh.load_from_file(qm, pm, sm, an, undo)
        if ok:
            st.success("Loaded state.")
        else:
            st.warning("No saved state found.")

    st.markdown("---")
    st.markdown("**Settings**")
    avg_min = st.number_input("Average service time (seconds)", min_value=30, max_value=3600, value=int(qm.avg_service_time))
    if st.button("Update avg service time", key="update_avg"):
        qm.avg_service_time = int(avg_min)
        st.success("Average service time updated.")

    st.caption("Admin actions affect everyone. Use undo to revert simple mistakes.")

# Main area
st.title("SmartQueue — Intelligent Queue Management")
st.markdown("A simple queue system with priority handling, counters and analytics. Designed for hospitals, offices, canteens.")

# Customer registration panel
st.header("Get a token")
with st.form("register_form"):
    name = st.text_input("Your name")
    user_type = st.selectbox("Type", ["Normal", "VIP", "Emergency"])
    submitted = st.form_submit_button("Get token")
    if submitted:
        if not name:
            st.error("Please enter your name.")
        else:
            if user_type == "Normal":
                item = qm.enqueue(name, user_type)
                undo.push_operation('enqueue', {"token": item.token})
                st.success(f"Token issued: {item.token} (Normal). Estimated wait: {qm.estimate_wait_time(item.token)['estimated_seconds']//60} minutes.")
            else:
                # priority add uses priority manager - choose priority_level mapping
                mapping = {"VIP": 5, "Emergency": 10}
                token = qm.next_token
                qm.next_token += 1
                pc = pm.add_priority_customer(token, name, mapping[user_type], user_type)
                undo.push_operation('enqueue', {"token": pc.token})
                st.success(f"Token issued: {pc.token} ({user_type}). You'll be prioritized.")

# Visual board
st.subheader("Queue Board")
c1, c2 = st.columns([2,1])
with c1:
    st.markdown("### Priority Queue")
    p_list = pm.peek_all()
    if not p_list:
        st.info("No priority customers.")
    else:
        dfp = pd.DataFrame(p_list)
        st.table(dfp)

    st.markdown("### Normal Queue")
    q_list = qm.display_queue()
    if not q_list:
        st.info("No customers in queue.")
    else:
        dfq = pd.DataFrame(q_list)
        st.table(dfq)

with c2:
    st.markdown("### Counters")
    st.markdown("Available: " + (", ".join(sm.available_counters()) if sm.available_counters() else "None"))
    st.markdown("---")
    est = qm.estimate_wait_time()
    st.metric("Total waiting (people)", len(qm.queue))
    st.metric("Estimated total wait (minutes)", f"{est['estimated_seconds']//60}")

# Search by token
st.subheader("Find your token")
colx, coly = st.columns([2,1])
token_search = colx.text_input("Enter your token to find position")
if coly.button("Find"):
    try:
        t = int(token_search)
        loc, ttype, pos, est_sec = us.find_user_by_token(t, qm.token_map, pm.token_map, queue_manager=qm)
        if loc == "not_found":
            st.warning("Token not found.")
        else:
            st.success(f"Found in {loc}. Type: {ttype}. Position: {pos}. Estimated wait: {int(est_sec)//60} minutes.")
    except ValueError:
        st.error("Provide a numeric token.")

# Analytics
st.header("Analytics & Reports")
st.markdown("Simple statistics and activity graph.")
colA, colB = st.columns([2,1])
with colA:
    avg_wait_display = an.average_wait_time([])  # placeholder: you could store real waits
    st.metric("Average Wait (sample)", f"{avg_wait_display:.1f} sec")
    # graph
    img_data = an.generate_matplotlib_bar()
    st.image(img_data, use_column_width=True)
with colB:
    st.text("ASCII Graph (services per hour):")
    st.code(an.generate_ascii_graph())

# Footnotes / instructions
st.markdown("---")
st.info("Instructions: Use the 'Get a token' form to register. Admins in the sidebar can serve, remove, undo, and manage counters. Save state to persist across sessions.")

# Save state on exit / periodically if desired (button already provided)
