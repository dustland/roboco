"""
Sidebar functionality for the RoboCo UI.

This module contains functions for rendering the sidebar with project information and controls.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from loguru import logger

from roboco.ui.utils import check_api_connection
from roboco.ui.status import update_execution_log

def sidebar_content():
    """Render the sidebar content."""
    # Add a cleaner sidebar header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="https://raw.githubusercontent.com/dustland/roboco/main/assets/logo.png" style="width: 80px; margin-bottom: 10px;">
        <h2 style="font-size: 28px; margin-bottom: 0; font-weight: 600;">RoboCo</h2>
        <p style="color: #64748b; margin-top: 8px; font-size: 14px; line-height: 1.5;">
        A powerful multi-agent platform for building AI teams that collaborate
        to solve complex problems.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a cleaner divider
    st.markdown('<hr style="margin: 1.5rem 0; border: 0; border-top: 1px solid #e5e7eb;">', unsafe_allow_html=True)
    
    # Display project controls
    st.markdown('<h3 style="font-size: 18px; margin-bottom: 12px; color: #4b5563;">Project Controls</h3>', unsafe_allow_html=True)
    
    # More prominent button
    if st.button("🔄 New Chat", key="new_chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.project_id = None
        st.session_state.execution_log = []
        st.session_state.tasks = []
        st.success("New chat started!")
        st.rerun()
    
    # Active project info
    if st.session_state.project_id:
        st.markdown(f"""
        <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e2e8f0;">
            <h4 style="margin: 0 0 8px 0; font-size: 15px; color: #64748b; font-weight: 600;">Active Project</h4>
            <code style="background-color: #e2e8f0; padding: 4px 6px; border-radius: 4px; font-size: 13px; color: #334155; word-break: break-all;">{st.session_state.project_id}</code>
        </div>
        """, unsafe_allow_html=True)
    
    # Add a cleaner divider
    st.markdown('<hr style="margin: 1.5rem 0; border: 0; border-top: 1px solid #e5e7eb;">', unsafe_allow_html=True)
    
    # System status section
    st.markdown('<h3 style="font-size: 18px; margin-bottom: 12px; color: #4b5563;">System Status</h3>', unsafe_allow_html=True)
    
    # API connection status
    if st.session_state.api_connected:
        st.markdown("""
        <div style="background-color: #dcfce7; padding: 10px 15px; border-radius: 6px; border: 1px solid #86efac; display: flex; align-items: center; margin-bottom: 15px;">
            <span style="color: #16a34a; font-size: 18px; margin-right: 8px;">✓</span>
            <span style="color: #166534; font-weight: 500;">API Connected</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #fee2e2; padding: 10px 15px; border-radius: 6px; border: 1px solid #fca5a5; display: flex; align-items: center; margin-bottom: 15px;">
            <span style="color: #dc2626; font-size: 18px; margin-right: 8px;">✗</span>
            <span style="color: #991b1b; font-weight: 500;">API Disconnected</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Retry Connection", use_container_width=True):
            st.session_state.api_connected = check_api_connection()
            st.rerun()
    
    # Task progress metrics
    if st.session_state.project_id and st.session_state.tasks:
        completed_tasks = sum(1 for task in st.session_state.tasks if task.get("status") == "COMPLETED")
        total_tasks = len(st.session_state.tasks)
        failed_tasks = sum(1 for task in st.session_state.tasks if task.get("status", "").upper() == "FAILED")
        
        if total_tasks > 0:
            completion_percentage = int(completed_tasks / total_tasks * 100)
            
            # Task completion metric with better styling
            st.markdown(f"""
            <div style="margin-bottom: 15px;">
                <p style="margin-bottom: 5px; font-size: 15px; color: #4b5563; font-weight: 500;">Task Completion</p>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-size: 24px; font-weight: 600; color: #1e40af;">{completion_percentage}%</span>
                    <span style="color: #6b7280; font-size: 14px;">{completed_tasks}/{total_tasks}</span>
                </div>
                <div style="height: 8px; width: 100%; background-color: #e5e7eb; border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; width: {completion_percentage}%; background-color: #3b82f6; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Tasks by status with better styling - recreated to avoid formatting issues
            completed_val = completed_tasks
            in_progress_val = total_tasks - completed_tasks - failed_tasks
            failed_val = failed_tasks
            
            st.markdown(f"""
            <style>
            .status-container {{
                display: flex;
                justify-content: space-between;
                margin-top: 10px;
                gap: 8px;
            }}
            .status-item {{
                flex: 1;
                text-align: center;
                padding: 12px 8px;
                border-radius: 8px;
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
            }}
            .status-item-icon {{
                font-size: 18px;
                margin-bottom: 5px;
            }}
            .status-item-label {{
                font-size: 12px;
                color: #64748b;
                margin-bottom: 3px;
            }}
            .status-item-value {{
                font-size: 18px;
                font-weight: 600;
                color: #334155;
            }}
            </style>
            <div class="status-container">
                <div class="status-item">
                    <div class="status-item-icon">✓</div>
                    <div class="status-item-label">Completed</div>
                    <div class="status-item-value">{completed_val}</div>
                </div>
                <div class="status-item">
                    <div class="status-item-icon">○</div>
                    <div class="status-item-label">In Progress</div>
                    <div class="status-item-value">{in_progress_val}</div>
                </div>
                <div class="status-item">
                    <div class="status-item-icon">✗</div>
                    <div class="status-item-label">Failed</div>
                    <div class="status-item-value">{failed_val}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Add footer with version info
    st.markdown('<div style="position: absolute; bottom: 20px; left: 0; right: 0; padding: 10px; text-align: center;">', unsafe_allow_html=True)
    st.markdown('<hr style="margin: 0 20px 10px 20px; border: 0; border-top: 1px solid #e5e7eb;">', unsafe_allow_html=True)
    st.markdown('<div style="color: #94a3b8; font-size: 13px; font-weight: 500;">RoboCo v0.3.0</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True) 