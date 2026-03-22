"""Data Inspector node — analyses an Excel/CSV file and builds a rich data context."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from langchain_core.messages import AIMessage

from my_agent.helpers.sandbox_client import check_server_health, preload_file_via_server
from my_agent.core.execution_var import get_current_session_id
from my_agent.helpers.utils import (
    analyze_dataframe,
    generate_data_description,
    load_excel_file_sampled,
)
from my_agent.models.state import ExcelAnalysisState
from my_agent.tools.tools import reset_execution_context

logger = logging.getLogger(__name__)


def _error_result(error_msg: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    return {
        "data_context": {"error": error_msg, "file_path": file_path, "description": None, "summary": {}},
        "messages": [AIMessage(content=error_msg, name="DataInspector")],
    }


async def _ensure_sandbox_healthy() -> Optional[Dict[str, Any]]:
    try:
        if not await check_server_health():
            msg = "Sandbox server is not running or unhealthy. Please start it: python run_sandbox_server.py"
            return _error_result(msg)
    except Exception as exc:
        return _error_result(f"Cannot connect to sandbox: {exc}")
    return None


def _build_semantic_profile(df: pd.DataFrame, analysis: Dict[str, Any]) -> Dict[str, Any]:
    numeric_cols = analysis["numeric_columns"]
    categorical_cols = analysis["categorical_columns"]
    
    roles = {}
    for col in analysis["column_names"]:
        c_low = col.lower()
        if col in numeric_cols: roles[col] = "metric"
        elif "date" in c_low or "month" in c_low: roles[col] = "time_dimension"
        else: roles[col] = "dimension"

    return {
        "metrics": numeric_cols,
        "dimensions": categorical_cols,
        "semantic_roles": roles,
        "has_scenarios": False, 
        "structure_type": "standard_tabular",
        "granularity": "unknown"
    }


async def data_inspector_node(state: ExcelAnalysisState) -> Dict[str, Any]:
    logger.info("📊 Data Inspector: Starting file analysis...")
    try:
        if err := await _ensure_sandbox_healthy(): return err
        await reset_execution_context()

        excel_path = state.get("excel_file_path")
        if not excel_path: return _error_result("No Excel file provided.")

        df, total_rows = await load_excel_file_sampled(excel_path)
        analysis = await analyze_dataframe(df)
        data_description = await generate_data_description(analysis)
        profile = _build_semantic_profile(df, analysis)

        await preload_file_via_server(excel_path, session_id=get_current_session_id())

        data_context = {
            "file_path": os.path.abspath(excel_path),
            "file_name": Path(excel_path).name,
            "analyzed_at": datetime.now().isoformat(),
            "description": data_description,
            "total_rows": total_rows,
            "summary": analysis,
            "dataset_profile": profile,
        }

        msg = AIMessage(content=f"Data inspection complete. {total_rows} rows found.", name="DataInspector")
        return {"data_context": data_context, "messages": [msg]}
    except Exception as exc:
        return _error_result(f"Analysis error: {exc}", file_path=state.get("excel_file_path"))
