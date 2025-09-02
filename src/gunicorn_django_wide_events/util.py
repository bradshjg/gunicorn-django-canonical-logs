from __future__ import annotations

import os
import sys
import sysconfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import traceback


def filter_stack_summary(stack_summaries: traceback.StackSummary) -> list[traceback.FrameSummary]:
    library_paths = sysconfig.get_paths().values()
    return [
        frame_summary
        for frame_summary in stack_summaries
        if not any(frame_summary.filename.startswith((path, os.path.realpath(path))) for path in library_paths)
    ]


def format_frame_summary(frame_summary: traceback.FrameSummary) -> str:
    # use sys.path to find the shortest possible import (i.e. strip base project path)
    python_paths = sorted(sys.path, key=len, reverse=True)
    fname = frame_summary.filename
    for path in python_paths:
        if fname.startswith(path):
            to_remove = path if path.endswith("/") else path + "/"
            fname = fname.removeprefix(to_remove)
            break

    return f"{fname}:{frame_summary.lineno}:{frame_summary.name}"


def get_stack_loc_context(stack_summary: traceback.StackSummary):
    filtered_frame_summaries = filter_stack_summary(stack_summary)

    if not filtered_frame_summaries:
        # only library code in the stack, use the last frame
        return {"loc": format_frame_summary(stack_summary[-1])}

    if len(filtered_frame_summaries) == 1:
        app_frame_summary = filtered_frame_summaries[0]
        # cause might be in library code
        cause_frame_summary = stack_summary[-1]

        if cause_frame_summary == app_frame_summary:  # there's no deeper cause
            return {"loc": format_frame_summary(app_frame_summary)}
        return {
            "loc": format_frame_summary(app_frame_summary),
            "cause_loc": format_frame_summary(cause_frame_summary),
        }

    return {
        "loc": format_frame_summary(filtered_frame_summaries[0]),
        "cause_loc": format_frame_summary(filtered_frame_summaries[-1]),
    }
