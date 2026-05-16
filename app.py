import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------------------------
# 1. SETUP & BRANDING (UI POLISH)
# ----------------------------------------------------
st.set_page_config(page_title="Atomberg Goal Portal", page_icon="⚛️", layout="wide")

# Custom UI CSS for branding
st.markdown("""
    <style>
    .brand-header { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .brand-sub { font-size: 16px; color: #64748B; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. IN-MEMORY DATABASE 
# ----------------------------------------------------
if 'goals_db' not in st.session_state:
    st.session_state.goals_db = pd.DataFrame([
        {
            "Goal_ID": "G001", "Emp_Name": "Lakshin", "Role": "Employee",
            "Thrust_Area": "Product Innovation", "Title": "Optimize Fan Motor Efficiency",
            "UoM": "Min (Numeric / %)", "Target": 95.0, "Weightage": 20.0,
            "Status": "On Track", "Approval": "Pending", "Q1_Actual": 92.0, "Comment": ""
        },
        {
            "Goal_ID": "G002", "Emp_Name": "Lakshin", "Role": "Employee",
            "Thrust_Area": "Operations", "Title": "Reduce Assembly Line Waste",
            "UoM": "Max (Numeric / %)", "Target": 5.0, "Weightage": 20.0,
            "Status": "Not Started", "Approval": "Pending", "Q1_Actual": 0.0, "Comment": ""
        },
        {
            "Goal_ID": "G003", "Emp_Name": "Lakshin", "Role": "Employee",
            "Thrust_Area": "Safety", "Title": "Zero Factory Incidents",
            "UoM": "Zero", "Target": 0.0, "Weightage": 30.0,
            "Status": "Completed", "Approval": "Pending", "Q1_Actual": 0.0, "Comment": ""
        }
    ])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def calculate_progress_score(uom, target, actual):
    try:
        if uom == "Min (Numeric / %)": return (actual / target) * 100 if target != 0 else 0.0
        elif uom == "Max (Numeric / %)": return (target / actual) * 100 if actual != 0 else 0.0
        elif uom == "Zero": return 100.0 if actual == 0 else 0.0
        elif uom == "Timeline": return 100.0 if actual <= target else 50.0
    except ZeroDivisionError: return 0.0
    return 0.0

# ----------------------------------------------------
# 3. INTERFACE - NAVIGATION SIDEBAR
# ----------------------------------------------------
with st.sidebar:
    st.markdown("<h1 style='color: #1E3A8A; margin-top: 0px;'>⚛️ Atomberg</h1>", unsafe_allow_html=True)
    st.markdown("### Goal Portal v1.0")
    st.markdown("---")
    current_user_role = st.radio(
        "Select User Persona Journey:",
        ["Employee View", "Manager View (L1)", "HR / Admin Dashboard"]
    )
    st.markdown("---")
    st.info("💡 Tip: Use this radio selector to test end-to-end multi-role workflows.")

# ----------------------------------------------------
# 4. VIEW RENDERING ENGINE
# ----------------------------------------------------

# --- JOURNEY A: EMPLOYEE INTERFACE ---
if current_user_role == "Employee View":
    st.markdown('<p class="brand-header">🎯 Employee Workspace: Lakshin</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">Draft, align, and track your quarterly objectives.</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Create & Submit Goals", "📈 Quarterly Progress"])
    
    with tab1:
        with st.expander("➕ Draft a New Performance Goal", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                thrust = st.selectbox("Thrust Area", ["Product Innovation", "Operations", "Customer Success", "Sustainability"])
                title = st.text_input("Goal Title")
            with col2:
                uom_type = st.selectbox("Unit of Measurement (UoM)", ["Min (Numeric / %)", "Max (Numeric / %)", "Timeline", "Zero"])
                target_val = st.number_input("Target Value", min_value=0.0, value=100.0)
                weight = st.number_input("Weightage (%)", min_value=0.0, max_value=100.0, step=5.0, value=10.0)
                
            if st.button("Add to Drafts", type="secondary"):
                current_employee_goals = st.session_state.goals_db[st.session_state.goals_db['Emp_Name'] == "Lakshin"]
                if len(current_employee_goals) >= 8: st.error("⛔ Max 8 goals allowed.")
                elif weight < 10.0: st.error("⛔ Minimum weightage is 10%.")
                elif current_employee_goals['Weightage'].sum() + weight > 100.0: st.error("⛔ Weightage exceeds 100%.")
                elif not title: st.warning("⚠️ Title cannot be blank.")
                else:
                    new_row = {"Goal_ID": f"G00{len(st.session_state.goals_db)+1}", "Emp_Name": "Lakshin", "Role": "Employee", "Thrust_Area": thrust, "Title": title, "UoM": uom_type, "Target": target_val, "Weightage": weight, "Status": "Not Started", "Approval": "Pending", "Q1_Actual": 0.0, "Comment": ""}
                    st.session_state.goals_db = pd.concat([st.session_state.goals_db, pd.DataFrame([new_row])], ignore_index=True)
                    st.toast("Goal added successfully!", icon="✅")
                    st.rerun()

        st.divider()
        st.subheader("Your Active Ledger")
        my_current_sheet = st.session_state.goals_db[st.session_state.goals_db['Emp_Name'] == "Lakshin"]
        
        clean_display_sheet = my_current_sheet[['Goal_ID', 'Thrust_Area', 'Title', 'UoM', 'Target', 'Weightage', 'Status', 'Approval']]
        st.dataframe(clean_display_sheet, use_container_width=True, hide_index=True)
        
        total_allocated_weight = my_current_sheet['Weightage'].sum()
        st.metric(label="Total Weightage Allocation", value=f"{total_allocated_weight}%")
        
        if total_allocated_weight == 100.0:
            if st.button("Submit Final Goal Sheet", type="primary"):
                st.session_state.goals_db.loc[st.session_state.goals_db['Emp_Name'] == "Lakshin", "Approval"] = "Submitted"
                st.balloons() 
                st.success("🚀 Sheet submitted securely to manager.")
                st.rerun()
        else:
            st.warning("⚠️ Complete allocation to exactly 100% to submit.")

    with tab2:
        st.subheader("Quarterly Achievement Log")
        editable_sheet = st.session_state.goals_db[st.session_state.goals_db['Emp_Name'] == "Lakshin"]
        for index, row in editable_sheet.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Title']}** ({row['Thrust_Area']})")
                c1, c2, c3 = st.columns(3)
                with c1: new_status = st.selectbox(f"Status", ["Not Started", "On Track", "Completed"], key=f"stat_{index}", index=["Not Started", "On Track", "Completed"].index(row['Status']))
                with c2: new_act = st.number_input(f"Actual (Target: {row['Target']})", value=float(row['Q1_Actual']), key=f"act_{index}")
                with c3: 
                    calc_score = calculate_progress_score(row['UoM'], row['Target'], new_act)
                    st.metric("Computed Score", f"{calc_score:.1f}%")
                
                # Dynamic state updating tracking
                if new_status != row['Status'] or new_act != row['Q1_Actual']:
                    st.session_state.goals_db.at[index, 'Status'] = new_status
                    st.session_state.goals_db.at[index, 'Q1_Actual'] = new_act

# --- JOURNEY B: MANAGER (L1) WORKSPACE ---
elif current_user_role == "Manager View (L1)":
    st.markdown('<p class="brand-header">👔 Manager Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">Verify goals and conduct quarterly check-ins.</p>', unsafe_allow_html=True)
    
    mgr_tab1, mgr_tab2 = st.tabs(["✔️ Goal Approvals", "💬 Quarterly Check-ins"])
    
    with mgr_tab1:
        pending_sheets = st.session_state.goals_db[st.session_state.goals_db['Approval'] == "Submitted"]
        if pending_sheets.empty: st.info("✨ Clean Queue: No pending reviews.")
        else:
            for index, row in pending_sheets.iterrows():
                with st.container(border=True):
                    st.write(f"**{row['Emp_Name']}** | {row['Title']} ({row['Weightage']}%)")
                    comment_text = st.text_input("Manager Note", key=f"mgr_app_com_{index}")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Approve & Lock", key=f"app_{index}", type="primary"):
                            st.session_state.goals_db.at[index, 'Approval'] = "Approved"
                            st.session_state.goals_db.at[index, 'Comment'] = comment_text
                            st.toast("Goal locked and approved.", icon="🔒")
                            st.rerun() # Instantly refreshes list state on click
                    with col_btn2:
                        if st.button("Return for Rework", key=f"rej_{index}"):
                            st.session_state.goals_db.at[index, 'Approval'] = "Pending"
                            st.toast("Returned to employee.", icon="↩️")
                            st.rerun() # Instantly refreshes list state on click

    with mgr_tab2:
        # Check-in queue shows active approved goals that still need feedback notes
        active_goals = st.session_state.goals_db[(st.session_state.goals_db['Approval'] == "Approved") & (st.session_state.goals_db['Comment'] == "")]
        if active_goals.empty: st.info("✨ Complete: All approved goals have been finalized with structured check-in notes.")
        else:
            for index, row in active_goals.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Emp_Name']}** | {row['Title']}")
                    current_score = calculate_progress_score(row['UoM'], row['Target'], row['Q1_Actual'])
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Target", f"{row['Target']} {row['UoM'][:3]}")
                    c2.metric("Logged Actual", row['Q1_Actual'])
                    c3.metric("Score", f"{current_score:.1f}%")
                    checkin_comment = st.text_area("Feedback Note (Required to clear)", value="", key=f"chk_com_{index}")
                    if st.button("Save Review", key=f"save_chk_{index}", type="primary"):
                        if not checkin_comment.strip():
                            st.warning("⚠️ Feedback comments cannot be completely empty.")
                        else:
                            st.session_state.goals_db.at[index, 'Comment'] = checkin_comment
                            st.toast("Check-in logged and saved successfully.", icon="💾")
                            st.rerun() # Forces the card to immediately drop off the pending feedback array list

# --- JOURNEY C: HR / ADMIN ENGINE ---
else:
    st.markdown('<p class="brand-header">🛡️ Admin Control Center</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">System governance, analytics, and rule enforcement.</p>', unsafe_allow_html=True)
    
    hr_tab1, hr_tab2, hr_tab3, hr_tab4 = st.tabs(["📊 KPI Dashboard", "📈 Analytics", "📥 Export Ledger", "⭐ Escalations"])
    
    with hr_tab1:
        st.subheader("Q1 Check-in Completion")
        total_goals = len(st.session_state.goals_db)
        completed_reviews = len(st.session_state.goals_db[st.session_state.goals_db['Comment'] != ""])
        completion_rate = (completed_reviews / total_goals) * 100 if total_goals > 0 else 0.0
        
        dash_c1, dash_c2, dash_c3 = st.columns(3)
        dash_c1.metric("Total Goals Tracked", total_goals)
        dash_c2.metric("Check-ins Finalized", completed_reviews)
        dash_c3.metric("Org Completion Rate", f"{completion_rate:.1f}%")
        
        st.progress(completion_rate / 100)
        st.dataframe(st.session_state.goals_db[['Emp_Name', 'Title', 'Status', 'Approval', 'Comment']], use_container_width=True, hide_index=True)
        
    with hr_tab2:
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            fig1 = px.pie(st.session_state.goals_db, names='Thrust_Area', title='Goals by Thrust Area', hole=0.4) 
            st.plotly_chart(fig1, use_container_width=True)
        with c_m2:
            fig2 = px.histogram(st.session_state.goals_db, x='Status', color='Status', title='Status Distribution')
            st.plotly_chart(fig2, use_container_width=True)
            
    with hr_tab3:
        st.info("System Audit Trail: Active.")
        csv_buffer = st.session_state.goals_db.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Master Data (CSV)", data=csv_buffer, file_name="Master_Ledger.csv", mime="text/csv", type="primary")
        
    with hr_tab4:
        st.subheader("System Escalations")
        days_elapsed = st.slider("Simulate Days Elapsed (Demo Mode)", 0, 30, 0)
        escalation_triggered = False
        
        for index, row in st.session_state.goals_db.iterrows():
            if row['Approval'] == "Pending" and days_elapsed >= 10:
                st.error(f"⚠️ **EMPLOYEE ESCALATION:** {row['Emp_Name']} has not submitted '{row['Title']}'.")
                escalation_triggered = True
            if row['Approval'] == "Submitted" and days_elapsed >= 5:
                st.error(f"🚨 **MANAGER ESCALATION:** '{row['Title']}' is stuck in review.")
                escalation_triggered = True
                
        if not escalation_triggered:
            st.success("✔️ All workflows are within acceptable SLAs.")
